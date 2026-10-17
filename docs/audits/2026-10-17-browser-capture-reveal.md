# Browser capture and reveal review — 2026-10-17

## Scope

This increment turns the protected local ledger into a small operator-facing
flow. It implements one part of the recovered Drive and DEV.to direction:

> observe an operator-entered event → retain it locally → reveal only what it
> supports → let the operator correct it.

The sources are still separate populations. The Drive research handoff is
Heavy Human-in-the-Loop source material; Local code and Cloud review are not
a Drive synchronization, KPGS runtime activation, legal conclusion, financial
admission or user-study result.

## What the browser now does

- The welcome page has **Record today’s sales or spending** alongside the
  existing money-check journey.
- The record view takes one paid sale or one cash expense at a time, keeps
  integer cents and a South African local timestamp, and sends the event only
  after the operator confirms what they are recording.
- Cash and card sales remain visibly separate. Choosing cash spending disables
  the card choice because card expenses are outside this bounded first record
  contract.
- The daily reveal labels four facts as *recorded*: sales, cash sales, card
  sales and cash spending. It always states that records may be incomplete and
  that the cash position is not prepared.
- A current record has **Correct amount**. Saving a correction creates the
  server's append-only replacement event with its revision; it does not delete
  the original event.

`ledger.ts` has the browser-side, exact-cent payload boundary. Flask remains
the runtime gate: it requires the local session, strict JSON, valid event
shape, a browser-safe integer, an idempotency key and the event-store's stale
revision check.

## Source alignment

This implements only the narrow overlap in the recovered sources:

| Source population | Locator | Applied direction |
| --- | --- | --- |
| Heavy Human-in-the-Loop GSMB / Drive | `1MygwsFvIwf7Z9Mb-gtIeLCSzfiX4PSFG` | Ledger is append/correction lineage, optional and distinct from a payment processor. |
| Heavy Human-in-the-Loop GSMB / Drive | `1nEcRvNpBcTk2Dl4y9bCQ5BzM7rvWvoL9` | A cash photo, payment notification or remembered amount is not independent proof; false confirmation must hold. |
| Heavy Human-in-the-Loop GSMB / Drive | `1yxDlmwqjGtSwfu6Al4SdR6RVc7XFbus4` | Observe, admit evidence, calculate/reveal selectively, then review and correct. |
| Owner-supplied DEV.to export | `f2ac2248-ca28-4ccb-8b20-e58d40198dfc/Pasted text.txt` | Fit the barber's ordinary work; do not replace existing payment tools or describe recorded sales as available cash. |

## Validation

- `npm run check`: strict TypeScript build and eight Node tests pass. New tests
  prove exact-cent daily entries, South African timestamps, cash-only spending
  and revision-bound corrections.
- `.venv\Scripts\python.exe -m unittest discover -s tests -v`: 70 tests pass.
  The static asset test now requires `ledger.js`, which caught the first live
  preview failure before delivery.
- `compileall` and `git diff --check` pass.
- Local browser review at `http://127.0.0.1:18082/` opened the new record view
  without submitting a record. It showed an empty daily view, the incomplete
  record/cash-count warnings, and the cash-only expense control. No merchant
  information, operator transaction or field observation was entered.

## Limits and next admissible work

This is not receipt OCR, POS or bank integration, a settlement checker,
profit calculation, cash reconciliation, multi-user ledger, remote backup or
financial advice. It retains only operator-entered sales and cash expenses on
this computer. The consented English barber walkthrough remains a separate
experiment: obtain consent, observe the current routine, use synthetic or
operator-authorized entries only, and record comprehension/effort separately
from system correctness.
