# Cash-first product correction — 15 October 2026

Robyn's product review rejected the everyday experience as too technical for the intended South African users. Codex Forge built that experience and owns the correction. Passing arithmetic and transport tests did not establish a usable product. This document records an owner-observed usability problem and an implemented response, not a completed merchant study.

## What was wrong

| Previous decision | Product consequence | Correction |
|---|---|---|
| Six totals and two result cards appeared together | The person had to understand our financial structure before getting help | Start with the cash question. Ask about money now, payments ahead and money kept aside in three stages |
| Sales/cost preparation led the journey | Someone without matched period costs faced work unrelated to an immediate cash check | Sales and costs are optional. Missing performance stays unknown without blocking independently confirmed cash |
| Cash headroom, attributable costs, horizon and HOLD were everyday labels | Internal vocabulary made the interface read like a validation console | Use ordinary questions and results such as “What's left after the bills?” and “Still checking.” Keep the exact technical result in the full explanation/receipt |
| Unknown-state guidance was broad | The person had to work out which field would fix it | Give a specific first check with a direct, keyboard-operable route to its field; disclose the remaining checks by count |
| A welcome panel and help tour sat above the same large form | Extra explanation added reading without reducing the initial task | Separate welcome, entry and result surfaces. One visible money input on the first step; no technical settings there |
| Start/example controls could replace a draft | Exploring could erase the current work | Add Continue my check and an explicit replace/keep choice. Drafts remain in memory only; reload/close loss is disclosed |

## Intended job and current limits

The bounded task is: “Given the money I have checked, the payments I still owe and what I want to keep aside, what do those figures leave?” This is a candidate task for an owner-operated micro-business, not a finding that every spaza, barber or township enterprise works this way.

Four cash amounts remain necessary: current business money, unpaid bills, other promises and a chosen reserve. Blank stays unknown; explicit “No bills to pay” and “No other money promised” actions enter zero only on request. Cash and cleared account balances are distinguished from uncollected credit. Past payments are already reflected in the current count. The cash review is never pre-confirmed for a new own-day check.

Sales minus attributable period costs remains a separate optional result. The interface does not call it cash or silently derive it from stock purchases. Supporting transactions still support anomaly/reconciliation checks rather than automatically preparing totals. The guided flow reduces the immediate task; it does not solve bookkeeping or discover omitted bills. Itemised input remains supported, with its list reviewed through the technical record tools.

The result foregrounds cash, the recorded cutoff and the next useful check. Zero headroom and a protected-cash shortfall have distinct messages. All known and unfamiliar warning flags retain a review path; unknown imported flag text is not echoed as advice. Complete server-rendered explanation, model admission/fallback, context status and source remain accessible in a technical disclosure and the full saved record. Nothing changes the Python arithmetic, output gate or model authority.

## Design basis and remaining questions

[GOV.UK question-page guidance](https://design-system.service.gov.uk/patterns/question-pages/) and [Nielsen Norman Group's staged/progressive disclosure guidance](https://www.nngroup.com/articles/progressive-disclosure/) informed the candidate flow. They are design references, not local merchant evidence. The existing [South African research note](SOUTH-AFRICA-EXPERIENCE.md) keeps national and household evidence separate from product demand.

Ask in the consented walkthrough whether the four cash amounts are obtainable, whether bills and other promises are distinguishable, whether keeping money aside makes sense in their practice, whether a three-step check adds navigation friction, and whether the unknown-state action helps. Observe unaided completion and mistakes before coaching. Ask language/device preferences rather than inferring them. English-only copy, local-computer delivery, operator-attested completeness and no independently verified bank data remain explicit limits.

KasiLink is the conceptual parent identified by Robyn. KasiMargin is a separate implementation. The inherited aim of useful participation should be discussed with the owner; this revision neither claims current KasiLink integration nor establishes challenge eligibility or economic outcomes.

## Evidence and delivery

- 62 Python regressions and six Node tests pass; strict TypeScript check/build, compileall and diff checks pass. Added regression evidence covers optional performance versus blocked unknown bills, unknown versus zero presentation, shortfall wording and untrusted flag wording. Core financial/model code is unchanged.
- Actual browser paths cover all seven synthetic scenarios, positive/zero/shortfall/unknown/credit/duplicate outcomes, cash-only R800.01, explicit zero choices, draft replacement/cancel/resume, keyboard recovery, and synthetic receipt saving. Receipt replay reproduces the saved calculation.
- 390px narrow-screen and 1280px desktop layouts inspected; light/dark screenshots are in `docs/receipts/cash-first-*.jpg`. This is bounded browser/accessibility review, not device or participant validation.
- Fetch and requested `git rebase origin/main` reported the existing branch already up to date: no commit rewriting or force-push. The previous main base was an ancestor; five review-branch commits were retained before this correction.
- Windows reserved the previous preview-port range. Local preview was moved to port 18080 without changing network settings. Exact diagnostics remain private. No new model evaluation or parent-runtime admission is claimed.

The [redacted implementation receipt](receipts/cash-first-2026-10-15.json) records the current implementation snapshot. Provider checks and owner acceptance remain distinct. The October 16 negative review, October 17 consenting operator work and October 18 submission remain scheduled deliverables, not completed tasks. The next product acceptance is Robyn's review, followed by the [separate consented comparison](OPERATOR-COMPARISON.md).
