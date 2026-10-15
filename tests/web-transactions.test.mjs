import test from "node:test";
import assert from "node:assert/strict";
import {readMoney} from "../kasimargin/web/build/money.js";
import {transactionDraft, ownDay, southAfricaInput, fromSouthAfricaInput} from "../kasimargin/web/build/transactions.js";

test("rand entry preserves exact cents and unknowns", () => {
  assert.equal(readMoney(""), null); assert.equal(readMoney("0"), 0);
  assert.equal(readMoney("19.99"), 1999); assert.equal(readMoney("0.01"), 1);
  assert.equal(readMoney("90071992547409.91"), Number.MAX_SAFE_INTEGER);
  for (const value of ["90071992547409.92","-1","1e3","NaN","1.001","1,20"]) assert.throws(() => readMoney(value));
});
test("South Africa dates retain their instant across UTC day boundaries", () => {
  assert.equal(southAfricaInput("2026-10-14T22:30:00Z"), "2026-10-15T00:30");
  assert.equal(fromSouthAfricaInput("2026-10-15T00:30"), "2026-10-15T00:30:00+02:00");
  for (const value of ["", "2026-02-30T12:00", "2026-10-15T25:00"]) assert.throws(() => fromSouthAfricaInput(value));
});
test("transaction drafts retain confirmation, references and credit-sale identity", () => {
  const row = transactionDraft({id:"tx-1",kind:"credit_sale",amount:"123.45",reference:" invoice-1 ",when:"2026-10-15T10:00",note:" unpaid ",confirmed:false});
  assert.equal(row.amount_cents, 12345); assert.equal(row.kind,"credit_sale"); assert.equal(row.is_confirmed,false);
  assert.equal(row.reference_id,"invoice-1"); assert.equal(row.timestamp,"2026-10-15T10:00:00+02:00");
  assert.throws(() => transactionDraft({id:"x",kind:"cash_sale",amount:"",reference:"r",when:"2026-10-15T10:00",note:"",confirmed:true}));
});
test("a new day contains unknown money and no invented confirmation", () => {
  const day = ownDay(new Date("2026-10-15T08:00:00Z"));
  assert.equal(day.cash_position.verified_cash_cents,null); assert.equal(day.cash_position.due_liabilities_cents,null);
  assert.equal(day.cash_position.basis_confirmed,false); assert.equal(day.performance.complete,false);
  assert.deepEqual(day.transactions,[]); assert.deepEqual(day.cash_position.evidence_refs,[]);
});
