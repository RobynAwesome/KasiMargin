# KasiMargin: corrected Day 1 contract

## Scope and disposition

Actor: Codex Forge, bounded CA task renter. `I_AM_STATELESS_RENTER_NOT_LANDLORD`. No RTC seat or independent KPGS trust grant is claimed. Work is a separate, reversible synthetic experiment under the user's KasiMargin request. It does not mutate Introduction-to-MCP, activate its agents, execute financial transactions or publish a submission.

Hypothesis: Can an open-weight assistant help a township micro-enterprise owner distinguish profit from cash and evaluate a reinvestment decision without manufacturing certainty?

Proposed first persona: an owner-operated spaza shop planning tomorrow's restock. This is a test persona, not a verified customer. Public wording must avoid treating township owners as one financial or linguistic stereotype.

Mission fit: better records and clearer decisions may support a livelihood pathway from survival cashflow toward deliberate reinvestment. A synthetic fixture is not evidence of adoption, revenue improvement, job creation or unemployment reduction. No current unemployment statistic is inferred from historical doctrine.

## Financial contract

All monetary inputs use non-negative integer ZAR cents. Null means unknown. Signed outputs such as operating margin can be negative. Booleans, decimal floats and numeric strings are rejected as money by the executable validator.

Performance and liquidity have separate evidence gates:

`estimated_operating_margin = recorded_sales - attributable_costs`

Attributable costs refer to the same performance period, including relevant sold-stock costs and operating-cost allocations. Stock purchased is not automatically cost of goods sold. Outstanding credit sales can be recorded sales; collecting an earlier debt is not new sales. This prototype accepts operator-prepared aggregate inputs, not a full accounting ledger or inventory valuation system.

`cash_headroom = max(0, verified_cash - due_unpaid_liabilities - minimum_buffer - other_committed_spend)`

`protected_cash_deficit = max(0, -(verified_cash - due_unpaid_liabilities - minimum_buffer - other_committed_spend))`

Cash refers to counted cash and cleared, accessible balances at `snapshot_at`. Credit sales and pending settlement are excluded. Operator confirmation and evidence references support an input assertion; the system does not independently authenticate a bank balance or receipt. The product must describe the output as conditional headroom, not guaranteed safe spending.

`due_liabilities_cents` covers outstanding obligations payable by `horizon_end`. `committed_spend_cents` covers other planned spending within that horizon, excluding those same liabilities. The buffer is an owner-defined reserve, not a value invented by a model. All three amounts may be null. Missing fields are invalid rather than defaulted to zero. `basis_confirmed` attests that the balance is reconciled, liabilities are complete for the horizon, and the two obligation buckets do not overlap. Day 2 should replace the aggregate attestation with obligation-level IDs and explicit allocation checks.

Past payments are already reflected in the cash snapshot. The engine must not subtract them again. Receivables are diagnostic ledger deltas, not a complete customer-balance ledger or available cash.

Low operating margin does not mathematically constrain cash headroom. A business may have prior cash even after a loss, or profit with no available cash. Fixture 02 combines low margin and constrained cash; an additional test demonstrates low margin with positive headroom.

Unknown margin may coexist with independently confirmed cash. Missing receipts affecting cash or obligations belong in blocking `unresolved_flags`. Incomplete performance costs alone make margin unknown. This distinction avoids falsely declaring all financial facts known or all financial facts unavailable together.

## Input and output boundaries

`docs/input.schema.json` records the structural input contract. Python `calculate()` additionally checks exact keys, integer types, timezone-aware ordering, freshness, evidence presence and transaction anomalies. JSON Schema format validation alone is not the semantic gate.

Cash timestamps must satisfy `snapshot_at <= decision_at < horizon_end`. The fixture freshness allowance is fifteen minutes for the experiment, not an empirically validated universal SME policy. Post-snapshot transactions, stale snapshots, unconfirmed entries, possible duplicate payment references, unknown components and unresolved cash flags block headroom.

Supplier payment references should be supplier-scoped invoice/payment identifiers. Repeated references are suspected duplicates; legitimate split payments need human review. The engine does not silently deduplicate, count money twice, or infer liability resolution.

`DailySummary` contains margin, nullable headroom, nullable protected-cash deficit, recorded receivables delta, CALCULATED/HOLD status, flags, blocking flags, horizon and input evidence references. CALCULATED means a calculation passed the stated input checks. It does not mean field-verified, PKA-admitted or economically proven.

## Model contract

Candidates: `gemma4:e2b` and `gemma4:e4b` on local Ollama. Official Ollama and Google documentation were checked on October 12. Availability does not prove device fit. No Ollama executable was found in this environment; neither model was downloaded or run.

Day 3 should give Gemma the validated summary and approved catalogue, require the JSON selection schema, parse strict JSON, reject unknown IDs or omitted flags, then render trusted templates. Do not pass raw merchant notes or receipt text into this selection step. No prompt is an enforcement guarantee.

Model selection contains only `fact_ids`, `flag_ids`, `action_ids`. Unsupported keys, generated prose, prices, debt estimates, spending commands and risk scores are rejected. The model chooses which permitted facts and options to surface; the renderer supplies amounts. HOLD allows only record confirmation. Zero headroom allows only cash protection. Positive headroom permits preserving liquidity or checking an owner-supplied quote; it does not authorize purchasing.

This restriction narrows AI's contribution. The field experiment must compare actual Gemma selections against the deterministic-template baseline and assess whether they improve understanding. If there is no measurable benefit, do not claim the model is essential merely because a model call exists. Wider free-form explanations require a separate semantic validation design; number matching does not prove grounded advice.

Record model digest, Ollama version, hardware/RAM, load time, repeated inference latency, resource observation method, all six fixture outcomes, malformed outputs, admission rate and comprehension result. Do not call E2B/E4B winners until measured. Reject malformed output and display a labelled deterministic fallback, with the failure receipted.

## CCP / PKA / KC / Cassey boundaries

Cloud GSMB inspected at `0e5d23cab3c2621d3678a9cdddb0ef4f299de0d8`; exact paths and blob hashes are in `cloud-provenance.json`. Root NOW still begins with October 7 observations and older master/status claims. Those entries are dated history, not fresh provider-status evidence. This task did not audit live PR/security state.

Local source `C:\Users\rkhol\OneDrive\Documents\Anthropic\Introduction to MCP\Schematics` is inaccessible from this workspace. Google Drive was not read. No ecosystem parity or private-source absence is inferred.

KC lane: preserve mission, doctrine provenance, human choice, bounded authority and reconstructable receipts. KC is not an arithmetic executor. KC runtime activation was NOT_EXECUTED.

Cassey lane: propose, inspect fixtures, teach the profit/cash distinction and bring evidence for review. A student/reviewer proposal is not teacher validation or graduation. Cassey runtime activation and teacher review were NOT_EXECUTED. Naming these lanes is not an agent activation receipt or a fake external ACK.

PKA mapping: X = changeable cash, liabilities, record quality, hardware and measured user outcomes. Y = versioned integer arithmetic, provenance, uncertainty preservation, explicit horizon, human choice and fail-closed spending boundaries. MAYBE/HOLD remains admissible when evidence is missing.

KPEFS interpretation for this experiment: primary V4_DIASPORA for locally constrained livelihood and sovereignty; secondary V3_HOMO_SAPIENS for comprehension and human-choice testing. This is a source-grounded routing proposal, not execution of the KPEFS runtime.

The source Economic Consequence Validation skill distinguishes `CCP_ACCEPTED != PKA_ADMITTED`, `CAPABILITY != ECONOMIC_VALUE` and `PKA_PROPOSE != DOWNSTREAM_EXECUTION_AUTHORITY`. Spark's acceptance is peer discussion. No canonical CCP receipt is present here, and no formal PKA engine was invoked. Disposition: synthetic calculation evidence only; CCP/PKA/economic promotion remains UNPROVEN. Do not invent a canonical receipt to pass the gate.

## Eligibility and dates

Official Week 2 rules set the entry period to October 12 at 12:00 PM PDT through October 18 at 11:59 PM PDT: October 12 at 21:00 SAST through October 19 at 08:59 SAST. The earlier Oct 18 evening milestone is an internal target, not the official cutoff. Retain actual repository creation and commit times; the experiment began after opening on October 12, not before opening and not backdated to October 13.

Theme: Side Hustle — a product a real person or business would plausibly pay for. The prior pasted Touch Grass material belongs to Week 1. Fresh project and repository work must occur in the challenge window; meaningful reuse needs attribution. Post-deadline commits must be noted in README. Maximum four team members, one submission per team, DEV handles listed for collaborators. English is required for prize judging. Use the submission template with #devchallenge and #hf26challenge; link code and either a deployment or video demo. Explain why open innovation matters and name any genuinely integrated prize category.

South Africa is not on the published excluded-jurisdiction list. Individual eligibility still depends on age/majority, active DEV membership, account standing, applicable restrictions and team eligibility. This pack does not certify those personal facts or submit/accept terms for anyone.

## Field validation before economic claims

With a willing participant and consent, compare the current manual process against the template baseline and then actual Gemma inference. Ask the owner to identify profit versus available cash, explain why credit sales cannot be spent yet, spot missing obligations, and assess an owner-supplied restock quote within the horizon. Capture errors and correction time as well as successful comprehension.

Measure time per decision, completion/error rate, supervision effort, compute/setup cost, and whether the owner returns to use it. Record willingness to pay separately from an actual purchase or payment. Define the period, sample, failure cost and evidence references before attempting the economic-consequence gate; do not fill unmeasured task-fit/reliability/adoption scores with optimism. No field contact or payment was initiated in this task.

## Official references

- https://dev.to/challenges/hacktoberfest-week2-2026-10-12
- https://dev.to/page/hacktoberfest-week2-2026-10-12-contest-rules
- https://dev.to/page/official-hackathon-rules
- https://ollama.com/library/gemma4
- https://ai.google.dev/gemma/docs

## Next admissible work

Import this fresh scaffold into a new repository; record real timestamps and lineage. Review the input/obligation contract before Day 2 transaction entry and persistence. On Day 3 connect and benchmark actual Gemma. Day 4 exercises negative outputs and balance reconciliation; Day 5 gathers consented user evidence; Day 6 produces the truthful demo and DEV article. The scheduled milestones quoted from Spark were not independently checked or modified here.
