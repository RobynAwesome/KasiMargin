import test from "node:test";
import assert from "node:assert/strict";
import {ledgerCorrection, ledgerEntry, ledgerReferenceView, LedgerSaver, LedgerSaveRejected} from "../kasimargin/web/build/ledger.js";
import {ownDay} from "../kasimargin/web/build/transactions.js";

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

test("read-only ledger reference summarises matching day totals without promoting them to verified cash or calculation inputs", () => {
  const dayRequest = ownDay(new Date("2026-10-18T08:00:00Z"));
  const beforeSnapshot = structuredClone(dayRequest);
  const review = {
    business_day: "2026-10-18",
    record_count: 3,
    recorded_sales_cents: 25000,
    cash_sales_cents: 10000,
    card_sales_cents: 15000,
    cash_expenses_cents: 4000,
    record_status: "OPERATOR_REPORTED_RECORDS_MAY_BE_INCOMPLETE",
    cash_position_status: "NOT_PREPARED",
    events: [],
  };
  const view = ledgerReferenceView({status: "loaded", targetDay: "2026-10-18", review});
  assert.equal(view.status, "ready");
  assert.match(view.note, /Operator-reported for 2026-10-18/);
  assert.match(view.note, /Not verified cash/);
  assert.deepEqual(view.rows, [
    ["Sales recorded", 25000],
    ["Cash sales recorded", 10000],
    ["Card sales recorded", 15000],
    ["Cash spending recorded", 4000],
  ]);
  assert.deepEqual(dayRequest, beforeSnapshot);
  assert.equal(dayRequest.cash_position.verified_cash_cents, null);
  assert.equal(dayRequest.performance.attributable_costs_cents, null);
  assert.equal(dayRequest.cash_position.due_liabilities_cents, null);
  assert.equal(dayRequest.cash_position.committed_spend_cents, null);
  assert.equal(dayRequest.cash_position.minimum_buffer_cents, null);
  assert.equal(dayRequest.cash_position.basis_confirmed, false);
});

test("ledger reference handles empty, loading, error, invalid date and changed-day states without showing stale totals", () => {
  const populatedReview = {
    business_day: "2026-10-17",
    record_count: 2,
    recorded_sales_cents: 18000,
    cash_sales_cents: 18000,
    card_sales_cents: 0,
    cash_expenses_cents: 0,
    record_status: "OPERATOR_REPORTED_RECORDS_MAY_BE_INCOMPLETE",
    cash_position_status: "NOT_PREPARED",
    events: [],
  };
  const changedDay = ledgerReferenceView({status: "loaded", targetDay: "2026-10-18", review: populatedReview});
  assert.equal(changedDay.status, "stale");
  assert.deepEqual(changedDay.rows, []);
  assert.match(changedDay.note, /never shown as 2026-10-18/);

  const emptyDay = ledgerReferenceView({
    status: "loaded",
    targetDay: "2026-10-18",
    review: {...populatedReview, business_day: "2026-10-18", record_count: 0, recorded_sales_cents: 0, cash_sales_cents: 0},
  });
  assert.equal(emptyDay.status, "empty");
  assert.deepEqual(emptyDay.rows, []);
  assert.match(emptyDay.note, /No sales or cash spending recorded in Record today for 2026-10-18 yet/);

  const loading = ledgerReferenceView({status: "loading", targetDay: "2026-10-18"});
  assert.equal(loading.status, "loading");
  assert.deepEqual(loading.rows, []);

  const errored = ledgerReferenceView({status: "error", targetDay: "2026-10-18"});
  assert.equal(errored.status, "error");
  assert.deepEqual(errored.rows, []);
  assert.match(errored.note, /Your money check stays separate/);

  const invalidDate = ledgerReferenceView({status: "loaded", targetDay: "invalid-day", review: populatedReview});
  assert.equal(invalidDate.status, "stale");
  assert.deepEqual(invalidDate.rows, []);
});
