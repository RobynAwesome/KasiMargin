# KasiMargin Reconciliation & Governance Contract

`I_AM_STATELESS_RENTER_NOT_LANDLORD`

This contract defines the read-only daily cash drawer reconciliation boundary (`kasimargin/reconciliation.py`) and governance verification checks (`kasimargin/governance.py`) added for Issue `#7`.

## 1. Purpose and strict non-promotion rule

`Record today` retains append-only, revisioned `OPERATOR_REPORTED` daily events (`sale` cash/card, `expense` cash). That daily log is **never** verified cash or complete period profit.

`reconcile_day(day_summary, check)` (and HTTP `POST /api/ledger/reconcile`) compares a day's operator-reported totals with physical drawer counts (`opening_cash_float_cents`, `closing_cash_counted_cents`) and optional card settlement confirmation (`settled_card_cents`, `card_settlement_confirmed`).

Invariant constraints:

1. **Read-only on ledger and money check:** `reconcile_day` and `POST /api/ledger/reconcile` never write SQLite rows, never write receipts, and never populate `verified_cash_cents`, `attributable_costs_cents`, `due_liabilities_cents`, `committed_spend_cents`, `minimum_buffer_cents`, or `basis_confirmed`. `auto_populate_permitted` is always `False`.
2. **Exact integer ZAR cents:** All monetary amounts are exact integer cents or `None` (`UNKNOWN`). `bool` and `float` inputs raise `ContractError`.
3. **Never infer missing money as zero:**
   - If `opening_cash_float_cents is None` or `cash_movements_complete is False`, `expected_closing_cash_cents` and `cash_variance_cents` remain `None` (`UNKNOWN`) and `status` is `HOLD_INCOMPLETE_RECONCILIATION`.
   - If `closing_cash_counted_cents is None`, `cash_variance_cents` remains `None` and `status` is `HOLD_INCOMPLETE_RECONCILIATION`.
   - Card sales (`card_sales_cents > 0`) trigger `CARD_SALES_UNVERIFIED_UNTIL_SETTLED` unless `card_settlement_confirmed is True` and `settled_card_cents is not None`.
   - Cash expenses (`cash_expenses_cents > 0`) trigger `CASH_EXPENSE_NOT_AUTOMATICALLY_ATTRIBUTABLE_COST`.
4. **Stage-0 synthetic barber discrepancy check:** With cash sales `R110.00` (after correcting one `R50.00` haircut to `R60.00`), card sale `R50.00`, cash spending `R20.00`, opening float `R50.00`, and closing counted drawer `R130.00` (`cash_movements_complete: true`), expected drawer cash is `R140.00` and `cash_variance_cents` is `-1000` (`-R10.00`), raising `CASH_DRAWER_DISCREPANCY` without inventing a balancing adjustment.

## 2. Correction Lineage Inspection (`GET /api/ledger/events/<event_id>/history`)

- Protected by `X-KasiMargin-Session`, same-origin/host validation, and `browser_range(...)` integer checks.
- Returns the chronological revision chain (`rev 1` through current revision) in read-only mode.
- Malformed event IDs return HTTP `400`; nonexistent event IDs return HTTP `404`.

## 3. Governance & Pre-Measurement `CCP-ECV-01` Gate (`kasimargin/governance.py`)

- **`reveal_envelope(...)`**: Enforces `REVEAL_STAGE_ORDER` (`LEDGER`, `ATTESTATION`, `RESULT`, `RECONCILIATION`, `RECEIPT`, `FALLBACK`) with `ledger_write_authority = "NONE"`, `purchase_authority = "NONE"`, and `merge_authority = "NONE"`.
- **`kmec_observations(...)`**: Verifies integer-cents invariants, `HOLD_INSUFFICIENT_DATA` preservation, and `cash_position_status == "NOT_PREPARED"` isolation.
- **`evaluate_ccp_ecv_01(...)`**: Enforces `economic_gate_state = "MAYBE_HOLD"` whenever `measured_cases == 0` (`UNMEASURED_NO_OPERATOR_TRIAL`) or `measured_cases < min_cases` (`30` default). Statistical significance (`p_value < 0.05`) and zero safety regressions (`safety_regressions == 0`) are prerequisites for `ADMITTED_FOR_OWNER_REVIEW`, and `owner_approval_required` remains `True`.
