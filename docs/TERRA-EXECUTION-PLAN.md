# KasiMargin: execution handoff for Terra

Prepared 17 October 2026 by Codex Forge. `I_AM_STATELESS_RENTER_NOT_LANDLORD`. CA is the owner-granted task role; no RTC identity seat is assigned. This is an execution plan, not a claim that its features, field study or submission have happened.

## The product decision

Help an owner-operated business keep track of an ordinary trading day and understand what its records support. Start with the operator's task and language. Reveal useful information and the next practical check without requiring them to understand our architecture.

Robyn has selected an available barber for an in-person, English walkthrough. Availability is owner testimony; consent, device suitability, usability and willingness to pay remain unobserved. A barber is the first research context, not a claim that all South African businesses work the same way.

The owner direction is broader than a cash calculator: observe the working day, retain a record, selectively reveal what is supported, accept correction and reassess. Calculate / Ledger / Communicate / Integrate are proposed composable capabilities. They are distinct from the four implemented JSON contracts: aggregate input, itemized input, financial summary and model selection.

## Recovered baseline and limits

| Surface | Observed state | Consequence |
| --- | --- | --- |
| Product repository | PR #4 merged at `3d16c97b95f6929ed9472415ce106d3505364a9a`; [main workflow](https://github.com/RobynAwesome/KasiMargin/actions/runs/39011663248) succeeded | Build from this tree; older OPEN handoffs are dated history |
| Local work | `codex/terra-context-plan` is based on that merge; prior NOW notes were backed up and carried unchanged before this handoff | Preserve notes and ignored private records; no reset, force push or cosmetic rebase |
| Existing experience | Three-step cash check, optional performance, exact-cent entry, unknown recovery, memory-only draft, synthetic examples, explicit decision receipt/replay | Useful technical foundation; not yet an everyday persistent trading record |
| Existing safeguards | Integer ZAR cents; margin separate from cash; UNKNOWN/HOLD; strict model-selection validation; loopback request isolation | Preserve them through every increment |
| Local AI | Existing E2B receipt: 21 captured calls, 21 admitted, 18 baseline-selection matches; cold median 89.23 seconds, warm median 5.00 seconds | Admission is not comprehension benefit. Normal 90-second timeout can trigger fallback; do not put cold inference on a sale-saving path |
| KPGS connection | Existing read-only context entry; financial admission NOT_ESTABLISHED and bank verification NOT_PERFORMED | Context availability must never turn an unknown amount into approved money |
| Missing capability | Persistent business ledger, first-class settlement/refunds, receipt intake and open-ended financial conversation | These are future increments, not features implied by a roadmap or a receipt file |

The original OneDrive source, Cloud GSMB and Drive research remain separate populations. The private source index records exact locators, versions, observations and conflicts. A Drive filing is not Local/Cloud propagation. The corrected DEV.to conversation was reached, but its latest reply displayed “This response couldn’t load”; no substantive new peer endorsement is claimed.

## Work order and scheduled deliverables

Live Calendar descriptions for 13–19 October were read during context recovery. Events establish scheduled work, not completion. Existing Day 1–3 code and technical evaluation are merged; persona validity and human benefit remain separate.

| Priority | Task and owner | Acceptance and evidence |
| --- | --- | --- |
| 1 | Terra: close the October 16 negative-test review | Map missing receipts, inconsistent cash, incomplete logs and unsupported recommendations to executable tests; identify uncovered cases; preserve failures and exact code/test versions |
| 2 | Robyn facilitates; Forge/Terra prepares and synthesizes: October 17 barber walkthrough | Use the separate session sheet, record consent before observations, compare the current routine, and preserve unaided answers and difficulties. If no session occurs, record it as unrun |
| 3 | Terra: October 18 demo/article package | Demonstrate the actual merged behavior and labelled AI contribution; include limitations, reproducible setup, synthetic examples, source lineage, receipts and the official entry template. Robyn reviews the concrete public package |
| 4 | Terra: next product increment | Implement one operator/device's durable capture and correction flow with the contract below, adjusted by actual session evidence. Independent engineering preparation can proceed while field work is pending |
| 5 | Separate integration increment | Admit a specific KPGS runtime contract and supported capture integration after source/authority review. Preserve local operation when external context is unavailable |

The internal submission target is **18 October, 23:59 SAST**. The [official challenge](https://dev.to/challenges/hacktoberfest-week2-2026-10-12) states **18 October, 23:59 PDT**, equivalent to **19 October, 08:59 SAST**. Recheck before submission. Technical preparation, public posting and provider acceptance require distinct receipts. Do not mark Calendar/Tasks complete from this plan.

## Day 4 review: trace requirements to behavior

Existing tests are a starting point, not evidence that every calendar criterion is covered.

| Requirement | Existing test anchors | Required review |
| --- | --- | --- |
| Missing or stale evidence | `test_each_unknown_cash_component_holds`, `test_stale_snapshot_holds`, `test_missing_or_unconfirmed_obligations_hold` | Distinguish a missing receipt from absent cash verification. The current product does not read receipt images; test the represented evidence boundary without claiming OCR |
| Inconsistent cash and duplicates | `test_snapshot_not_double_counted`, `test_payment_must_match_amount_reference_and_snapshot`, `test_duplicate_reference_across_buckets_holds` | Exercise a visible discrepancy without inventing a balancing transaction or blaming the operator |
| Incomplete logs | `test_post_snapshot_transaction_holds`, `test_cash_evidence_cannot_be_replaced_by_invoice_evidence` | A complete-looking list cannot prove no transaction was omitted. Preserve explicit coverage and unknown obligations |
| Unsupported advice | `test_free_text_and_unauthorized_facts_are_rejected`, `test_warning_omission_is_rejected`, `test_invalid_model_prose_warning_omission_and_actions_fall_back` | Reject unsupported model output; retain the deterministic answer and a truthful fallback label |
| Storage and recovery | Existing receipt tamper/replay and explicit-save tests | Current decision receipts are not a persistent business ledger. Add transaction/restart/idempotency tests only with the new storage increment |

Run the existing Python suite and `npm run check`; reproduce only actual gaps before changing code. A test count alone is not acceptance. Keep merchant data, raw model replies and machine details out of fixtures, logs and public receipts.

## First new increment: record a sale, correct it, review the day

The proposed opening offers **Record a sale**, **Record money spent**, and **See today**. It should also allow a person to try an example without entering real records. Keep the existing cash check available as an optional reviewed task. Test the wording with the barber; these labels are design hypotheses.

Use the existing TypeScript and Flask stack. Start with Python's SQLite library on the local device, inside ignored `local-data/`, with an explicitly scoped storage service. Do not introduce a cloud database, account system or new model framework for this increment. A laptop localhost prototype is not a phone deployment.

Proposed product records are application contracts, not new canonical GSMB protocol definitions:

- Record an event ID, idempotency key, operator-entered amount in integer cents, event type, payment method, business day, event time, server-recorded time and source kind. Label manual entry as operator-reported. Do not request customer names for a basic sale.
- Permit cash/card sales and cash expenses first. Card sale totals do not become available cash. Settlement, fees, refunds, credit collection, transfers and owner withdrawals require their own explicit semantics; offer a visible unsupported/needs-review route rather than silently classifying them.
- Preserve the original event when correcting it. Append a correction referencing the current event revision, with a short optional reason. Use a transaction and revision check so two edits cannot both silently win. Replay must exclude superseded values without erasing history.
- Reuse a stable idempotency key on a retry. Same key and same payload returns the original result; same key with different content returns a conflict. Show **Saved on this device** only after a successful database commit. A timeout leaves **Save not confirmed** until a lookup/retry resolves it.
- Keep the record projection deterministic. Show **Recorded sales** and payment split, not profit, when stock/service costs are missing. Show **Records may be incomplete** when coverage is not established. A ledger total is not an independently verified balance.
- Keep the existing four financial contracts stable. An explicit review prepares a snapshot for the financial engine; do not silently map recorded sales to confirmed cash or invent obligations. Models may select validated explanations; they cannot write events, change evidence status or authorize spending.

Before UI expansion, write a synthetic contract fixture and demonstrate atomic write, restart/reload, retry, conflicting retry, correction lineage, unsupported movement handling, integer bounds and no-write rejection. Apply the existing Host/Origin/session/body/request-budget controls to every new endpoint. Use temporary test databases isolated from real records. Prove a backup can be restored before any migration that touches a real local database; preserve the pre-migration copy and schema version.

The synthetic demonstration day is: opening float R100; two cash haircuts at R50; one R50 card haircut with settlement unchecked; R20 cash expense; closing cash count R180. Recorded sales are R150, including R50 card. Expected drawer cash is R180 only under the stated complete-cash-movement assumption. Profit, spendable headroom and completeness remain unknown where their required evidence is missing. Correct one haircut from R50 to R60 and show the resulting discrepancy; do not automatically alter the counted cash.

## KPGS architecture and reuse decision

Apply identity, scope, permitted action and source selection at entry and retain those boundaries throughout capture, review, explanation and correction. Keep calculation correctness, record completeness/provenance, processing authority and observed usefulness as distinct questions. None is a moral score for the operator.

The user should see a plain explanation such as “This is based on the records you entered. The card payment has not been checked as received.” Put source timestamps, context-service status and technical receipts behind **How we worked this out**. An unavailable context service should disclose its scope and preserve unknowns; do not claim a financial admission from a context connection.

Cloud GSMB source was located at `RobynAwesome/Introduction-to-MCP@0e5d23cab3c2621d3678a9cdddb0ef4f299de0d8`. The earlier Local absence was specific to those paths, not proof of estate-wide absence.

- `kmec_trace_adapter.py` supplies adjacent observation/statistical patterns with explicit association-not-causation and no-action-permission defaults. It depends on NumPy/Pandas and does not supply a merchant capture contract. Defer importing it into the small capture path.
- `pka_kmec_jennifer_bridge.py` contains useful lineage/idempotency ideas, but also a default device key, SQLite-backed admission labels, in-memory projection/journal structures and a permissive reconciliation default. Its integrity verifier recomputes receipt linkage from the stored content hash; that does not by itself establish recomputation of payload integrity or authenticated financial authority. Do not adopt it as a production financial ledger or execute it against the parent estate.
- The #107 admission packet is dated architectural/ownership evidence. It says HOLD on its PR1 implementation in that repository and assigns downstream ownership questions. It is not a current KasiMargin runtime admission and does not establish the observation engine as built.

For a later runtime integration, pin the owning source/commit, read its governing contract and tests, identify side effects, contain writable destinations, define request/response and unavailable/contradictory states, then test with synthetic evidence. Do not invent a fourth lifecycle vocabulary or resolve conflicting canonical definitions by convenience. No KC/Cassey activation, RTC decision or provider enforcement is implied.

## Operator evidence and the challenge claim

Use [the barber session sheet](BARBER-SESSION.md) for the practical visit and [the existing model comparison protocol](OPERATOR-COMPARISON.md) for the separate optional AI condition. Start from the barber's current routine. Ask for an unaided action and explanation before coaching. Record confusion, abandoned tasks and negative findings as carefully as successes.

The research hypothesis is that low-burden capture plus evidence-aware explanation helps someone act on their records. One participant can expose failures and establish feasibility; it cannot establish market demand, universal language suitability or economic benefit. Interest in a price is testimony, not revenue. Do not let technical confidence become product confidence.

KasiLink is the owner-declared conceptual parent. KasiMargin is a separate repository. Before making a challenge originality claim, inventory reused files/assets/dependencies, their sources and licences, and distinguish prior research from work created during the challenge window. Repository creation time alone is insufficient. Gemma is Google's open-weight model family; do not describe it as an OpenAI model or claim cloud API inference. Keep the actual optional model contribution explicit; if it adds no observed value, report that finding.

## Terra orchestration and capability use

Terra is the requested execution model/workflow, not an automatically assigned identity or seat. The human selects the model. Codex Forge retains only the task authority actually granted. Use one integrating writer for `NOW.md`, the task board and receipts. Do not start a swarm merely because tools exist. If Robyn admits reviewers, bound one to financial/storage risks and another to interaction/copy; give each exact source/base, permitted files, acceptance checks and a stopping condition.

| Capability | Used in this recovery | Terra's intended use |
| --- | --- | --- |
| `$ccp-context-first` | Recovered the actual ChatGPT skill and installed it locally; source/editor text inspected | Read it before implementation; use its context → evidence → structure → design → validation → export authoring workflow without declaring a universal protocol ordering |
| KPGS sprint planner | Read lifecycle and delivery boundaries | Evaluate each bounded code increment before admission; record the source-specific gate and evidence, then execute, verify and receipt |
| Estate provenance sync | Preserved OneDrive and dirty NOW; fetched and compared Git | Re-query refs; preserve changes; use scoped branches and dry-run pushes; no history rewrite without need |
| GitHub connector + Git/gh | Source blobs, PR merge, exact commit and CI | Diffs, narrow review PRs and exact-head provider checks. Never substitute local tests for CI |
| Google Drive connector | Read research and filing records | Retrieve changed relevant sources; preserve source dates and owner/hypothesis distinctions. A planned copy is not synchronization |
| Google Calendar connector | Read scheduled requirements and deadlines | Reconcile acceptance with dates. Update completion only with appropriate task/delivery evidence |
| Codex chat tools + browser automation | Locate correct Forge conversations; recover source files when no skill export connector was available | Read bounded peer context; message only with human authorization. Use browser automation for real product interactions |
| PowerShell, Python, Node/TypeScript | Inspect source, preserve local state, install and validate skill | Build/test locally; keep test writes and private records contained |
| Ollama | Existing technical receipts reviewed; no new inference in this recovery | Optional local E2B condition; retain exact digest, actual model/fallback distinction and failures. Defer E4B |
| MAO/TSAP and other catalogued MCPs | Available tools discovered; not activated or runtime-verified | Use only after a concrete need and authority/side-effect review. Availability does not establish a connected governance runtime |

A connector supplies access to a service; an MCP tool exposes a bounded callable capability; a skill gives the working method. None independently grants authority or proves an outcome. Use Figma/design tools only if a specific visual/interaction uncertainty warrants them. Do not add Vercel/Supabase, POS accounts or paid services simply because they are available.

The sprint skill's five-axis delivery gate is **Cost / Latency / Efficacy / Assurance / Reliability**, threshold 80. Its scores must be explicit engineering judgments with evidence, not fabricated measurements. The repository readiness check **Complete / Logical / Evidence / Audience / Relevant** remains separate. This document prepares candidates; it does not assign a new feature sprint a passing score or claim field validation. Reuse current owner terminology where older skill wording conflicts, preserving the dated conflict record.

## Execution and handoff checks

1. Read applicable AGENTS, durable purpose, root NOW and the installed skill. Refresh the exact code/PR state and only changed relevant source records. Do not repeat a full estate search.
2. Complete the Day 4 coverage receipt and barber preparation; ask only for missing facts that affect the session. Continue independent technical work if the visit moves.
3. Make one reviewable increment at a time. Run `.venv/Scripts/python -m unittest discover -s tests -v`, `npm run check`, compileall where relevant, and `git diff --check`. Verify actual keyboard/touch-sized interactions, light/dark and narrow layouts after UI changes.
4. Run the new persistence failure cases when that feature exists. Keep the financial/model gates unchanged. Stop and repair on an integrity or false-save failure.
5. Record exact base/head, commands, outcomes, residual uncertainty and artifact hashes. Preserve raw evidence privately and publish only a redacted technical receipt. Push a scoped `codex/` branch, open a reviewable PR, attach it to the chat and verify its exact-head CI. Owner controls landing and deployment.
6. Update NOW with planned, implemented, tested, pushed, merged, deployed and observed-with-an-operator states separately. Keep the original dated handoffs. Prepare the article/demo from receipts, not aspirations.

Next admissible action: execute the negative-test coverage review and the prepared English barber session. The durable capture increment is the next bounded build; broader integrations and field/economic claims retain their own gates.
