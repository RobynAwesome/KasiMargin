import {readMoney} from "./money.js";
import type {FinancialRequest, Transaction} from "./types.js";

export const transactionLabels: Record<Transaction["kind"], string> = {
  cash_sale:"Paid sale", credit_sale:"Sale on credit", credit_collection:"Payment for earlier credit",
  supplier_payment:"Supplier payment", operating_payment:"Other business payment",
};
export function southAfricaInput(value: string): string {
  const parts = new Intl.DateTimeFormat("en-CA", {timeZone:"Africa/Johannesburg", year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).formatToParts(new Date(value));
  const get = (type: string) => parts.find(part => part.type === type)?.value ?? "";
  return `${get("year")}-${get("month")}-${get("day")}T${get("hour")}:${get("minute")}`;
}
export function fromSouthAfricaInput(value: string): string {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)) throw new Error("Choose a date and time for this record.");
  const timestamp = `${value}:00+02:00`;
  if (!Number.isFinite(Date.parse(timestamp)) || southAfricaInput(timestamp) !== value) throw new Error("That date or time is not valid. Please check it.");
  return timestamp;
}
export function transactionDraft(fields: {id:string; kind:string; amount:string; reference:string; when:string; note:string; confirmed:boolean}): Transaction {
  if (!Object.hasOwn(transactionLabels, fields.kind)) throw new Error("Choose what happened.");
  const amount = readMoney(fields.amount);
  if (amount === null) throw new Error("Add the amount for this record. Leave unknown cash in the cash-count field.");
  if (!fields.id.trim() || !fields.reference.trim()) throw new Error("Add a receipt or reference so this record can be checked later.");
  return {id:fields.id,kind:fields.kind as Transaction["kind"],amount_cents:amount,reference_id:fields.reference.trim(),
    timestamp:fromSouthAfricaInput(fields.when),source_description:fields.note.trim(),is_confirmed:fields.confirmed};
}
export function ownDay(now = new Date()): FinancialRequest {
  return {currency:"ZAR", performance:{recorded_sales_cents:null,attributable_costs_cents:null,complete:false},
    cash_position:{verified_cash_cents:null,due_liabilities_cents:null,committed_spend_cents:null,minimum_buffer_cents:null,
      snapshot_at:now.toISOString(),decision_at:now.toISOString(),horizon_end:new Date(now.getTime()+86400000).toISOString(),
      max_snapshot_age_seconds:900,basis_confirmed:false,unresolved_flags:[],evidence_refs:[]},transactions:[]};
}
