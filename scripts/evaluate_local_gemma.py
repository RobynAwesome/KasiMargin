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
from kasimargin.jsonio import dumps, loads
from kasimargin.ollama import LocalOllama, MODELS, ModelUnavailable
from kasimargin.workflow import decision


def resources(stop, rows):
    import psutil
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


def validate_resume_prefix(observations, fixture_ids, repeats, model_digest):
    expected = [(fixture_id, "cold" if repeat == 0 else f"warm-{repeat}")
                for fixture_id in fixture_ids for repeat in range(repeats + 1)]
    actual = [(row["fixture_id"], row["pass"]) for row in observations]
    if actual != expected[:len(actual)] or len(actual) % (repeats + 1):
        raise ValueError("resume requires an ordered prefix of fully completed scenarios")
    if any(row["output_admitted"] and row["inference"]["digest"] != model_digest for row in observations):
        raise ValueError("model digest changed; start a separate run")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MODELS, default="gemma4:e2b-it-q4_K_M")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--resume", help="Existing private run timestamp; resume only at a completed scenario boundary")
    args = parser.parse_args()
    if not 1 <= args.repeats <= 5: parser.error("repeats must be between 1 and 5")
    timestamp = args.resume or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    try:
        datetime.strptime(timestamp, "%Y%m%dT%H%M%SZ")
    except ValueError:
        parser.error("resume must be a run timestamp, not a path")
    private = ROOT / "local-data/gemma-evaluation" / timestamp
    if args.resume and not private.is_dir(): parser.error("private run does not exist")
    private.mkdir(parents=True, exist_ok=bool(args.resume))
    traces, rows = [], []
    client = LocalOllama(timeout=300, trace=traces.append)
    version = client._request("GET", "/api/version")
    model_digest = client.digest(args.model)
    metadata = client._request("POST", "/api/show", {"model": args.model})
    (private / "runtime-private.json").write_text(dumps({"version": version, "show": metadata, "tags": client._request("GET", "/api/tags")}), encoding="utf-8")
    paths = [ROOT / "fixtures" / f"{number:02}.json" for number in range(1, 7)] + [ROOT / "fixtures/itemized/01.json"]
    observations = []
    if args.resume:
        observations = loads((private / "observations-private.json").read_text(encoding="utf-8"))
        traces.extend(loads((private / "wire-private.json").read_text(encoding="utf-8")))
        try:
            validate_resume_prefix(observations, [loads(path.read_text(encoding="utf-8"))["fixture_id"] for path in paths], args.repeats, model_digest)
        except ValueError as exc:
            parser.error(str(exc))
        installed = loads((private / "source-manifest-private.json").read_text(encoding="utf-8"))
        import hashlib
        if any(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest
               for name, digest in installed.items() if name != "scripts/evaluate_local_gemma.py"):
            parser.error("adapter or financial source changed; start a separate run")
        for row in observations:
            saved = loads((private / f"{row['fixture_id']}-{0 if row['pass'] == 'cold' else row['pass'].split('-')[1]}-private.json").read_text(encoding="utf-8"))
            current = next(loads(path.read_text(encoding="utf-8")) for path in paths
                           if loads(path.read_text(encoding="utf-8"))["fixture_id"] == row["fixture_id"])
            if saved["fixture"] != current:
                parser.error("completed fixture changed; start a separate run")
            rows.extend(saved["resources"])
    for path in paths:
        fixture = loads(path.read_text(encoding="utf-8"))
        if any(row["fixture_id"] == fixture["fixture_id"] for row in observations):
            continue
        baseline_started = perf_counter()
        baseline = decision(fixture["input"])
        baseline_elapsed = perf_counter() - baseline_started
        client._request("POST", "/api/generate", {"model": args.model, "keep_alive": 0})
        loaded = client._request("GET", "/api/ps").get("models", [])
        cold_confirmed = not any(entry.get("name") == args.model or entry.get("model") == args.model for entry in loaded)
        for repeat in range(args.repeats + 1):
            sample_rows, stop = [], Event()
            sampler = Thread(target=resources, args=(stop, sample_rows), daemon=True)
            trace_start = len(traces)
            sampler.start(); start = perf_counter()
            result = decision(fixture["input"], args.model, client)
            elapsed = perf_counter() - start
            stop.set(); sampler.join(timeout=7)
            admitted = result["inference"]["status"] == "ADMITTED"
            result_flags = result["selection"]["flag_ids"]
            replies = [trace for trace in traces[trace_start:] if trace["path"] == "/api/chat"]
            reply = replies[-1] if replies else None
            output_received = False
            metrics = {}
            if reply is not None and reply["status"] == 200:
                try:
                    payload = loads(reply["raw_response"])
                    message = payload.get("message") if isinstance(payload, dict) else None
                    output_received = isinstance(message, dict) and isinstance(message.get("content"), str)
                    if isinstance(payload, dict):
                        metrics = {key: payload[key] for key in ("total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration", "eval_count", "eval_duration")
                                   if type(payload.get(key)) is int and payload[key] >= 0}
                except ValueError:
                    pass
            failure_class = ("NONE" if admitted else "MODEL_OUTPUT_REJECTED" if output_received
                             else "NO_COMPLETED_CHAT_RESPONSE" if reply is None
                             else "LOCAL_HTTP_ERROR" if reply["status"] != 200
                             else "MALFORMED_MODEL_RESPONSE")
            observation = {"fixture_id": fixture["fixture_id"], "scenario": fixture["scenario"], "pass": "cold" if repeat == 0 else f"warm-{repeat}", "cold_unload_confirmed": cold_confirmed if repeat == 0 else False, "elapsed_seconds": round(elapsed, 6), "baseline_elapsed_seconds": round(baseline_elapsed, 6), "inference": result["inference"], "output_admitted": admitted, "fallback_used": not admitted, "all_warnings_surfaced": set(result_flags) == set(baseline["summary"]["flags"]), "model_warnings_surfaced": admitted and set(result_flags) == set(baseline["summary"]["flags"]), "selection_equals_baseline": result["selection"] == baseline["selection"] if admitted else None, "deterministic_summary_unchanged": result["summary"] == baseline["summary"], "flags": baseline["summary"]["flags"], "status": baseline["summary"]["status"], "resource_sample_count": len(sample_rows)}
            observation.update({"completed_chat_response_observed": reply is not None,
                                "chat_http_status": reply["status"] if reply is not None else None,
                                "model_output_received": output_received,
                                "model_output_rejected": output_received and not admitted,
                                "ollama_metrics": metrics,
                                "failure_class": failure_class})
            observations.append(observation)
            rows.extend(sample_rows)
            (private / f"{fixture['fixture_id']}-{repeat}-private.json").write_text(dumps({"fixture": fixture, "result": result, "resources": sample_rows}), encoding="utf-8")
            (private / "wire-private.json").write_text(dumps(traces), encoding="utf-8")
            (private / "observations-private.json").write_text(dumps(observations), encoding="utf-8")
            print(f"{fixture['fixture_id']} {observation['pass']}: {result['inference']['status']} in {elapsed:.2f}s", flush=True)
    cold = [row["elapsed_seconds"] for row in observations if row["pass"] == "cold"]
    warm = [row["elapsed_seconds"] for row in observations if row["pass"] != "cold"]
    receipt = {"schema_version": "kasimargin-real-gemma-evaluation-v1", "recorded_at": datetime.now(timezone.utc).isoformat(), "data_class": "SYNTHETIC", "model": args.model, "digest": model_digest, "ollama_version": version.get("version"), "runtime_options": {"num_ctx":4096,"num_predict":512,"temperature":0,"seed":0,"think":False}, "scenario_count":7, "calls":len(observations), "admitted":sum(row["output_admitted"] for row in observations), "fallback":sum(row["fallback_used"] for row in observations), "cold_latency_seconds":{"min":min(cold),"median":statistics.median(cold),"max":max(cold)}, "warm_latency_seconds":{"min":min(warm),"median":statistics.median(warm),"max":max(warm)}, "observations":observations, "resource_measurement":{"method":"psutil plus nvidia-smi, approximately once per second during calls", "samples":len(rows), "raw_samples":"PRIVATE_NOT_PUBLISHED", "machine_identity":"PRIVATE_NOT_PUBLISHED"}, "raw_model_outputs":"PRIVATE_NOT_PUBLISHED", "scope":"technical output admission, runtime latency and deterministic-baseline comparison on synthetic fixtures", "comprehension_benefit":"NOT_MEASURED", "operator_trial":"NOT_RUN", "economic_value":"UNPROVEN", "e4b":"DEFERRED_PENDING_RESOURCE_HEADROOM"}
    receipt.update({"call_count_scope": "End-to-end adapter decision attempts, including fallback and failures",
                    "latency_scope": "End-to-end adapter attempts; failed calls are included, not successful-inference-only timing",
                    "completed_chat_responses_observed": sum(row["completed_chat_response_observed"] for row in observations),
                    "model_outputs_received": sum(row["model_output_received"] for row in observations),
                    "model_outputs_rejected": sum(row["model_output_rejected"] for row in observations),
                    "unavailable_or_malformed_responses": sum(not row["model_output_received"] for row in observations)})
    if args.resume:
        receipt["resumed_run"] = {"completed_comparisons": len(observations),
                                  "interruption_cause": "UNKNOWN",
                                  "additional_interrupted_attempts": "UNKNOWN; no completed response captured",
                                  "scope": "Counts and latency describe recorded completed comparisons across run segments"}
    receipt_path = ROOT / "docs/receipts" / f"gemma-evaluation-{timestamp}.json"
    receipt_path.write_bytes((json.dumps(receipt, indent=2)+"\n").encode("utf-8"))
    print(f"Redacted receipt: {receipt_path.relative_to(ROOT)}", flush=True)
    client._request("POST", "/api/generate", {"model": args.model, "keep_alive": 0})


if __name__ == "__main__": main()
