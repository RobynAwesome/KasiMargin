import test from "node:test";
import assert from "node:assert/strict";
import {ledgerCorrection, ledgerEntry} from "../kasimargin/web/build/ledger.js";

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
