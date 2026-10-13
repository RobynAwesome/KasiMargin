# TypeScript, Flask and local Gemma

The owner approved replacing handwritten browser JavaScript with TypeScript and introducing Python Flask while preserving the accepted ribbon identity and both colour modes. This migration keeps the Python financial engine and explanation admission rules.

## Application boundaries

`kasimargin/web/src/app.ts` describes the request, summary, inference and UI element contracts. Strict TypeScript compilation catches source mismatches; it does not replace runtime financial validation. The browser still receives generated JavaScript, built by `npm run build` into ignored `web/build/`. `theme.ts` remains a separate synchronous initialization script so the remembered mode is applied early. There are no runtime browser packages or external script CDNs.

`server.create_app()` is a Flask application factory. The CLI uses a threaded Werkzeug WSGI server bound to `127.0.0.1`, without debug mode or the reloader. Explicit routes serve the existing logo/styles and generated assets. Missing generated scripts produce a clear build-required response rather than stale source fallback.

The strict JSON parser is applied to wire bytes, preserving duplicate-key rejection instead of relying on Flask's permissive standard JSON loading. The body limit, local Host/Origin gate, no-store/CSP headers, integer-cents checks, unknown-state handling and explicit receipt-save behaviour remain. The same seven synthetic scenarios and real HTTP boundary tests run through Flask.

## Reproducible setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
npm ci
npm run check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m kasimargin --serve
```

Python 3.10+ and Node 24+ are the tested targets. Flask is pinned in `pyproject.toml`; TypeScript is pinned in the npm lockfile. CI builds the frontend before running Python tests. The application remains a local development surface, not an authenticated multi-user deployment.

## Local model evaluation

Current observed state on October 13: official signed Windows Ollama 0.40.3 is installed, its loopback endpoint responds, and cloud use is disabled. The E2B download failed with insufficient disk space. No installed model or model digest exists; no real inference has run. Task-created failed-pull weights were removed to restore working space. Hardware details and raw diagnostics remain private. The [redacted blocker receipt](receipts/gemma-runtime-blocker-2026-10-13.json) records seven actual endpoint checks that retained the labelled deterministic fallback, including its warnings and unknown/HOLD states.

Free enough owner-selected space to leave **at least 8 GiB available on C:** before retrying. Alternatively, the owner can designate another local volume with that capacity and configure Ollama's model directory there. A remote/cloud endpoint is not an alternative in this experiment. The [official tag catalogue](https://ollama.com/library/gemma4/tags) lists approximately 4.6 GB for E2B Q4_K_M and 6.6 GB for E4B; neither listing establishes measured inference fit.

With the existing loopback service running, retry from PowerShell:

```powershell
cd C:\Users\rkhol\KasiMargin
if ((Get-PSDrive C).Free -lt 8GB) { throw 'Free at least 8 GiB on C: before pulling Gemma.' }
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull gemma4:e2b-it-q4_K_M
if ($LASTEXITCODE -ne 0) { throw 'Model pull failed; do not report inference or a model digest.' }
.\.venv\Scripts\python.exe scripts/evaluate_local_gemma.py --model gemma4:e2b-it-q4_K_M --repeats 2
```

The evaluator obtains the full installed digest before any inference. Preserve failures and rejected selections instead of changing the validation gate. A missing model remains an unavailable-runtime fallback, not a rejected model answer.

The selected initial candidate is the official `gemma4:e2b-it-q4_K_M` tag. Alias and larger-model candidates remain explicit choices; cloud tags and remote inference endpoints are not admitted. The adapter uses 4096 context tokens, a 512-token output budget, deterministic seed/temperature settings, and disabled thinking output. The exact installed digest and Ollama version belong in each technical evaluation receipt.

The optional wire observer is for private synthetic evaluation. It never appears in the normal browser response. The evaluator stores raw model responses, model metadata and machine/resource samples under ignored `local-data/gemma-evaluation/`, and publishes only a redacted technical receipt.

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[evaluation]'
.\.venv\Scripts\python.exe scripts/evaluate_local_gemma.py --model gemma4:e2b-it-q4_K_M --repeats 2
```

The script unloads the model before each of seven scenarios and confirms absence from `/api/ps`, then runs one cold and two warm calls per scenario. Cold here means an unloaded model runner; it does not mean flushed OS disk caches or a freshly booted computer. It records baseline timing, admitted/rejected output, actual surfaced model warnings, fallback, deterministic-summary equality, and Ollama load/token metrics. Global CPU/RAM and Ollama process RSS are sampled with psutil; GPU use is sampled with nvidia-smi. These are observations on a busy user machine, not an isolated hardware benchmark.

Output gates are retained. More informative prompts and an explicit quantized tag do not grant a model authority to change figures, omit warnings or issue a purchase command. Malformed or unsupported selections remain rejected. A renderer's fallback warnings cannot be counted as warnings successfully supplied by a model.

E4B requires a separate capacity and measured-performance decision. Download availability or a newer generation does not prove device fit or benefit. Real technical inference does not establish human understanding: [the proposed consented operator comparison](OPERATOR-COMPARISON.md) is the next separate experiment.
