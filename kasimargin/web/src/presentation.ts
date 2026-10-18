import type {Inference, Summary} from "./types.js";

export interface RecordCheck {text: string; step: number; target?: string;}
export interface ProvenanceText {operatorState: string; technicalDetail: string;}
// Interface wording only. The Python engine and model gate decide the result.
const checks: Record<string, RecordCheck> = {
  MARGIN_UNKNOWN: {text:"Sales or their costs are still missing. You can leave this optional check for later; it doesn’t change the cash calculation.", step:2, target:"profit-review"},
  UNKNOWN_VERIFIED_CASH_CENTS: {text:"Check the business money you can use now. Money customers still owe is left out.",step:0,target:"verified_cash_cents"},
  UNKNOWN_DUE_LIABILITIES_CENTS: {text:"Add the bills still due. If there are none, choose ‘No bills to pay’ after checking.",step:1,target:"due_liabilities_cents"},
  UNKNOWN_COMMITTED_SPEND_CENTS: {text:"Check other money you’ve promised, such as a planned delivery. Don’t repeat a bill already listed.",step:1,target:"committed_spend_cents"},
  UNKNOWN_MINIMUM_BUFFER_CENTS: {text:"Choose what to keep aside. Leave it blank while you decide; choose zero only if you intend to keep nothing aside.",step:2,target:"minimum_buffer_cents"},
  CASH_BASIS_UNCONFIRMED: {text:"Review your cash and payments, then tick the confirmation if the figures are complete.",step:2,target:"cash-confirmed"},
  MISSING_CASH_EVIDENCE: {text:"Your cash check has no supporting reference. Review your records and confirmation.",step:2,target:"cash-confirmed"},
  STALE_CASH_SNAPSHOT: {text:"Your count is too old for this check. Check the money again and update when you counted it.",step:0,target:"record-snapshot"},
  POST_SNAPSHOT_TRANSACTION: {text:"Money moved after your count. Count again so your balance includes it.",step:0,target:"record-snapshot"},
  DUPLICATE_TRANSACTION_ID: {text:"Two records have the same identity. Review the full record before using these figures.",step:2,target:"technical-settings"},
  UNCONFIRMED_TRANSACTION: {text:"A supporting transaction still needs checking. Review it before using the cash result.",step:2,target:"supporting-records"},
  POSSIBLE_DUPLICATE_PAYMENT: {text:"Two payments may be for the same bill. Check the references so it isn’t counted twice.",step:2,target:"supporting-records"},
  CREDIT_SALES_NOT_CASH: {text:"A customer sale is still unpaid. That money is left out of the cash available now.",step:2,target:"supporting-records"},
  RECEIVABLES_RECONCILIATION_REQUIRED: {text:"Customer payments are greater than the credit sales recorded here. Check earlier customer balances.",step:2,target:"supporting-records"},
  PROTECTED_CASH_DEFICIT: {text:"The money recorded does not cover all the payments and the amount you want to keep aside.",step:1},
  NO_DISCRETIONARY_HEADROOM: {text:"There’s no money left after these payments and the amount kept aside.",step:1},
  "UNRESOLVED:MISSING_RECEIPT": {text:"A receipt is missing. Find it or resolve the missing record before using this cash result.",step:2,target:"supporting-records"},
  "UNRESOLVED:DUPLICATE_OR_OVERLAPPING_OBLIGATION": {text:"A bill may be listed twice. Review the bills and other promises together.",step:2,target:"technical-settings"},
  "UNRESOLVED:OBLIGATIONS_INCOMPLETE": {text:"The itemised bills are not confirmed complete. Review the list before confirming it.",step:2,target:"cash-confirmed"},
  "UNRESOLVED:UNCONFIRMED_OBLIGATION": {text:"An itemised bill still needs checking.",step:2,target:"technical-settings"},
  "UNRESOLVED:UNKNOWN_OBLIGATION_AMOUNT": {text:"A bill or the amount already paid is unknown. Check it before using this result.",step:2,target:"technical-settings"},
  "UNRESOLVED:OBLIGATION_OVERPAID": {text:"The payment recorded is larger than its bill. Check the amounts.",step:2,target:"technical-settings"},
  "UNRESOLVED:PAYMENT_ALLOCATED_MORE_THAN_ONCE": {text:"The same payment is linked to more than one bill. Review those links.",step:2,target:"technical-settings"},
  "UNRESOLVED:MISSING_OBLIGATION_PAYMENT": {text:"A bill refers to a payment record that is missing. Find and check that record.",step:2,target:"technical-settings"},
  "UNRESOLVED:OBLIGATION_PAYMENT_NOT_RECONCILED": {text:"A payment does not match its bill or payment time. Check the linked records.",step:2,target:"technical-settings"},
  "UNRESOLVED:OBLIGATION_PAYMENT_TOTAL_MISMATCH": {text:"The paid amount and linked payment records don’t add up. Check them together.",step:2,target:"technical-settings"},
  "UNRESOLVED:UNALLOCATED_OBLIGATION_PAYMENT": {text:"A payment has not been linked to its bill. Review it so money isn’t counted twice.",step:2,target:"technical-settings"},
};
export function recordChecks(summary: Pick<Summary,"flags"|"blocking_flags">): RecordCheck[] {
  // Include every warning, even an unfamiliar one. Never render raw imported flags as prose.
  const flags = [...new Set([...summary.blocking_flags,...summary.flags])];
  return flags.map(flag => checks[flag] ?? {text:"A record still needs review. Open the full record and technical explanation before using this result.",step:2,target:"technical-settings"});
}
export function resultMessage(summary: Pick<Summary,"status"|"cash_headroom_cents"|"protected_cash_deficit_cents">): {title:string; next:string} {
  if (summary.status !== "CALCULATED" || summary.cash_headroom_cents === null) return {title:"A few things still need checking",next:"We can’t tell what’s left yet. Start with the checks below; an unknown amount is not zero."};
  if (summary.protected_cash_deficit_cents !== null && summary.protected_cash_deficit_cents > 0) return {title:"These payments need more than you have",next:"There’s a shortfall in the figures you checked. Review what’s due and what you need to keep aside before making another commitment."};
  if (summary.cash_headroom_cents === 0) return {title:"All of this money has a job already",next:"These payments and the amount kept aside use the money recorded. Check what’s due before making another commitment."};
  return {title:"Here’s what your figures leave",next:"Check that no bills or promises are missing before deciding how to use what’s left."};
}
export function inferenceProvenance(inference: Inference): ProvenanceText {
  if (inference.status === "ADMITTED") {
    return {
      operatorState: "The local assistant selected these explanation points. The calculation supplied every amount.",
      technicalDetail: `Model: ${inference.model}. Digest: ${inference.digest}`,
    };
  }
  if (inference.status === "NOT_REQUESTED") {
    return {
      operatorState: "Calculated explanation. No AI assistant was requested.",
      technicalDetail: "Explanation source: deterministic template.",
    };
  }
  return {
    operatorState: "The assistant's answer was unavailable or did not pass the checks. You are seeing the calculated explanation instead.",
    technicalDetail: `Fallback reason: ${inference.reason}`,
  };
}
