"""Seven synthetic scenarios, private wire/resource traces, redacted technical receipt."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import subprocess
import sys
from threading import Event, Thread
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import psutil
from kasimargin.jsonio import dumps, loads
from kasimargin.ollama import LocalOllama, MODELS, ModelUnavailable
from kasimargin.workflow import decision


def resources(stop, rows):
    while not stop.is_set():
        memory = psutil.virtual_memory()
        processes = []
        for process in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                if "ollama" in (process.info["name"] or "").lower():
                    processes.append({"pid": process.info["pid"], "name": process.info["name"], "rss": process.info["memory_info"].rss})
            except (psutil.Error, AttributeError): pass
        try:
            gpu = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.free,utilization.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5)
            gpu_usage = gpu.stdout.strip() if gpu.returncode == 0 else "measurement unavailable"
        except (OSError, subprocess.TimeoutExpired):
            gpu_usage = "measurement unavailable"
        rows.append({"at": datetime.now(timezone.utc).isoformat(), "cpu_percent": psutil.cpu_percent(), "available_ram_bytes": memory.available, "ram_percent": memory.percent, "ollama_processes": processes, "gpu_usage": gpu_usage})
        stop.wait(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MODELS, default="gemma4:e2b-it-q4_K_M")
    parser.add_argument("--repeats", type=int, default=2)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 5: parser.error("repeats must be between 1 and 5")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    private = ROOT / "local-data/gemma-evaluation" / timestamp
    private.mkdir(parents=True)
    traces, rows = [], []
    client = LocalOllama(timeout=300, trace=traces.append)
    version = client._request("GET", "/api/version")
    model_digest = client.digest(args.model)
    metadata = client._request("POST", "/api/show", {"model": args.model})
    (private / "runtime-private.json").write_text(dumps({"version": version, "show": metadata, "tags": client._request("GET", "/api/tags")}), encoding="utf-8")
    paths = [ROOT / "fixtures" / f"{number:02}.json" for number in range(1, 7)] + [ROOT / "fixtures/itemized/01.json"]
    observations = []
    for path in paths:
        fixture = loads(path.read_text(encoding="utf-8"))
        baseline_started = perf_counter()
        baseline = decision(fixture["input"])
        baseline_elapsed = perf_counter() - baseline_started
        client._request("POST", "/api/generate", {"model": args.model, "keep_alive": 0})
        loaded = client._request("GET", "/api/ps").get("models", [])
        cold_confirmed = not any(entry.get("name") == args.model or entry.get("model") == args.model for entry in loaded)
        for repeat in range(args.repeats + 1):
            sample_rows, stop = [], Event()
            sampler = Thread(target=resources, args=(stop, sample_rows), daemon=True)
            sampler.start(); start = perf_counter()
            result = decision(fixture["input"], args.model, client)
            elapsed = perf_counter() - start
            stop.set(); sampler.join(timeout=7)
            admitted = result["inference"]["status"] == "ADMITTED"
            result_flags = result["selection"]["flag_ids"]
            observation = {"fixture_id": fixture["fixture_id"], "scenario": fixture["scenario"], "pass": "cold" if repeat == 0 else f"warm-{repeat}", "cold_unload_confirmed": cold_confirmed if repeat == 0 else False, "elapsed_seconds": round(elapsed, 6), "baseline_elapsed_seconds": round(baseline_elapsed, 6), "inference": result["inference"], "output_admitted": admitted, "fallback_used": not admitted, "all_warnings_surfaced": set(result_flags) == set(baseline["summary"]["flags"]), "model_warnings_surfaced": admitted and set(result_flags) == set(baseline["summary"]["flags"]), "selection_equals_baseline": result["selection"] == baseline["selection"] if admitted else None, "deterministic_summary_unchanged": result["summary"] == baseline["summary"], "flags": baseline["summary"]["flags"], "status": baseline["summary"]["status"], "resource_sample_count": len(sample_rows)}
            observations.append(observation)
            rows.extend(sample_rows)
            (private / f"{fixture['fixture_id']}-{repeat}-private.json").write_text(dumps({"fixture": fixture, "result": result, "resources": sample_rows}), encoding="utf-8")
            (private / "wire-private.json").write_text(dumps(traces), encoding="utf-8")
            (private / "observations-private.json").write_text(dumps(observations), encoding="utf-8")
            print(f"{fixture['fixture_id']} {observation['pass']}: {result['inference']['status']} in {elapsed:.2f}s", flush=True)
    cold = [row["elapsed_seconds"] for row in observations if row["pass"] == "cold"]
    warm = [row["elapsed_seconds"] for row in observations if row["pass"] != "cold"]
    receipt = {"schema_version": "kasimargin-real-gemma-evaluation-v1", "recorded_at": datetime.now(timezone.utc).isoformat(), "data_class": "SYNTHETIC", "model": args.model, "digest": model_digest, "ollama_version": version.get("version"), "runtime_options": {"num_ctx":4096,"num_predict":512,"temperature":0,"seed":0,"think":False}, "scenario_count":7, "calls":len(observations), "admitted":sum(row["output_admitted"] for row in observations), "fallback":sum(row["fallback_used"] for row in observations), "cold_latency_seconds":{"min":min(cold),"median":statistics.median(cold),"max":max(cold)}, "warm_latency_seconds":{"min":min(warm),"median":statistics.median(warm),"max":max(warm)}, "observations":observations, "resource_measurement":{"method":"psutil plus nvidia-smi, approximately once per second during calls", "samples":len(rows), "raw_samples":"PRIVATE_NOT_PUBLISHED", "machine_identity":"PRIVATE_NOT_PUBLISHED"}, "raw_model_outputs":"PRIVATE_NOT_PUBLISHED", "scope":"technical output admission, runtime latency and deterministic-baseline comparison on synthetic fixtures", "comprehension_benefit":"NOT_MEASURED", "operator_trial":"NOT_RUN", "economic_value":"UNPROVEN", "e4b":"DEFERRED_PENDING_RESOURCE_HEADROOM"}
    receipt_path = ROOT / "docs/receipts" / f"gemma-evaluation-{timestamp}.json"
    receipt_path.write_bytes((json.dumps(receipt, indent=2)+"\n").encode("utf-8"))
    print(f"Redacted receipt: {receipt_path.relative_to(ROOT)}", flush=True)
    client._request("POST", "/api/generate", {"model": args.model, "keep_alive": 0})


if __name__ == "__main__": main()
