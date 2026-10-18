import {readMoney} from "./money.js";
import {fromSouthAfricaInput} from "./transactions.js";

export interface LedgerSaveResult { save_status: "SAVED_ON_THIS_DEVICE" }

// A definite rejection means the server did not write this request. A lost
// response is different: retry that exact request with the same identity.
export class LedgerSaveRejected extends Error {}

export class LedgerSaver<T extends {id: string; idempotency_key: string}> {
  private pending: {signature: string; request: T} | null = null;
  private active: Promise<LedgerSaveResult> | null = null;

  constructor(private send: (request: T) => Promise<LedgerSaveResult>) {}

  save(candidate: T): Promise<LedgerSaveResult> {
    const {id: _id, idempotency_key: _key, ...content} = candidate;
    const signature = JSON.stringify(content);
    if (this.pending && signature !== this.pending.signature) {
      return Promise.reject(new Error("The previous save is not confirmed. Retry the unchanged entry before recording something different. Keep this page open."));
    }
    if (this.active) return this.active;
    this.pending ??= {signature, request: structuredClone(candidate)};
    // Copy before sending so a caller cannot change a retained retry payload.
    const request = structuredClone(this.pending.request);
    this.active = Promise.resolve().then(() => this.send(request)).then(result => {
      if (result.save_status !== "SAVED_ON_THIS_DEVICE") throw new Error("Save not confirmed. Keep this page open and retry the unchanged entry.");
      this.pending = null;
      return result;
    }).catch((error: unknown) => {
      if (error instanceof LedgerSaveRejected) this.pending = null;
      throw error;
    }).finally(() => { this.active = null; });
    return this.active;
  }
}

export type LedgerEventType = "sale" | "expense";
export type LedgerPaymentMethod = "cash" | "card";

export interface LedgerEvent {
  id: string;
  idempotency_key: string;
  business_day: string;
  event_type: LedgerEventType;
  payment_method: LedgerPaymentMethod;
  amount_cents: number;
  occurred_at: string;
  source_kind: "OPERATOR_REPORTED";
  revision: number;
  replaces_id: string | null;
  correction_reason: string | null;
  is_current: 0 | 1;
}

export interface LedgerDay {
  business_day: string;
  events: LedgerEvent[];
  recorded_sales_cents: number;
  cash_sales_cents: number;
  card_sales_cents: number;
  cash_expenses_cents: number;
  record_count: number;
  record_status: "OPERATOR_REPORTED_RECORDS_MAY_BE_INCOMPLETE";
  cash_position_status: "NOT_PREPARED";
}

export interface LedgerEntryValues {
  id: string;
  idempotencyKey: string;
  eventType: LedgerEventType;
  paymentMethod: LedgerPaymentMethod;
  amount: string;
  when: string;
}

export interface LedgerCorrectionValues {
  id: string;
  idempotencyKey: string;
  replaces: LedgerEvent;
  amount: string;
  when: string;
  reason: string;
}

function shortText(value: string, name: string, required: boolean): string | null {
  if (!value.trim()) {
    if (required) throw new Error(`${name} is needed.`);
    return null;
  }
  if (value.length > 280) throw new Error(`${name} is too long.`);
  return value;
}

export function ledgerEntry(values: LedgerEntryValues): Omit<LedgerEvent, "revision" | "replaces_id" | "correction_reason" | "is_current"> {
  if (values.eventType === "expense" && values.paymentMethod !== "cash") throw new Error("This early version records cash spending only.");
  const occurredAt = fromSouthAfricaInput(values.when);
  return {
    id: shortText(values.id, "Record ID", true)!,
    idempotency_key: shortText(values.idempotencyKey, "Save key", true)!,
    business_day: values.when.slice(0, 10),
    event_type: values.eventType,
    payment_method: values.paymentMethod,
    amount_cents: requireAmount(values.amount),
    occurred_at: occurredAt,
    source_kind: "OPERATOR_REPORTED",
  };
}

export function ledgerCorrection(values: LedgerCorrectionValues): {id: string; idempotency_key: string; replaces_id: string; expected_revision: number; amount_cents: number; occurred_at: string; reason: string | null} {
  return {
    id: shortText(values.id, "Correction ID", true)!,
    idempotency_key: shortText(values.idempotencyKey, "Save key", true)!,
    replaces_id: values.replaces.id,
    expected_revision: values.replaces.revision,
    amount_cents: requireAmount(values.amount),
    occurred_at: fromSouthAfricaInput(values.when),
    reason: shortText(values.reason, "Reason", false),
  };
}

function requireAmount(value: string): number {
  const amount = readMoney(value);
  if (amount === null || amount === 0) throw new Error("Enter an amount greater than R0.00.");
  return amount;
}

export type LedgerReferenceInput =
  | {status: "loading"; targetDay: string}
  | {status: "error"; targetDay: string}
  | {status: "loaded"; targetDay: string; review: LedgerDay | null};

export interface LedgerReferenceView {
  status: "loading" | "error" | "stale" | "empty" | "ready";
  note: string;
  rows: ReadonlyArray<readonly [string, number]>;
}

export function ledgerReferenceView(input: LedgerReferenceInput): LedgerReferenceView {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(input.targetDay)) {
    return {
      status: "stale",
      note: "Choose when you checked this money to see that date’s recorded sales and cash spending.",
      rows: [],
    };
  }
  if (input.status === "loading") {
    return {
      status: "loading",
      note: `Loading recorded sales and cash spending for ${input.targetDay}…`,
      rows: [],
    };
  }
  if (input.status === "error") {
    return {
      status: "error",
      note: `Could not load recorded sales or cash spending for ${input.targetDay}. Your money check stays separate—enter your counted cash and bills below.`,
      rows: [],
    };
  }
  const review = input.review;
  if (
    !review ||
    review.business_day !== input.targetDay ||
    review.record_status !== "OPERATOR_REPORTED_RECORDS_MAY_BE_INCOMPLETE" ||
    review.cash_position_status !== "NOT_PREPARED"
  ) {
    return {
      status: "stale",
      note: `Records from another date are hidden so a previous day’s figures are never shown as ${input.targetDay}.`,
      rows: [],
    };
  }
  if (review.record_count === 0) {
    return {
      status: "empty",
      note: `No sales or cash spending recorded in Record today for ${input.targetDay} yet. Count your cash and enter your figures below, or open Record today first.`,
      rows: [],
    };
  }
  return {
    status: "ready",
    note: `Operator-reported for ${input.targetDay} (${review.record_count} record${review.record_count === 1 ? "" : "s"}). Not verified cash: these figures are for reference only and never fill in your money check automatically. Count your cash and check card settlement separately.`,
    rows: [
      ["Sales recorded", review.recorded_sales_cents],
      ["Cash sales recorded", review.cash_sales_cents],
      ["Card sales recorded", review.card_sales_cents],
      ["Cash spending recorded", review.cash_expenses_cents],
    ],
  };
}
