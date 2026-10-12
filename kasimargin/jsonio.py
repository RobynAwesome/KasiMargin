"""Strict JSON at input and model boundaries."""
import json
from .engine import ContractError


def loads(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ContractError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value):
        raise ContractError("non-standard JSON number rejected")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def dumps(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
