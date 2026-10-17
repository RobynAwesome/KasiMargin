# Local event-store contract — 17 October 2026

**State:** locally tested, not yet delivered to the review branch. Codex Forge is the scoped CA renter under `I_AM_STATELESS_RENTER_NOT_LANDLORD`; this is not a financial admission, a merchant deployment, or an observed operator result.

## What was added

`kasimargin.event_store.EventStore` is a small SQLite-backed service intended for a single local device. It is not exposed in the Flask API or the browser yet. The database path is supplied explicitly by the caller and production records belong under ignored `local-data/`.

It accepts only these first movements:

| Record | Supported payment methods | Meaning retained |
| --- | --- | --- |
| Sale | Cash or card | Operator-reported recorded sale; card sales remain separate from cash. |
| Expense | Cash | Operator-reported cash expense. |
| Refund, transfer, card expense, settlement, fee, credit collection and withdrawal | Not accepted | The caller must use a future explicit contract or a visible needs-review route; the store never guesses. |

Every accepted event has a stable event ID, idempotency key, exact integer cents, business day, occurred-at time, server-recorded time, source kind `OPERATOR_REPORTED`, revision, and correction lineage. A repeated key with the same content returns the original event; a repeated key with different content is rejected. Corrections insert a later revision and mark the prior revision non-current. A stale correction cannot silently win.

The day projection reports recorded sales, cash/card split and cash expenses. It deliberately reports `OPERATOR_REPORTED_RECORDS_MAY_BE_INCOMPLETE` and `NOT_PREPARED` for cash position. It does not calculate profit, spendable cash, bank/card settlement, or a financial decision.

## Failure tests and verification

The new `tests/test_event_store.py` verifies:

- atomic append and day replay after recreating the store from the same database;
- idempotent retry and divergent-retry conflict;
- correction lineage, projection replacement and stale-revision rejection;
- rejection without writes for unsupported movement semantics and non-browser-safe amounts;
- rollback after a conflicting event identifier.

An initial Windows test run showed that committed SQLite connections stayed open and prevented temporary-database cleanup. The store now closes every connection through its `_open()` context manager; the regression suite passes after that fix.

```text
.venv\Scripts\python.exe -m unittest discover -s tests -v   # 68 passed
npm run check                                                  # TypeScript check/build and 6 Node tests passed
.venv\Scripts\python.exe -m compileall -q kasimargin tests   # passed
git diff --check                                               # passed
```

## Next admissible increment

Add authenticated loopback endpoints and then a small, tested browser surface for **Record a sale**, **Record money spent**, and **See today**. Reuse the Host, Origin, session, body-size and request-budget controls already enforced by the Flask app. Before exposing the store to real local records, test endpoint idempotency, conflict responses, source-bound writes and an explicit backup/restore path. Do not route these records through the financial engine until an explicit reviewed snapshot supplies the engine's separate cash evidence.
