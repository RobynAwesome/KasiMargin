# Local foundation contract — 2026-10-13

This document describes the executable 0.2.0 prototype. `DAY1-CONTRACT.md`, `cloud-provenance.json` and `validation-receipt.json` are preserved historical artifacts. Their October 12 environment assertions are not current runtime or repository truth.

## Input versions and financial checks

`engine.calculate()` accepts the original aggregate request described by `input.schema.json`, or an itemized request with `schema_version: kasimargin-input-v2` described by `input-v2.schema.json`. Structural schemas document shape; the executable Python validator enforces integer types, timestamp ordering, freshness, completeness and reconciliation. The v2 example is `fixtures/itemized/01.json`.

V2 removes caller-provided liability and committed-spending totals. Each obligation carries an identity, supplier-scoped reference, bucket (`liability` or `committed`), total amount, amount paid by the cash cutoff, due timestamp, confirmation, linked payment transaction IDs and evidence reference. Null amounts remain unknown. The engine sums only outstanding amounts due by the horizon, including overdue obligations. The protected buffer is separate and remains operator-defined.

An obligation's paid amount must equal its linked payments. Payments must be confirmed expense payments, reference the same obligation and precede or equal the snapshot. Payment IDs cannot be allocated twice; obligation identities and references cannot overlap across buckets. Payments matching an obligation but omitted from its allocation trigger HOLD. Cash-balance evidence cannot be replaced by an invoice reference.

The current duplicate-payment gate is conservative: even fully allocated split payments with a shared reference require human resolution. It does not silently remove records. This is a known pilot limitation, not evidence of duplicate bank transactions.

`obligations_complete` and `basis_confirmed` are operator assertions, not external verification. The engine cannot detect an omitted invoice that the operator never recorded. V1 remains useful for the original synthetic scenarios, but its aggregate disjointness check remains attestation-based. Margin still uses operator-prepared attributable costs rather than inventory valuation or a full accounting ledger.

Both versions preserve timezone-aware `snapshot_at <= decision_at < horizon_end`. The fifteen-minute sample freshness allowance is experimental; no universal SME freshness policy has been validated. CLI requests carry an explicit historical or current decision time; this is not a live bank feed or automatic wall-clock verification. Synthetic fixture times stay fixed for reproducible tests. Own records require a new cash count and an appropriate decision time and horizon.

The summary includes its confirmed cash basis, nullable headroom, nullable protected deficit, independent margin, receivables delta and blocking flags. Positive headroom does not approve a specific quote. Unknown performance costs may coexist with independently confirmed cash. Credit collections are not new sales, and outstanding credit sales are not cash.

## Local model boundary

`workflow.decision()` calculates first. If a model is explicitly requested, `LocalOllama` sends only the approved summary catalogue to `127.0.0.1:11434/api/chat`, with a JSON selection schema, non-streaming response and a bounded generation request. It never invokes a model pull, uses a remote endpoint, passes raw transaction descriptions or permits model ledger writes. It reads the installed model digest before and after inference and rejects changed identity or incomplete responses. Digest metadata is Ollama's local report, not independent weight authentication.

Selections may contain only `fact_ids`, `flag_ids` and `action_ids`. Validation enforces known profit/cash figures, material deficit/credit context, all warning flags and permissible options. Human-readable warnings are rendered from trusted messages. The model can order known facts and select bounded options; it cannot replace amounts or supply free prose. Malformed JSON, duplicate keys, omitted facts/warnings and unauthorized actions are rejected. The baseline remains visible in the JSON result for comparison.

The available candidates were checked against the official [Ollama Gemma 4 catalogue](https://ollama.com/library/gemma4) on October 13. The request contract follows the official [local chat API](https://docs.ollama.com/api/chat). No real model was installed or run during this implementation. HTTP adapter tests use an explicitly synthetic service. Admission rate, language coverage, comprehension benefit, latency, hardware resource use and willingness to pay remain unmeasured.

Before choosing a model, run all fixtures with E2B and E4B on the target hardware; retain model digest, Ollama version, hardware, latency/resource observation method, rejected selections and baseline comparison in private receipts. The current narrow selection task must demonstrate value over deterministic templates. Otherwise, reopen the AI task design without relaxing the money boundary.

## Local browser and persistence

`python -m kasimargin --serve` provides the same workflow through a local browser. All browser assets are served from the checkout; no CDN or telemetry is needed. It binds to `127.0.0.1`, checks Host/Origin, accepts JSON-only bounded requests, disables caching and logs no request bodies. This is a development server, not an authenticated multi-user product.

The rand form converts decimal text through `BigInt`; blank maps to null. Full-record editing is validated on the server before applying it, rejecting duplicate keys and integers outside the browser's exact range. Edits invalidate old results. Controls are disabled during a calculation/save so an older result cannot be presented as a new input's result.

Ordinary calculations do not persist. `--save` or the browser save button creates a new private receipt file under `local-data/decisions/`. The browser save route preserves the displayed result and performs deterministic validation without calling the model again. Each saved receipt includes the full input/result, data classification, timestamp and SHA-256 over canonical JSON. The application uses exclusive file creation and never overwrites an existing receipt. The filesystem does not provide WORM storage or access-control enforcement: an owner can modify/delete local files. Replay detects byte-content changes and inconsistent calculations but does not authenticate provenance; a person able to rewrite a receipt can also recompute its checksum.

Human approval and independent bank verification are explicitly unrecorded. Merely saving a result records no approval, merchant consent, economic outcome or authority transfer. Real input records, generated responses and receipts are ignored by Git. Public fixtures, screenshots and validation receipts contain synthetic data only.

## Remaining work and acceptance boundary

The proposed first persona remains an owner-operated spaza shop planning restock, not an observed customer. Technical acceptance covers the original six scenarios plus obligation reconciliation, safe output admission, explicit persistence and reproduction. It does not establish adoption or financial reliability under real business conditions.

Next: benchmark an explicitly installed local Gemma candidate, gather consented operator comprehension evidence against the baseline, measure task time/error/supervision/compute costs and test whether the owner returns. Preserve failures as evidence. Public demo/video, DEV submission, individual eligibility and economic claims remain separate decisions.

The official [Week 2 challenge](https://dev.to/challenges/hacktoberfest-week2-2026-10-12) is Side Hustle, and requires a new project with open-source AI at its core. A tested calculation demo and adapter are preparation; actual model contribution and a truthful submission remain to be established.
