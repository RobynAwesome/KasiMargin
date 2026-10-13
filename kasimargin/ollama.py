"""Optional local model inference; only validated catalogue selections are rendered."""
from http.client import HTTPConnection, HTTPException
import json
from time import perf_counter
from .explanations import catalogue, validate_selection
from .jsonio import loads

MODELS = ("gemma4:e2b-it-q4_K_M", "gemma4:e2b", "gemma4:e4b")
MAX_RESPONSE_BYTES = 262144


class ModelUnavailable(ValueError):
    pass


class LocalOllama:
    def __init__(self, port=11434, timeout=90, trace=None):
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("port must be an integer from 1 to 65535")
        if type(timeout) not in (int, float) or not 0 < timeout <= 300:
            raise ValueError("timeout must be between 0 and 300 seconds")
        self.port, self.timeout = port, timeout
        self.trace = trace

    def _request(self, method, path, payload=None):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=self.timeout)
        try:
            body = None if payload is None else json.dumps(payload, allow_nan=False)
            connection.request(method, path, body=body, headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if self.trace is not None:
                self.trace({"method": method, "path": path, "request": payload,
                            "status": response.status, "raw_response": raw.decode("utf-8", errors="replace")})
            if response.status != 200:
                raise ModelUnavailable(f"local Ollama returned HTTP {response.status}")
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ModelUnavailable("local Ollama response exceeded size limit")
            value = loads(raw.decode("utf-8"))
            if not isinstance(value, dict):
                raise ModelUnavailable("local Ollama returned a non-object response")
            return value
        except (OSError, HTTPException, UnicodeError, ValueError) as exc:
            if isinstance(exc, ModelUnavailable):
                raise
            raise ModelUnavailable("local Ollama unavailable or returned invalid JSON") from exc
        finally:
            connection.close()

    def digest(self, model):
        metadata = self._request("GET", "/api/tags")
        entries = metadata.get("models")
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and entry.get("name") == model:
                    digest = entry.get("digest")
                    if isinstance(digest, str) and digest.strip():
                        return digest
        raise ModelUnavailable("requested model is not installed with a recorded digest")

    def select(self, summary, model):
        if model not in MODELS:
            raise ModelUnavailable("choose an explicitly supported local Gemma candidate")
        digest = self.digest(model)
        allowed = catalogue(summary)
        schema = {
            "type": "object", "additionalProperties": False,
            "required": ["fact_ids", "flag_ids", "action_ids"],
            "properties": {
                "fact_ids": {"type": "array", "uniqueItems": True, "items": {"type": "string", "enum": list(allowed["facts"])}},
                "flag_ids": {"type": "array", "uniqueItems": True, "items": {"type": "string", "enum": allowed["required_flags"]}},
                "action_ids": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "string", "enum": list(allowed["options"])}},
            },
        }
        for key in schema["properties"]:
            if not schema["properties"][key]["items"]["enum"]:
                schema["properties"][key]["maxItems"] = 0
                del schema["properties"][key]["items"]["enum"]
        started = perf_counter()
        response = self._request("POST", "/api/chat", {
            "model": model, "stream": False, "think": False, "format": schema,
            "options": {"temperature": 0, "seed": 0, "num_predict": 512, "num_ctx": 4096}, "keep_alive": "5m",
            "messages": [
                {"role": "system", "content": "Select catalogue IDs to help an operator understand profit versus cash. Return only the selection JSON. Include operating_margin and cash_headroom whenever available. Include protected_cash_deficit for a nonzero shortfall and receivables_delta when credit sales are flagged. Include every required flag exactly once. Choose only approved action options; never invent amounts or add advice. The renderer supplies all financial values."},
                {"role": "user", "content": json.dumps({"status": summary["status"], "catalogue": allowed}, allow_nan=False)},
            ],
        })
        if response.get("model") != model or response.get("done") is not True:
            raise ModelUnavailable("model identity or completion was not confirmed")
        message = response.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ModelUnavailable("missing model selection")
        try:
            selection = loads(message["content"])
            validate_selection(summary, selection)
        except (ValueError, TypeError) as exc:
            raise ModelUnavailable("model selection failed the output contract") from exc
        if self.digest(model) != digest:
            raise ModelUnavailable("model digest changed during inference")
        timing_keys = ("total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration", "eval_count", "eval_duration")
        return selection, {
            "model": model, "digest": digest, "endpoint": f"http://127.0.0.1:{self.port}",
            "elapsed_seconds": round(perf_counter() - started, 6),
            "ollama_metrics": {key: response[key] for key in timing_keys if type(response.get(key)) is int and response[key] >= 0},
        }
