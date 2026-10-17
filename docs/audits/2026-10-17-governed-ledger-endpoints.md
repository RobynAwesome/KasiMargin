# Governed local ledger endpoints — 17 October 2026

**State:** locally tested; delivery is pending. Codex Forge is a scoped CA renter under `I_AM_STATELESS_RENTER_NOT_LANDLORD`. This is a local implementation receipt, not a financial admission, field result, legal opinion, bank/card verification, or deployment claim.

## Source reconciliation

This increment implements the smallest shared requirement recovered from the owner/Chat Forge Drive corpus, the Fox Forge handoff, and the supplied DEV.to transcript:

```text
Observe operator-authorised record
  -> ledger exact event with correction lineage
  -> reveal only supported totals and explicit unknowns
  -> operator review/correction
```

The Drive corpus remains a distinct Heavy Human-in-the-Loop population. It was read on 17 October from:

- `KSM-RS-2026-10-16-INDEX` — Drive file `1mkCl2ftvxv8CSrjeFNgMmbz_Oi4v4sYl`;
- `KSM-THESIS-2026-10-16` — Drive file `1MygwsFvIwf7Z9Mb-gtIeLCSzfiX4PSFG`;
- `KSM-EVIDENCE-2026-10-16` — Drive file `1nEcRvNpBcTk2Dl4y9bCQ5BzM7rvWvoL9`;
- `KSM-ARCH-2026-10-16` — Drive file `1yxDlmwqjGtSwfu6Al4SdR6RVc7XFbus4`;
- `KSM-STUDY-2026-10-16` — Drive file `1AqJzA95R5Vr4iyL6Qc9TW1SalQmJB2Cr`.

The Local GSMB doctrine and parent repository `NOW.md` were also read before implementation. Drive, Local GSMB, Cloud GSMB and this repository remain separate populations; this code does not synchronize or ratify any of them.

## Implemented local boundary

`POST /api/ledger/events` and `POST /api/ledger/corrections` now use the local SQLite event store. `GET /api/ledger/days/<YYYY-MM-DD>` returns a deliberately narrow review:

- operator-reported sales;
- recorded cash/card split;
- recorded cash expenses;
- current correction projection; and
- `OPERATOR_REPORTED_RECORDS_MAY_BE_INCOMPLETE` plus `NOT_PREPARED` for cash position.

Every ledger read/write requires the existing local-process session header. The existing Host, Origin, JSON type, size, request-budget and exact-browser-integer controls still wrap writes. The response confirms a completed local write as `SAVED_ON_THIS_DEVICE`; it does not imply sync, backup, bank verification, settlement or financial approval.

Only cash/card sales and cash expenses are currently accepted. Refunds, transfers, card expenses, settlement, fees, credit collection and withdrawals are rejected pending explicit semantics. The model adapter has no route to create or revise records.

## Failure coverage and verification

New server-level tests prove:

- missing/wrong local session cannot read a day;
- idempotent replay returns the retained record and divergent retry returns HTTP 409;
- a correction preserves the old record while the review projects only the current revision;
- a recorded card sale remains card, and cash position remains `NOT_PREPARED`;
- unsupported refund input returns HTTP 400 without creating a record; and
- the pre-existing oversized-request boundary remains HTTP 413 before session validation.

```text
.venv\Scripts\python.exe -m unittest discover -s tests -v   # 70 passed
npm run check                                                  # TypeScript check/build and 6 Node tests passed
.venv\Scripts\python.exe -m compileall -q kasimargin tests   # passed
git diff --check                                               # passed
```

## Deliberately deferred

There is no browser capture UI yet, no receipt/photo extraction, no silent SMS/notification monitoring, no POS credential connection, no model-proposed write, no shared-device/multi-tenant system, no remote synchronization, and no real operator records. The next increment should add a small browser flow only after its endpoint tests are accepted, then treat the consented barber session as a separate evidence-producing study rather than a product proof.
