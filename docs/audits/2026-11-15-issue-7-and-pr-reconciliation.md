# Issue #7 & Pull Request Reconciliation Audit

- **Date:** 2026-11-15
- **Constraint:** `I_AM_STATELESS_RENTER_NOT_LANDLORD`
- **Repository baseline:** `main@85d3cc9398701c451734eafe62aa1d15770fc6d1`
- **Review branch:** `codex/issue-7-reconciliation-and-fixes`
- **Authority note:** Consequential authority (merge, deploy, closing Issue `#7`, publication, economic claims) remains exclusively with Robyn. Historical receipts in `docs/` were left untouched.

## 1. GitHub PR & Issue Audit (`RobynAwesome/KasiMargin`)

All 8 pull requests created prior to this branch are merged into `main`, with `0` open pull requests and `1` open issue (`#7`, `[HF26 Week 2] Submission readiness, Gemma-value boundary & governed operator validation`):

| Item | State | Head / Merge Commit | Focus |
|---|---|---|---|
| PR `#1` | MERGED | `67f10739` | Local cash decision foundation |
| PR `#2` | MERGED | `737f3b9f` | KasiMargin logo, light/dark modes, branded README |
| PR `#3` | MERGED | `5a0326a4` | TypeScript, Flask and local Gemma evaluation |
| PR `#4` | MERGED | `3d16c97b` | Guided daily journey for cash check |
| PR `#5` | MERGED | `579bfec3` | Terra execution and barber validation handoff |
| PR `#6` | MERGED | `e900fcd6` | Daily SQLite ledger, safe retries and synthetic demo |
| Issue `#7` | OPEN | — | HF26 Week 2 submission readiness, Gemma-value boundary & operator validation (no PR `#7` exists) |
| PR `#8` | MERGED | `17f397fe` | Primary decision explanation & read-only ledger reference |
| PR `#9` | MERGED | `85d3cc93` | Align `NOW.md` and DEV draft with merged `main@17f397f` |

### Automated Review Gap Found

Automated Codex Cloud code reviews on PRs `#1`–`#9` reported zero completed reviews due to Codex usage-limit failures, leaving PR `#6`, PR `#8`, and PR `#9` without an independent line-by-line review receipt. A direct code audit of `main@85d3cc9` identified and resolved five concrete implementation defects on this branch:

1. **Duplicate transaction flag duplication & whitespace evasion (`kasimargin/obligations.py`, `kasimargin/engine.py`):** `obligations.py` pushed `"DUPLICATE_TRANSACTION_ID"` into `unresolved_flags`, causing `engine.py` to emit both `"DUPLICATE_TRANSACTION_ID"` and `"UNRESOLVED:DUPLICATE_TRANSACTION_ID"`, while `engine.py` checked `transaction["id"]` and `transaction["reference_id"]` without `.strip()`. Both are now normalized without duplicate unresolved prefix emission.
2. **SQLite locking, missing-event distinction, and browser integer guard (`kasimargin/event_store.py`, `kasimargin/server.py`):** Added `timeout=10.0` + `PRAGMA busy_timeout = 5000`, introduced `EventNotFoundError(ContractError)` so malformed IDs return `400` and unknown IDs return `404` on the new read-only `GET /api/ledger/events/<event_id>/history` route, added `sqlite3.Error` handling, and enforced `browser_range(...)` on `GET /api/ledger/days/<business_day>`.
3. **Stale date / race condition / invalid calendar date in `Record today` (`kasimargin/web/src/app.ts`):** Cleared `#ledger-date` and `#ledger-empty` when `ledgerReview` is null, guarded `loadLedger()` against out-of-order responses with `ledgerLoadRevision`, reloaded `correctionTarget.business_day` instead of `#ledger-when` after saving a correction, validated `ledgerDayFromInput()` with `fromSouthAfricaInput`, and added a read-only `"History"` toggle for corrected events.
4. **`#replace-confirm` hidden-`#error` trap (`kasimargin/web/src/app.ts`):** When confirming day replacement while `#journey` was hidden, `start()` previously wrote to hidden `#error` and returned. Confirmed replacement now bypasses cleanly after explicit confirmation, and switching back from `SYNTHETIC` via `#ledger-to-check` prompts consistently.
5. **Session reset (`403`) clearing retry identity (`kasimargin/web/src/ledger.ts`, `kasimargin/web/src/app.ts`):** `403` is now treated as retryable rather than `LedgerSaveRejected`, retaining `LedgerSaver.pending` across local server restarts, while definite rejections (`400`, `409`, etc.) report `"No entry/correction was saved."` instead of asking the operator to retry.

## 2. Issue #7 Verification & Scope Disposition

| Requirement | Status on Branch | Evidence / Reason |
|---|---|---|
| **P0:** Live DEV.to submission & signed-out MP4 | Verified live (historical) | DEV article `4874175` (`https://dev.to/robynawesome/kasimargin-2h3j`) published `2026-10-18T21:40:54Z` (`23:40:54 SAST`) with `#hf26challenge` banner & Completion badge; Oct 23 winners post excluded KasiMargin; signed-out raw MP4 returns HTTP `200` (`2763961` bytes, SHA-256 `e6a64df...`). Owner playback receipt remains pending in `docs/`. |
| **P1 #1 & #4:** Read-only correction history UI & reveal envelope | Implemented & tested | `GET /api/ledger/events/<event_id>/history`, `"History"` toggle in UI, `kasimargin/governance.py` `reveal_envelope` with `ledger_write_authority="NONE"`. Live barber walkthrough remains UNRUN. |
| **P1 #2:** Drawer cash & card reconciliation without auto-fill | Implemented & tested | `kasimargin/reconciliation.py` (`reconcile_day`) + `POST /api/ledger/reconcile` + `docs/RECONCILIATION-CONTRACT.md`; verifies Stage-0 synthetic barber `R50->R60` `-R10.00` variance & holds on incomplete movements. |
| **P1 #3:** OCR / POS / SMS / offline / multilingual / RAG | Out of scope (unimplemented) | Explicitly preserved as future roadmap items; no unsupported capability claimed. |
| **P1 #5:** External Google Drive / OneDrive / GSMB sync | Verified external / read-only | Drive folder contains CA hand-in + research corpus matching `local-data/assessment-2026-10-18/`; local OneDrive holds only Day 1 + Public; external GSMB/Cloud repos remain untouched outside KasiMargin. |
| **P1 #6:** Pre-measurement `CCP-ECV-01` boundary | Implemented & tested | `evaluate_ccp_ecv_01(0)` enforces `MAYBE_HOLD` (`UNMEASURED_NO_OPERATOR_TRIAL`) until `n>=30` paired operator cases pass safety and statistical thresholds with owner approval. |

Because live operator field testing, owner playback sign-off, and external GSMB synchronization cannot be simulated in synthetic unit tests, **Issue `#7` should remain OPEN** until Robyn reviews this PR and decides whether to close or split remaining field items.
