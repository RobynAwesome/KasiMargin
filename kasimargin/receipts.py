"""Explicit local saves; immutable files preserve the input and reviewed calculation."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
from .engine import ContractError, exact_keys, instant
from .explanations import render
from .jsonio import dumps, loads
from .workflow import decision
from .kpgs import validate_observation


def digest(payload):
    return sha256(dumps(payload).encode("utf-8")).hexdigest()


def save(request, result, data_class, directory):
    if data_class not in ("SYNTHETIC", "OPERATOR_ATTESTED"):
        raise ContractError("data_class must be SYNTHETIC or OPERATOR_ATTESTED")
    expected = decision(request)
    if "context_check" in result:
        validate_observation(result["context_check"])
    if result["summary"] != expected["summary"] or result["explanation"] != render(expected["summary"], result["selection"]):
        raise ContractError("receipt result does not match the deterministic input")
    payload = {
        "schema_version": "kasimargin-decision-receipt-v1", "recorded_at": datetime.now(timezone.utc).isoformat(),
        "data_class": data_class, "input": request, "result": result,
        "human_review": "NOT_RECORDED", "bank_verification": "NOT_PERFORMED",
    }
    envelope = {"payload": payload, "sha256": digest(payload)}
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"decision-{uuid4().hex}.json"
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(dumps(envelope) + "\n")
    return path


def verify(path):
    envelope = loads(Path(path).read_text(encoding="utf-8"))
    exact_keys(envelope, {"payload", "sha256"}, "receipt")
    payload = envelope["payload"]
    exact_keys(payload, {"schema_version", "recorded_at", "data_class", "input", "result", "human_review", "bank_verification"}, "receipt payload")
    if payload["schema_version"] != "kasimargin-decision-receipt-v1" or digest(payload) != envelope["sha256"]:
        raise ContractError("receipt integrity check failed")
    instant(payload["recorded_at"], "receipt.recorded_at")
    if payload["data_class"] not in ("SYNTHETIC", "OPERATOR_ATTESTED") or payload["human_review"] != "NOT_RECORDED" or payload["bank_verification"] != "NOT_PERFORMED":
        raise ContractError("this receipt format cannot attest external verification or human approval")
    expected = decision(payload["input"])
    result = payload["result"]
    if isinstance(result, dict) and "context_check" in result:
        validate_observation(result["context_check"])
    if not isinstance(result, dict) or result.get("summary") != expected["summary"]:
        raise ContractError("receipt calculation cannot be reproduced")
    if result.get("explanation") != render(expected["summary"], result.get("selection")):
        raise ContractError("receipt explanation cannot be reproduced")
    return {"status": "REPRODUCED", "sha256": envelope["sha256"], "data_class": payload["data_class"], "human_review": payload["human_review"], "bank_verification": payload["bank_verification"], "limit": "content checksum and replay only; not author authentication or external verification"}
