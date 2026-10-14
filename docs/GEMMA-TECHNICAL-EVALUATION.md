# Local Gemma technical comparison

Recorded at 2026-10-14T09:41:27.114505+00:00 (UTC receipt). All input scenarios are synthetic.

Result: **21/21 admitted, 0 rejected model outputs, 0 fallback results, 0 unavailable or malformed responses**. All 21 deterministic financial summaries remained unchanged and every required warning was surfaced. 18/21 admitted selections matched the baseline exactly.

Exact tag: `gemma4:e2b-it-q4_K_M`. Installed digest: `b37049369adfe3d2b653af0ab301a062ca5cbe96ace6aa0d3f2559ee9b563fc2`. Ollama `0.40.3`, loopback only; cloud disabled in the started service.

Cold attempts: 56.34-294.94 seconds, median 89.23. Warm attempts: 2.74-42.22 seconds, median 5.00.

Deterministic baseline median calculation time across seven scenarios: 0.002265 seconds. The comparison includes adapter transport/model load for Gemma and local calculation for the baseline; it is not an isolated model benchmark.

| Scenario | Cold seconds | Warm 1 seconds | Warm 2 seconds | Admitted |
|---|---:|---:|---:|---:|
| 01: Profitable day with confirmed cash position | 294.94 | 42.22 | 4.16 | 3/3 |
| 02: Low margin with independently constrained cash | 78.90 | 5.24 | 4.76 | 3/3 |
| 03: Cash shortfall against obligations and protected buffer | 56.34 | 4.63 | 9.68 | 3/3 |
| 04: Missing receipts and unknown cash / liabilities | 89.23 | 11.81 | 7.63 | 3/3 |
| 05: Uncollected credit sale earns recorded margin without cash | 89.06 | 3.02 | 2.74 | 3/3 |
| 06: Suspected duplicate supplier payment requires human resolution | 96.23 | 4.21 | 3.60 | 3/3 |
| itemized-01: Itemized liabilities with a reconciled partial payment | 147.45 | 10.02 | 8.93 | 3/3 |

Cold means the model runner was unloaded and absence confirmed through /api/ps. OS disk caches were not flushed. One cold attempt and two warm repeats were run per scenario, with a 300-second evaluator socket timeout. Normal app requests retain their 90-second timeout: a slow cold load can produce labelled fallback in the app.

Resource observation: low available RAM was observed. 214 samples recorded global CPU/RAM, Ollama process RSS and nvidia-smi GPU readings. Sampling pauses one second between iterations; process/GPU query overhead means actual cadence is not fixed at 1 Hz. Exact capacity, process identifiers, machine details and raw samples remain private. Concurrent machine activity and separate run segments limit attribution; no hardware-wide functionality certification is claimed.

The first segment stopped after 15 completed comparisons. The evaluator and both local services were no longer observed; cause UNKNOWN. One resume preflight failed because the local endpoint refused connections. The services were restarted and the remaining six comparisons resumed at a confirmed scenario boundary. Additional interrupted activity has no captured response and remains UNKNOWN. Counts and latency describe the 21 recorded completed comparisons, not every attempted request or uninterrupted availability.

Integer-cents arithmetic, unknown/HOLD semantics and selection validation were preserved. No model answer was rewritten to pass. The model selected IDs; the trusted renderer supplied the financial values and warnings. Complete wire replies and model selections remain private.

This run establishes bounded local execution and output admission. Exact agreement with the deterministic selection does not demonstrate added usefulness. Language quality, operator comprehension and economic benefit remain unmeasured. E4B is deferred because of storage and memory pressure. The consented operator comparison is the next separate experiment; no recruitment, consent or trial has occurred.

[Full redacted technical receipt](receipts/gemma-evaluation-20261013T222027Z.json) · [Operator comparison protocol](OPERATOR-COMPARISON.md) · [Partial storage recovery](receipts/storage-recovery-2026-10-13.json)
