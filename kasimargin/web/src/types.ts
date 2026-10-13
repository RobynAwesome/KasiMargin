/** Compile-time contracts. Server validators remain the runtime authority. */
export type Money = number | null;
export type Theme = "light" | "dark";
export type DataClass = "SYNTHETIC" | "OPERATOR_ATTESTED";
export interface Performance {
  recorded_sales_cents: Money;
  attributable_costs_cents: Money;
  complete: boolean;
}
export interface CashPosition {
  verified_cash_cents: Money;
  minimum_buffer_cents: Money;
  snapshot_at: string;
  decision_at: string;
  horizon_end: string;
  max_snapshot_age_seconds: number;
  basis_confirmed: boolean;
  unresolved_flags: string[];
  evidence_refs: string[];
  due_liabilities_cents?: Money;
  committed_spend_cents?: Money;
  obligations_complete?: boolean;
}
export interface Transaction {
  id: string;
  kind: "cash_sale" | "credit_sale" | "credit_collection" | "supplier_payment" | "operating_payment";
  amount_cents: number;
  is_confirmed: boolean;
  reference_id: string;
  timestamp: string;
  source_description: string;
}
export interface Obligation {
  id: string;
  reference_id: string;
  bucket: "liability" | "committed";
  amount_cents: Money;
  paid_cents: Money;
  due_at: string;
  is_confirmed: boolean;
  payment_transaction_ids: string[];
  evidence_ref: string;
}
export interface FinancialRequest {
  schema_version?: "kasimargin-input-v2";
  currency: "ZAR";
  performance: Performance;
  cash_position: CashPosition;
  transactions: Transaction[];
  obligations?: Obligation[];
}
export interface Fixture { fixture_id: string; scenario: string; data_class: DataClass; input: FinancialRequest; }
export interface Selection { fact_ids: string[]; flag_ids: string[]; action_ids: string[]; }
export interface CashBasis {
  verified_cash_cents: Money;
  due_liabilities_cents: Money;
  committed_spend_cents: Money;
  minimum_buffer_cents: Money;
  snapshot_at: string;
  decision_at: string;
}
export interface Summary {
  operating_margin_cents: Money;
  cash_headroom_cents: Money;
  protected_cash_deficit_cents: Money;
  status: "CALCULATED" | "HOLD_INSUFFICIENT_DATA";
  flags: string[];
  blocking_flags: string[];
  horizon_end: string;
  cash_basis: CashBasis;
}
export type Inference =
  | {status: "NOT_REQUESTED"; model: null}
  | {status: "ADMITTED"; model: string; digest: string}
  | {status: "REJECTED_OR_UNAVAILABLE"; model: string; reason: string};
export interface DecisionResult {
  summary: Summary;
  selection: Selection;
  explanation: string;
  inference: Inference;
  baseline_selection: Selection;
  baseline_explanation: string;
  receipt_filename?: string;
}
export interface DecisionPayload { input: FinancialRequest; model: string | null; save_receipt: boolean; data_class: DataClass; }
