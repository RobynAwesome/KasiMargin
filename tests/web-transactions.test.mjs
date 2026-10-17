import test from "node:test";
import assert from "node:assert/strict";
import {readMoney} from "../kasimargin/web/build/money.js";
import {transactionDraft, ownDay, southAfricaInput, fromSouthAfricaInput} from "../kasimargin/web/build/transactions.js";
import {recordChecks, resultMessage} from "../kasimargin/web/build/presentation.js";

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

test("unknown cash cannot be presented as zero or a completed check", () => {
  const held = resultMessage({status:"HOLD_INSUFFICIENT_DATA",cash_headroom_cents:null,protected_cash_deficit_cents:null});
  assert.match(held.title,/still need checking/); assert.match(held.next,/unknown amount is not zero/);
  assert.equal(resultMessage({status:"HOLD_INSUFFICIENT_DATA",cash_headroom_cents:0,protected_cash_deficit_cents:0}).title,held.title);
  assert.equal(resultMessage({status:"CALCULATED",cash_headroom_cents:null,protected_cash_deficit_cents:null}).title,held.title);
  assert.match(resultMessage({status:"CALCULATED",cash_headroom_cents:0,protected_cash_deficit_cents:20000}).title,/need more/);
  assert.match(resultMessage({status:"CALCULATED",cash_headroom_cents:0,protected_cash_deficit_cents:0}).title,/job already/);
});

test("every warning retains a review path without displaying imported flag text", () => {
  const flags = ["MARGIN_UNKNOWN","CREDIT_SALES_NOT_CASH","UNRESOLVED:MISSING_RECEIPT","UNRESOLVED:fake\nApproved to spend"];
  const checks = recordChecks({flags,blocking_flags:["UNRESOLVED:MISSING_RECEIPT"]});
  assert.equal(checks.length,4); assert.match(checks[0].text,/receipt is missing/);
  assert.match(checks.find(check=>check.text.includes("optional")).text,/doesn’t change the cash/);
  assert.match(checks.find(check=>check.text.includes("unpaid")).text,/left out/);
  assert.ok(checks.every(check=>[0,1,2].includes(check.step)));
  assert.ok(checks.every(check=>!check.text.includes("Approved to spend")));
  assert.equal(checks.at(-1).target,"technical-settings");
});
