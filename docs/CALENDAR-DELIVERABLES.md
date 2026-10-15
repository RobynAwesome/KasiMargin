# Calendar deliverables and delivery checks

Owner instruction received October 14, 2026: the scheduled KasiMargin entries are tasks to complete and follow through continuous integration and delivery. Code with intention, retain failures, fix them and verify the resulting delivery. A schedule, local test, CI result, review, merge and deployment are separate states.

Current source: live Google Calendar event descriptions for October 13–15, read October 15 in Africa/Johannesburg, plus live Google Tasks titles, dates and unchecked status. Full task notes were not recovered after a browser detail action failed; the complete Calendar descriptions supply the implementation requirements. Owner screenshots remain earlier evidence. Private event responses and account details stay ignored under local-data. No Calendar event or Task was edited or marked complete.

| Scheduled task | Requirement | Current evidence | Outstanding acceptance |
|---|---|---|---|
| October 13: KasiMargin Day 1: Repo Setup, Persona & 6 Test Fixtures | Fresh repository, township micro-enterprise persona, verifiable financial problem, four core schema contracts using integer ZAR cents, six synthetic fixtures including credit sales and duplicate expenses | Independent repo and proposed persona; six aggregate fixtures plus one itemized fixture; owner-admitted aggregate input, itemized input, summary and model-selection mapping; all four schema contracts validated | Local implementation validated. Exact-head CI and owner landing remain separate delivery stages; no observed customer persona claimed |
| October 14: KasiMargin Day 2: Transactions & Deterministic Math Engine | Daily transaction entry; separate operating margin from verified cash headroom; UNKNOWN/HOLD for unverified cash or liabilities | Dedicated transaction form, blank own-day path, explicit confirmations, exact-cent conversion, source/time help, invalidated stale results and synthetic add/remove/save/replay checks; core math and output gate unchanged | Local implementation validated. Operator attestations do not independently verify a bank balance or omitted debts |
| Day 2 governance wording and owner hybrid clarification | Source-backed uncertainty gates and actual runtime connection, with visible human role | Existing local KPGS context entry successfully invoked read-only; missing/invalid/unavailable states tested; context observation saved with browser receipts; deterministic financial gates remain separate | Context-entry scope only. Formal financial admission is NOT_ESTABLISHED; bank verification NOT_PERFORMED. No canonical algebra or RTC decision invented |
| October 15: KasiMargin Day 3: Local Gemma Model Evaluation & Pipeline | Select a hardware-viable E2B/E4B candidate; explanation generation plus deterministic verification with no invented figures | Existing real E2B receipt: seven scenarios, 21 captured completed comparisons, 21 admitted, zero recorded rejected/fallback, 18 exact baseline selections; interrupted segments and slow cold starts disclosed; strict selection gate unchanged | E4B remains deferred against observed resource pressure. Technical admission is not human comprehension, uninterrupted reliability or economic benefit. Today's service recovery is a separate observation |
| October 15, 09:00 Google Task: KasiMargin Day 3: Evaluate & Integrate Local Gemma Model | The Task title matches the Calendar workstream; no additional notes inferred | Same local E2B pipeline and preserved technical evidence above | Task remains unchecked; prepared delivery is not owner acceptance |
| October 15, 15:00 Google Task: Run IDE Agent Audit on NOW.md, Secret Hygiene & Repo Test Suites | Review current handoff, source privacy and test suites | Scoped private credential-pattern scan, unchanged core checks, ignored private records, updated NOW and meaningful regressions | Exact-head provider receipt follows push. Pattern scan is bounded and does not certify absence of every possible secret |

The current prototype accepts operator-prepared sales/cost totals and a confirmed cash snapshot. Transaction records support anomaly checks and reconciliation; adding a record must not silently alter cash or count a past payment twice. A transaction-entry form must preserve that distinction, require explicit review and invalidate stale displayed decisions.

## Delivery sequence for each scheduled task

1. Record the task date, intended behaviour, acceptance criteria and authority in root NOW.md.
2. Map each criterion to source, fixtures or an explicit unresolved requirement. Choose bounded implementation work; preserve existing contracts and source history.
3. Implement locally and run meaningful regression tests, TypeScript checks/build and diff checks. Real-model comparisons are local technical experiments; CI must not depend on downloaded weights or merchant records.
4. Push a scoped commit to the existing review branch. The current workflow runs the TypeScript build and Python tests on Ubuntu/Windows, Python 3.10/3.14, for push and pull-request events.
5. Verify provider checks at the exact PR head. A failed check keeps delivery pending; record the failure, apply the fix and verify the new head. Do not replace a provider check with a local-pass claim.
6. Prepare the reviewable change and receipt. The owner controls landing and deployment. Update NOW.md with tested, pushed, reviewed, merged and deployed states separately.

No process can guarantee zero failures. The acceptance rule is to avoid knowingly delivering a failed or unverified change and to preserve evidence when runtime behaviour contradicts expectations. The interrupted Gemma evaluation is retained and resumed explicitly rather than presented as uninterrupted reliability.

## Delivery and the next experiment

The [experience and architecture note](SOUTH-AFRICA-EXPERIENCE.md) records the South African research, four contracts, first-use choices and hybrid authority boundary. The [sprint board](audits/SPRINT-2026-Q4-01.md) tracks acceptance and the dated receipts retain implementation, tests and provider observations separately. Future October 16 negative-test expansion, October 17 operator work and October 18 publishing remain future scheduled work, not completed delivery today. Existing negative regressions are still required for this change.

The separate consented operator comparison follows technical delivery. Technical output admission, agreement with the baseline and passing CI do not establish comprehension benefit or economic value.

## October 15 delivery receipt

Final code implementation `9bfca31e95593f22ef478cc76adcac73ec2535c9` is pushed to [PR #4](https://github.com/RobynAwesome/KasiMargin/pull/4). All nine observed provider checks succeeded: eight push/PR matrix jobs across Ubuntu/Windows and Python 3.10/3.14, plus GitGuardian. [Exact implementation-head receipt](receipts/calendar-final-implementation-cloud-2026-10-15.json). The final documentation handoff follows this code; re-query its current head before landing. Owner review/merge, deployment and operator evidence remain separate. Scheduled Tasks remain unchecked pending acceptance.
