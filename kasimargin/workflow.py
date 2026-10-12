"""Calculation precedes optional inference; failure retains a labelled baseline."""
from .engine import calculate
from .explanations import catalogue, render
from .ollama import LocalOllama, ModelUnavailable


def decision(request, model=None, client=None):
    summary = calculate(request)
    allowed = catalogue(summary)
    baseline = {"fact_ids": list(allowed["facts"]), "flag_ids": list(allowed["required_flags"]), "action_ids": list(allowed["options"])}
    selected = baseline
    inference = {"status": "NOT_REQUESTED", "model": None}
    source = "deterministic_template; MODEL_NOT_RUN"
    if model is not None:
        try:
            selected, metadata = (client or LocalOllama()).select(summary, model)
            inference = {"status": "ADMITTED", **metadata}
            source = "local_model_selection; deterministic_renderer"
        except ModelUnavailable as exc:
            inference = {"status": "REJECTED_OR_UNAVAILABLE", "model": model, "reason": str(exc)}
            source = "deterministic_fallback; MODEL_OUTPUT_NOT_ADMITTED"
    return {
        "summary": summary, "selection": selected,
        "explanation": render(summary, selected), "explanation_source": source,
        "inference": inference, "baseline_selection": baseline,
        "baseline_explanation": render(summary, baseline),
    }
