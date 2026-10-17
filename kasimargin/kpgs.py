"""Read-only bridge to the owner's existing local KPGS context entry runtime.

This observes context availability, never financial admission or bank verification.
The root is explicit local configuration, not a browser-controlled executable path.
"""
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
from threading import Lock
from time import monotonic
from .jsonio import loads
from .engine import ContractError, exact_keys, instant

ROOT = Path(__file__).resolve().parents[1]
ACK = "I_AM_STATELESS_RENTER_NOT_LANDLORD"


def validate_observation(value):
    """Validate historical context metadata without claiming or repeating a probe."""
    exact_keys(value, {"status", "checked_at", "scope", "financial_admission", "bank_verification"}, "context observation")
    if (value["status"] not in ("NOT_CONFIGURED", "UNAVAILABLE", "INVALID_REPLY", "CONNECTED_READ_ONLY")
            or value["scope"] != "READ_ONLY_CONTEXT_ENTRY"
            or value["financial_admission"] != "NOT_ESTABLISHED"
            or value["bank_verification"] != "NOT_PERFORMED"):
        raise ContractError("context observation cannot attest financial approval or bank verification")
    instant(value["checked_at"], "context.checked_at")


class LocalKpgs:
    def __init__(self, root=None):
        self.root = Path(root).resolve() if root else None
        self._lock, self._cached, self._checked = Lock(), None, 0.0

    def probe(self):
        with self._lock:
            if self._cached is not None and monotonic() - self._checked < 30:
                return dict(self._cached)
            result = self._observe()
            self._cached, self._checked = result, monotonic()
            return dict(result)

    def _observe(self):
        result = {"status": "NOT_CONFIGURED", "checked_at": datetime.now(timezone.utc).isoformat(),
                  "scope": "READ_ONLY_CONTEXT_ENTRY", "financial_admission": "NOT_ESTABLISHED",
                  "bank_verification": "NOT_PERFORMED"}
        if self.root is None:
            return result
        script = self.root / "scripts/kc_kpgs_governance.py"
        if not script.is_file():
            return {**result, "status": "UNAVAILABLE"}
        containment = (ROOT / "local-data/kpgs-runtime/contained-ledgers").resolve()
        if not containment.is_relative_to(ROOT.resolve()):
            return {**result, "status": "UNAVAILABLE"}
        environment = {**os.environ, "KC_LEDGER_ROOT": str(containment)}
        try:
            process = subprocess.run([sys.executable, "-I", "-B", str(script), "entry",
                                      "--renter-id", "kasimargin_context_adapter"],
                                     cwd=ROOT, env=environment, capture_output=True,
                                     encoding="utf-8", timeout=5, check=False)
            if process.returncode != 0 or len(process.stdout.encode("utf-8")) > 262144:
                return {**result, "status": "UNAVAILABLE"}
            payload = loads(process.stdout)
            if (not isinstance(payload, dict) or payload.get("schema") != "kpgs_hood_entry_assertion_v1"
                    or payload.get("hood_ack_required") != ACK
                    or not isinstance(payload.get("entryway_source"), str)
                    or payload.get("renter_id") != "kasimargin_context_adapter"):
                return {**result, "status": "INVALID_REPLY"}
            # No doctrine content, file paths, identity seats or runtime ACK claims leave this bridge.
            return {**result, "status": "CONNECTED_READ_ONLY"}
        except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
            return {**result, "status": "UNAVAILABLE"}
