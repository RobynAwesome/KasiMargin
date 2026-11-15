"""Governance invariants: reveal envelope, exact-cents checks and pre-measurement CCP-ECV-01 gate."""
from .engine import ContractError

REVEAL_STAGE_ORDER = ("LEDGER", "ATTESTATION", "RESULT", "RECONCILIATION", "RECEIPT", "FALLBACK")
UI_CLASSES = ("DEMO", "CAPTURE", "REVEAL")


def _is_exact_int_or_none(value):
    return value is None or (type(value) is int)


def reveal_envelope(stage, *, ui_class="REVEAL", receipt_sha256=None, ledger_write_authority="NONE", owner_approval_required=False):
    """Build a bounded UI reveal envelope without granting write, purchase or merge authority."""
    if stage not in REVEAL_STAGE_ORDER:
        raise ContractError(f"unsupported reveal stage: {stage}")
    if ui_class not in UI_CLASSES:
        raise ContractError(f"unsupported ui_class: {ui_class}")
    if ledger_write_authority != "NONE":
        raise ContractError("reveal and model surfaces cannot hold ledger write authority")
    if type(owner_approval_required) is not bool:
        raise ContractError("owner_approval_required must be boolean")
    if receipt_sha256 is not None and (not isinstance(receipt_sha256, str) or len(receipt_sha256) != 64):
        raise ContractError("receipt_sha256 must be a 64-character hex digest when provided")
    return {
        "schema_version": "kasimargin-reveal-envelope-v1",
        "stage": stage,
        "stage_index": REVEAL_STAGE_ORDER.index(stage),
        "ui_class": ui_class,
        "receipt_sha256": receipt_sha256,
        "ledger_write_authority": "NONE",
        "purchase_authority": "NONE",
        "merge_authority": "NONE",
        "owner_approval_required": owner_approval_required,
    }


def kmec_observations(summary, ledger_day=None):
    """Verify exact integer-cents invariants across engine summary and optional day ledger summary."""
    if not isinstance(summary, dict) or summary.get("currency") != "ZAR":
        raise ContractError("KMEC check requires a ZAR engine summary")
    for field in ("operating_margin_cents", "cash_headroom_cents", "protected_cash_deficit_cents", "recorded_receivables_delta_cents"):
        if not _is_exact_int_or_none(summary.get(field)):
            raise ContractError(f"non-integer financial field in KMEC summary: {field}")
    basis = summary.get("cash_basis")
    if not isinstance(basis, dict):
        raise ContractError("cash_basis must be an object")
    for field in ("verified_cash_cents", "due_liabilities_cents", "minimum_buffer_cents", "committed_spend_cents"):
        if not _is_exact_int_or_none(basis.get(field)):
            raise ContractError(f"non-integer cash_basis field: {field}")
    hold_preserved = (summary.get("status") != "HOLD_INSUFFICIENT_DATA") or (summary.get("cash_headroom_cents") is None)
    ledger_isolated = True
    if ledger_day is not None:
        if not isinstance(ledger_day, dict):
            raise ContractError("ledger_day must be an object when supplied")
        ledger_isolated = ledger_day.get("cash_position_status") == "NOT_PREPARED"
    return {
        "schema_version": "kasimargin-kmec-observations-v1",
        "currency": "ZAR",
        "integer_cents_exact": True,
        "hold_preserved": hold_preserved,
        "profit_and_cash_separated": True,
        "ledger_isolated_from_cash_basis": ledger_isolated,
        "passed": hold_preserved and ledger_isolated,
    }


def evaluate_ccp_ecv_01(
    measured_cases,
    *,
    min_cases=30,
    control_comprehension_accuracy=None,
    treatment_comprehension_accuracy=None,
    safety_regressions=None,
    p_value=None,
):
    """Enforce pre-measurement MAYBE_HOLD boundary before any Gemma value or economic claim."""
    if type(measured_cases) is not int or measured_cases < 0:
        raise ContractError("measured_cases must be a non-negative integer")
    if type(min_cases) is not int or min_cases < 1:
        raise ContractError("min_cases must be a positive integer")

    base = {
        "gate_id": "CCP-ECV-01",
        "measured_cases": measured_cases,
        "min_cases": min_cases,
        "owner_approval_required": True,
        "gemma_value_proven": False,
        "eligible_to_claim_value": False,
    }
    if measured_cases == 0:
        return {
            **base,
            "economic_gate_state": "MAYBE_HOLD",
            "measurement_status": "UNMEASURED_NO_OPERATOR_TRIAL",
            "reason": "Zero consented paired operator cases measured (n=0 < 30); Gemma usefulness and economic benefit remain unverified.",
        }
    if measured_cases < min_cases:
        return {
            **base,
            "economic_gate_state": "MAYBE_HOLD",
            "measurement_status": "INSUFFICIENT_SAMPLE",
            "reason": f"Measured sample n={measured_cases} is below required minimum n={min_cases}.",
        }

    for name, val in (
        ("control_comprehension_accuracy", control_comprehension_accuracy),
        ("treatment_comprehension_accuracy", treatment_comprehension_accuracy),
        ("p_value", p_value),
    ):
        if type(val) is bool or not isinstance(val, (int, float)) or not (0.0 <= float(val) <= 1.0):
            raise ContractError(f"{name} must be a probability between 0.0 and 1.0")
    if type(safety_regressions) is not int or safety_regressions < 0:
        raise ContractError("safety_regressions must be a non-negative integer")

    if safety_regressions > 0:
        return {
            **base,
            "economic_gate_state": "HOLD_SAFETY_REGRESSION",
            "measurement_status": "MEASURED_SAFETY_FAILURE",
            "reason": f"Observed {safety_regressions} safety regression(s); fail-closed.",
        }
    if float(treatment_comprehension_accuracy) <= float(control_comprehension_accuracy) or float(p_value) >= 0.05:
        return {
            **base,
            "economic_gate_state": "REJECT_NO_NET_BENEFIT",
            "measurement_status": "MEASURED_NO_IMPROVEMENT",
            "reason": "Treatment did not demonstrate statistically significant comprehension improvement over baseline.",
        }
    return {
        **base,
        "economic_gate_state": "ADMITTED_FOR_OWNER_REVIEW",
        "measurement_status": "MEASURED_PASSING_SUBJECT_TO_OWNER_REVIEW",
        "gemma_value_proven": True,
        "eligible_to_claim_value": True,
        "reason": "Measured trial met sample, safety and statistical thresholds; awaiting Robyn's sign-off.",
    }
