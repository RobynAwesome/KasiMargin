---
title: "KasiMargin: a busy day does not always mean money to spend"
published: false
tags: devchallenge, hf26challenge
---

*This is a submission draft for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12). It has not been published or submitted.*

Built by Kholofelo Robyn Rababalela as a solo entry, with AI-assisted development.

## What I Built

A barber can finish a busy day with cash sales, a card payment that has not settled, rent still to pay and money that needs to stay in the business. A sales total alone does not answer the next question: **what is actually left?**

KasiMargin is a local prototype for an owner-operated South African micro-enterprise. It offers two small starting points:

- **Record today:** enter a paid cash or card sale, or cash spending. Review the recorded totals and correct a mistaken amount while retaining its original history.
- **Check my money:** enter money counted or cleared, payments still due and money to keep aside. Missing answers stay unknown and lead to a practical check. Sales and their costs are an optional, separate calculation.

The screen uses rand amounts and South African time. The arithmetic uses integer cents. A card sale appears in recorded sales; it does not silently become available cash. Records can be incomplete, and the interface says so.

The proposed paying customer is a business owner who finds a short daily record and review useful enough to return to it. That remains a product hypothesis. There is no observed purchase, revenue or willingness-to-pay result yet.

## Demo

[Download/watch the captioned synthetic demo](https://raw.githubusercontent.com/RobynAwesome/KasiMargin/refs/heads/main/docs/demo/KasiMargin-synthetic-demo.mp4). This MP4 belongs to the repository and may download in your browser. It has captions and no audio. The recording shows the standard explanation; it does not represent a new live Gemma call.

The demonstration uses made-up barber records: two R50 cash haircuts, one R50 card haircut and R20 cash spending. Sales recorded are R150, split between R100 cash and R50 card. Correct one haircut to R60: sales become R160 while the earlier record remains in the history.

This screen does not turn those sales into profit or a verified cash balance. The separate money check still needs a counted/cleared balance and the operator's review of payments due.

The technical walkthrough also checks a double submit, a saved request whose response is lost, and a retry using the same request identity. These are synthetic software tests, not an observed business day.

## Code

[KasiMargin on GitHub](https://github.com/RobynAwesome/KasiMargin)

[Decision meaning and read-only ledger reference (merged PR #8)](https://github.com/RobynAwesome/KasiMargin/pull/8). Landed on `main` at commit [`17f397f`](https://github.com/RobynAwesome/KasiMargin/commit/17f397fe687de18fde54d532b74070b36c882423).

The code is MIT licensed. Gemma's weights have their own terms; the code licence does not relicense the model or imported artwork. The emblem was supplied by the project owner. KasiLink is the owner-declared conceptual parent, and Kopano Labs research informed the governance boundaries. KasiMargin is a separate implementation; those connections do not establish customer validation or a deployed KPGS financial authority.

## How I Built It

Python and Flask provide the local service. TypeScript provides the browser interaction. SQLite retains operator-reported events and revisioned corrections on the computer. A deliberate local save is different from the unsaved money-check draft.

The AI component is Google's open-weight **Gemma**, requested locally through Ollama. The evaluated tag is `gemma4:e2b-it-q4_K_M`. It selects from permitted facts, warnings and explanation options supplied by the deterministic engine. The model does not calculate the money, write the ledger or approve a purchase. A validation gate checks the selection before the renderer supplies the actual figures. If inference fails or its output is rejected, the result identifies the deterministic fallback.

The [recorded technical evaluation](https://github.com/RobynAwesome/KasiMargin/blob/main/docs/GEMMA-TECHNICAL-EVALUATION.md) compared seven synthetic scenarios, including unpaid credit, missing receipts and a suspected duplicate payment. Across 21 captured completed calls, all 21 selections were admitted, required warnings remained present and 18 matched the baseline selection exactly. That is bounded output-validation evidence. It does not show that the model helped someone understand the answer.

The performance trade-off matters: recorded warm median latency was about five seconds; cold median was about 89 seconds, with one cold call taking nearly five minutes. The normal app timeout is 90 seconds. Interrupted evaluation segments and service recovery are disclosed in the receipt. Saving a sale does not wait for inference.

The new browser work adds protection against overlapping submits and retains a request identity for an unchanged retry after an uncertain response. That retry memory lasts within the live page. Closing or reloading during an uncertain save still requires checking the stored records before another entry.

## Why Does Open Innovation Matter?

Local model inference lets us explore financial explanations without sending the inference payload to a hosted model API. A constrained adapter also lets us compare model choices with a deterministic baseline and preserve rejected or failed attempts instead of hiding them behind a polished answer.

That choice brings costs: weights must be downloaded, memory is limited and a cold model can be slow. Local inference does not make every part of development local; cloud coding tools helped build this prototype. The application’s own Gemma path uses the local endpoint.

The experiment is deliberately critical of its AI contribution. The calculator and daily record work without Gemma. We have established technical execution; we still need evidence that the optional model changes what a business owner understands or does.

## What I Learned and What Comes Next

The first interface exposed too much of the architecture. My product review was direct: it was too technical for the person we were trying to serve. The revision starts with ordinary work and puts the implementation detail behind explanations.

A planned English walkthrough with a barber has **not happened**. There is no first-user success story to claim. After hand-in, the next experiment is a consented comparison with the barber's current routine: can they record a sale, correct a mistake and explain the difference between recorded sales and money available, without coaching? Confusion and rejection will be findings too.

This prototype does not read receipts, verify bank balances or card settlement, handle every refund/payment movement, or establish economic benefit. Its useful starting point is a small record with visible limits and a check that refuses to invent missing money.

## Prize Categories

**Best Use of Gemma** — actual local E2B execution is documented in the technical receipt. Human comprehension benefit remains unmeasured; no category eligibility or award is claimed.

<!-- Before publishing: replace the opening draft sentence with the official submission sentence; verify public video and code/version links; Robyn reviews playback and authorises publication of the final article. Robyn confirmed this is a solo KasiMargin entry on October 18. -->
