# Calendar deliverables and delivery checks

Owner instruction received October 14, 2026: the scheduled KasiMargin entries are tasks to complete and follow through continuous integration and delivery. Code with intention, retain failures, fix them and verify the resulting delivery. A schedule, local test, CI result, review, merge and deployment are separate states.

Source: two owner-supplied screenshots showing October 13 and October 14 entries in Africa/Johannesburg. The screenshots are task-description evidence, not a live Calendar read or completion receipt. Only the KasiMargin entries are transcribed here. Calendar events were not edited or marked complete.

| Scheduled task | Requirement | Current evidence | Outstanding acceptance |
|---|---|---|---|
| October 13: KasiMargin Day 1: Repo Setup, Persona & 6 Test Fixtures | Fresh repository, township micro-enterprise persona, verifiable financial problem, four core schema contracts using integer ZAR cents, six synthetic fixtures including credit sales and duplicate expenses | Independent repository; proposed spaza-shop persona and financial contract in DAY1-CONTRACT.md; six fixtures and integer-cents tests; branding/foundation merged | Three published JSON Schema files currently exist. The four-contract acceptance mapping is not explicit; document the intended four boundaries and complete any missing schema before marking this requirement complete |
| October 14: KasiMargin Day 2: Transactions & Deterministic Math Engine | Daily transaction entry; separate operating margin from verified cash headroom; UNKNOWN/HOLD for unverified cash or liabilities | Python engine, v1/v2 input validators, obligation/payment reconciliation, exact cents, unknown/HOLD tests, Flask, TypeScript, full-record JSON entry and explicit private saves | Dedicated daily transaction-entry form remains to implement and validate. Full-record editing is the current entry surface; do not claim the dedicated form exists |
| Day 2 governance wording | Calendar description references uncertainty gates | Standalone financial uncertainty gates are implemented and tested | Formal integration with the referenced governance engine is NOT_EXECUTED. Intended integration scope remains UNKNOWN; preserve source wording and route any formal admission through owner review |

The current prototype accepts operator-prepared sales/cost totals and a confirmed cash snapshot. Transaction records support anomaly checks and reconciliation; adding a record must not silently alter cash or count a past payment twice. A transaction-entry form must preserve that distinction, require explicit review and invalidate stale displayed decisions.

## Delivery sequence for each scheduled task

1. Record the task date, intended behaviour, acceptance criteria and authority in root NOW.md.
2. Map each criterion to source, fixtures or an explicit unresolved requirement. Choose bounded implementation work; preserve existing contracts and source history.
3. Implement locally and run meaningful regression tests, TypeScript checks/build and diff checks. Real-model comparisons are local technical experiments; CI must not depend on downloaded weights or merchant records.
4. Push a scoped commit to the existing review branch. The current workflow runs the TypeScript build and Python tests on Ubuntu/Windows, Python 3.10/3.14, for push and pull-request events.
5. Verify provider checks at the exact PR head. A failed check keeps delivery pending; record the failure, apply the fix and verify the new head. Do not replace a provider check with a local-pass claim.
6. Prepare the reviewable change and receipt. The owner controls landing and deployment. Update NOW.md with tested, pushed, reviewed, merged and deployed states separately.

No process can guarantee zero failures. The acceptance rule is to avoid knowingly delivering a failed or unverified change and to preserve evidence when runtime behaviour contradicts expectations. The interrupted Gemma evaluation is retained and resumed explicitly rather than presented as uninterrupted reliability.

## Next bounded implementation

Complete the four-contract mapping first, then the daily transaction-entry surface. Reuse the existing exact-cents parsing and server validator; test credit sales, duplicate references, unconfirmed cash/obligations, split-payment HOLD and save/replay without automatic persistence. Confirm both colour modes and keyboard operation. Formal governance-engine integration requires a separate source-backed scope and admission receipt; the financial engine's HOLD gate alone does not prove that integration.

The separate consented operator comparison follows technical delivery. Technical output admission, agreement with the baseline and passing CI do not establish comprehension benefit or economic value.
