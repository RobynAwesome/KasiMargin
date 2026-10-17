# Day 4 negative-test coverage review — 17 October 2026

**State:** locally tested on `codex/terra-context-plan`; delivery and provider validation remain pending. Codex Forge is the scoped CA renter, `I_AM_STATELESS_RENTER_NOT_LANDLORD`; no RTC seat or financial admission is implied.

## Scope and result

The calendar requirement was reviewed against executable behavior, rather than treated as an assertion that the product reads receipt images or operates a business ledger. The review added one missing regression: a populated transaction and obligation list cannot make a cash amount available when the operator has not confirmed the cash basis. It also strengthens the existing missing-cash-evidence test to require `HOLD_INSUFFICIENT_DATA` and no cash-headroom amount.

| Calendar concern | Executable coverage | Observed behavior |
| --- | --- | --- |
| Missing or stale receipts/evidence | `test_cash_evidence_cannot_be_replaced_by_invoice_evidence`; `test_each_unknown_cash_component_holds`; `test_stale_snapshot_holds` | An absent cash-evidence reference, unknown cash component, or stale snapshot blocks the cash answer. An obligation's invoice evidence cannot substitute for cash evidence. |
| Inconsistent cash and duplicate records | `test_snapshot_not_double_counted`; `test_duplicate_id_holds`; `test_duplicate_reference_across_buckets_holds`; `test_payment_must_match_amount_reference_and_snapshot` | The engine does not invent a balancing transaction. It preserves the supplied snapshot as the basis and returns a HOLD for duplicate, overlapping, unreconciled, or post-snapshot records. |
| Incomplete logs | `test_unconfirmed_cash_basis_holds_despite_populated_entries`; `test_missing_or_unconfirmed_obligations_hold`; `test_post_snapshot_transaction_holds` | A complete-looking list is not proof of a complete day. The explicit cash-basis confirmation and obligation coverage remain necessary; otherwise cash headroom is `null` and the status is `HOLD_INSUFFICIENT_DATA`. |
| Unsupported recommendations | `test_free_text_and_unauthorized_facts_are_rejected`; `test_warning_omission_is_rejected`; `test_invalid_model_prose_warning_omission_and_actions_fall_back` | The renderer admits only catalogued facts, required warnings, and permitted actions. Invalid local-model output is rejected and the deterministic explanation remains labelled as the fallback. |
| Stored decision tampering | `test_modified_amount_or_forged_recalculation_rejected`; `test_save_and_replay_without_model_or_overwrite` | A saved decision must replay its deterministic calculation. This is a decision receipt, not a merchant ledger. |

## Verification

Run from `C:\Users\rkhol\KasiMargin` after the test change:

```text
.venv\Scripts\python.exe -m unittest discover -s tests -v   # 63 passed
npm run check                                                  # TypeScript check/build and 6 Node tests passed
.venv\Scripts\python.exe -m compileall -q kasimargin tests   # passed
git diff --check                                               # passed
```

## Boundary retained

KasiMargin currently accepts structured, synthetic or operator-attested inputs. It does not inspect receipt images, verify bank/card settlement, discover omitted transactions, or retain an everyday durable sales ledger. The current controls make those states visible as unknown or blocked only when the operator supplies the applicable coverage signal. The next storage increment must introduce a separate event/correction/restart/idempotency contract and its own failure tests; it must not be inferred from this review.
