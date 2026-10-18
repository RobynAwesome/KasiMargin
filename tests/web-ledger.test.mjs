import test from "node:test";
import assert from "node:assert/strict";
import {ledgerCorrection, ledgerEntry, LedgerSaver, LedgerSaveRejected} from "../kasimargin/web/build/ledger.js";

const original = {
  id: "sale-1", idempotency_key: "create-1", business_day: "2026-10-17", event_type: "sale", payment_method: "card",
  amount_cents: 15000, occurred_at: "2026-10-17T10:00:00+02:00", source_kind: "OPERATOR_REPORTED", revision: 1,
  replaces_id: null, correction_reason: null, is_current: 1,
};

test("a daily entry preserves exact cents, South African time and the payment boundary", () => {
  const entry = ledgerEntry({id:"entry-1",idempotencyKey:"save-1",eventType:"sale",paymentMethod:"card",amount:"150.05",when:"2026-10-17T10:00"});
  assert.equal(entry.amount_cents,15005); assert.equal(entry.business_day,"2026-10-17");
  assert.equal(entry.occurred_at,"2026-10-17T10:00:00+02:00"); assert.equal(entry.source_kind,"OPERATOR_REPORTED");
  assert.throws(() => ledgerEntry({id:"expense-1",idempotencyKey:"save-2",eventType:"expense",paymentMethod:"card",amount:"30",when:"2026-10-17T10:00"}),/cash spending only/);
  assert.throws(() => ledgerEntry({id:"zero",idempotencyKey:"save-3",eventType:"sale",paymentMethod:"cash",amount:"0",when:"2026-10-17T10:00"}),/greater than/);
});

test("a correction uses the current revision and keeps an optional reason optional", () => {
  const correction = ledgerCorrection({id:"sale-1-r2",idempotencyKey:"correct-1",replaces:original,amount:"160",when:"2026-10-17T10:00",reason:""});
  assert.deepEqual(correction,{id:"sale-1-r2",idempotency_key:"correct-1",replaces_id:"sale-1",expected_revision:1,amount_cents:16000,occurred_at:"2026-10-17T10:00:00+02:00",reason:null});
});

test("rapid submissions share one in-flight write; an intentional next sale gets a fresh identity", async () => {
  let release;
  const calls = [];
  const saver = new LedgerSaver(async entry => {
    calls.push(entry);
    await new Promise(resolve => { release = resolve; });
    return {save_status:"SAVED_ON_THIS_DEVICE"};
  });
  const first = saver.save({...original});
  const duplicate = saver.save({...original,id:"ignored-second-id",idempotency_key:"ignored-second-key"});
  assert.equal(first,duplicate);
  await Promise.resolve();
  assert.equal(calls.length,1);
  release(); await first;
  const next = saver.save({...original,id:"intentional-next-sale",idempotency_key:"next-sale-key"});
  await Promise.resolve(); release(); await next;
  assert.equal(calls.length,2);
  assert.equal(calls[1].id,"intentional-next-sale");
});

test("a lost response retries the retained sale identity and blocks changed money", async () => {
  const persisted = new Map(), calls = [];
  const saver = new LedgerSaver(async entry => {
    calls.push(structuredClone(entry));
    persisted.set(entry.idempotency_key,entry);
    if (calls.length === 1) throw new Error("response lost after commit");
    return {save_status:"SAVED_ON_THIS_DEVICE"};
  });
  await assert.rejects(saver.save({...original}),/response lost/);
  await assert.rejects(saver.save({...original,amount_cents:16000}),/previous save is not confirmed/);
  await saver.save({...original,id:"new-unused-id",idempotency_key:"new-unused-key"});
  assert.equal(persisted.size,1);
  assert.deepEqual(calls[0],calls[1]);
});

test("a lost correction response retains revision and identity on retry", async () => {
  const calls = [];
  const saver = new LedgerSaver(async entry => {
    calls.push(entry);
    if (calls.length === 1) throw new Error("lost");
    return {save_status:"SAVED_ON_THIS_DEVICE"};
  });
  const correction = ledgerCorrection({id:"r2",idempotencyKey:"correct-key",replaces:original,amount:"160",when:"2026-10-17T10:00",reason:"entry mistake"});
  await assert.rejects(saver.save(correction),/lost/);
  await saver.save({...correction,id:"discarded-r2",idempotency_key:"discarded-key"});
  assert.deepEqual(calls[0],calls[1]);
  assert.equal(calls[1].expected_revision,1);
});

test("definite rejection permits edits; an unconfirmed success response retains the retry", async () => {
  let mode = "reject";
  const calls = [];
  const saver = new LedgerSaver(async entry => {
    calls.push(entry);
    if (mode === "reject") throw new LedgerSaveRejected("input rejected without write");
    if (mode === "unknown") return {save_status:"UNKNOWN"};
    return {save_status:"SAVED_ON_THIS_DEVICE"};
  });
  await assert.rejects(saver.save({...original}),LedgerSaveRejected);
  mode = "unknown";
  const changed = {...original,amount_cents:16000,id:"edited",idempotency_key:"edited-key"};
  await assert.rejects(saver.save(changed),/Save not confirmed/);
  mode = "success";
  await saver.save({...changed,id:"discarded",idempotency_key:"discarded"});
  assert.deepEqual(calls[1],calls[2]);
});
