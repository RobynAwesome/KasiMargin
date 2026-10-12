# KasiMargin — From sales to growth

A local financial decision prototype for an owner-operated township micro-enterprise. It separates **estimated operating margin** from **conditional cash headroom**, preserves unknowns, and lets an optional local Gemma model select approved explanations without doing arithmetic or authorizing spending.

Working hypothesis: can an open-weight assistant help an operator understand the daily financial position and evaluate a potential restock decision without manufacturing financial certainty?

## Run locally

Python 3.10+; no third-party Python runtime dependency. In PowerShell:

```powershell
cd C:\Users\rkhol\KasiMargin
python -m unittest discover -s tests -v
python -m kasimargin --serve
```

Open **http://127.0.0.1:8765**. The browser demo offers seven synthetic scenarios, editable rand inputs, full-record review, plain-language warnings, optional local inference, and explicit receipt saving. It has no external fonts, scripts, analytics or bank connection. It binds only to loopback and is a development demo; it is not a public production server.

The six original scenarios cover a profitable cash position, low margin, a protected-cash deficit, missing records, uncollected credit sales and a suspected duplicate supplier payment. A seventh uses itemized obligations and a reconciled partial payment. Loading a scenario labels it synthetic; only choose operator-attested records after replacing the example with your own complete records and appropriate timestamps.

## CLI and reproducible receipts

```powershell
python -m kasimargin fixtures/01.json
python -m kasimargin fixtures/04.json
python -m kasimargin fixtures/itemized/01.json --save
python -m kasimargin --verify local-data/decisions/decision-REPLACE_WITH_ACTUAL_ID.json
```

The CLI accepts either a fixture wrapper or a raw request JSON. Saving a raw request requires `--data-class OPERATOR_ATTESTED` or `--data-class SYNTHETIC`. Browser saves preserve the exact displayed result; they do not rerun the model. Receipts contain inputs, summary, permitted selection, baseline comparison, inference metadata and a content checksum. Replay checks the deterministic calculation and rendered explanation without calling a model. This proves reproducibility and detects content changes; it does **not** authenticate the author, independently verify a bank balance or certify human approval.

Real business records and generated decision receipts belong in ignored `local-data/`. Ordinary calculation does not save records. Do not add merchant records, receipt images, personal identifiers or model responses to Git.

## Financial boundary

All calculation amounts use exact integer ZAR cents. Decimal floats, booleans, numeric strings and negative money inputs are rejected; signed calculated margins may be negative. The browser converts rand text through integer arithmetic and rejects values outside its exact number range. The CLI retains Python integer precision.

```text
estimated operating margin = recorded sales - attributable costs
conditional cash headroom = max(0, confirmed cash - unpaid due liabilities
                                  - separately committed spending - protected buffer)
```

Margin and cash use separate evidence gates. Uncollected credit sales can contribute to recorded margin, but are excluded from available cash. Paid expenses and collected sales are already reflected in the cash snapshot and are never added or deducted again.

V1 accepts operator-prepared aggregate totals. V2 derives obligation totals from itemized records, matches paid amounts to confirmed payment transactions, excludes obligations beyond the horizon, and flags overlapping references, reused payment allocations, missing evidence and inconsistent amounts. A complete obligation list remains an operator assertion; the application cannot discover omitted debts. Legitimate split payments sharing one reference currently require human resolution under the conservative duplicate gate.

Missing cash, a missing buffer, incomplete obligations, stale snapshots or unresolved cash records return **null headroom and HOLD**. Unknown is never silently replaced by zero. Positive headroom is conditional on recorded inputs and horizon, not a guarantee that any purchase is safe. See [the current implementation contract](docs/LOCAL-FOUNDATION.md).

## Optional open-weight AI

The adapter uses [Ollama's local chat API](https://docs.ollama.com/api/chat). Evaluation candidates are [Gemma 4 E2B and E4B](https://ollama.com/library/gemma4). It connects only to `127.0.0.1:11434`, never downloads weights automatically, and rejects cloud model tags. Once Ollama and a candidate model are installed, request it explicitly:

```powershell
python -m kasimargin fixtures/05.json --model gemma4:e2b
```

The model sees the deterministic summary catalogue, not raw transaction descriptions. It returns only approved fact, warning and action IDs. Programmatic validation requires known profit/cash figures, material risks and all warnings. A trusted renderer supplies every monetary value. Unsupported prose, omitted warnings, invented actions, incomplete responses and model-digest drift are rejected. An unavailable service or rejected output displays a labelled deterministic fallback.

**Current evidence:** the adapter has been tested against a synthetic local HTTP service. A live connection attempt found no available Ollama service on this machine. No Gemma weights were downloaded or run. Model latency, device fit, language quality and added operator value remain unmeasured. The restricted selection task may offer little benefit over the baseline; actual inference and a consented comparison must establish whether it is useful. An adapter alone is not proof that AI is essential.

## Project origin and challenge

This repository was created at **2026-10-12 22:07:26 UTC / 2026-10-13 00:07:26 SAST**. Its first Cloud commit is `5897456485b15474e8cbbf1c8b13f68a04533788` (the owner's README). The owner-supplied Day 1 scaffold has an October 12 receipt and has been imported with its historical records preserved. We do not backdate code or replace historical claims with later outcomes.

KasiMargin draws conceptual governance inspiration from Kopano Labs and Kholofelo Robyn Rababalela's research. This is a separate greenfield implementation, not a migration of the GSMB runtime or private source corpus. [Historical Cloud provenance](docs/cloud-provenance.json), [the original Day 1 contract](docs/DAY1-CONTRACT.md) and [the original validation receipt](docs/validation-receipt.json) retain their dated scope. Their statements about repository creation or unavailable local paths describe that earlier session; current state lives in [NOW.md](NOW.md).

Target: [Hacktoberfest 2026 Week 2 — Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12). The official deadline is October 18 at 11:59 PM PDT, equivalent to **October 19 at 08:59 SAST**. Individual eligibility, genuine use of an open model, a consented first-user experiment, demo/video and DEV submission remain pending. No economic value, customer payment, employment outcome, teacher review, formal ratification or production deployment is claimed.

## Development and license

Read [AGENTS.md](AGENTS.md), then [NOW.md](NOW.md). Run the unittest suite and `git diff --check`; GitHub Actions is configured for Ubuntu and Windows on Python 3.10 and 3.14. Local test results and hosted checks are separate evidence.

Prototype code: [MIT](LICENSE). Ollama, model weights and other future dependencies retain their own licenses. Attribute meaningful reused work in the README and submission.
