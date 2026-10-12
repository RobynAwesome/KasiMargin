"""Explicit cash snapshot, independent margin and fail-closed decision state."""
from datetime import datetime


class ContractError(ValueError):
    pass


def money(value, name):
    if value is not None and (type(value) is not int or value < 0):
        raise ContractError(f"{name} must be null or non-negative integer ZAR cents")
    return value


def instant(value, name):
    if not isinstance(value, str):
        raise ContractError(f"{name} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{name} must be an ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContractError(f"{name} must include a timezone")
    return parsed


def exact_keys(obj, keys, name):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        raise ContractError(f"{name} fields must be exactly {sorted(keys)}")


def calculate(request):
    if isinstance(request, dict) and request.get("schema_version") == "kasimargin-input-v2":
        from .obligations import prepare_request
        request = prepare_request(request)
    exact_keys(request, {"currency", "performance", "cash_position", "transactions"}, "request")
    if request["currency"] != "ZAR":
        raise ContractError("only ZAR is supported")
    performance = request["performance"]
    exact_keys(performance, {"recorded_sales_cents", "attributable_costs_cents", "complete"}, "performance")
    if type(performance["complete"]) is not bool:
        raise ContractError("performance.complete must be boolean")
    sales = money(performance["recorded_sales_cents"], "recorded_sales_cents")
    costs = money(performance["attributable_costs_cents"], "attributable_costs_cents")
    margin = sales - costs if performance["complete"] and sales is not None and costs is not None else None

    position = request["cash_position"]
    amount_keys = ("verified_cash_cents", "due_liabilities_cents", "committed_spend_cents", "minimum_buffer_cents")
    exact_keys(position, {*amount_keys, "snapshot_at", "decision_at", "horizon_end", "max_snapshot_age_seconds", "basis_confirmed", "unresolved_flags", "evidence_refs"}, "cash_position")
    values = {key: money(position[key], key) for key in amount_keys}
    if type(position["basis_confirmed"]) is not bool:
        raise ContractError("basis_confirmed must be boolean")
    age_limit = position["max_snapshot_age_seconds"]
    if type(age_limit) is not int or age_limit < 0:
        raise ContractError("max_snapshot_age_seconds must be a non-negative integer")
    times = {key: instant(position[key], key) for key in ("snapshot_at", "decision_at", "horizon_end")}
    if not times["snapshot_at"] <= times["decision_at"] < times["horizon_end"]:
        raise ContractError("snapshot_at <= decision_at < horizon_end required")
    for key in ("unresolved_flags", "evidence_refs"):
        if not isinstance(position[key], list) or any(not isinstance(s, str) or not s.strip() for s in position[key]):
            raise ContractError(f"{key} must be a list of non-empty strings")

    flags, blocking = [], []

    def flag(code, block=False):
        if code not in flags:
            flags.append(code)
        if block and code not in blocking:
            blocking.append(code)

    if margin is None:
        flag("MARGIN_UNKNOWN")
    for key, value in values.items():
        if value is None:
            flag(f"UNKNOWN_{key.upper()}", True)
    if not position["basis_confirmed"]:
        flag("CASH_BASIS_UNCONFIRMED", True)
    if not position["evidence_refs"]:
        flag("MISSING_CASH_EVIDENCE", True)
    if (times["decision_at"] - times["snapshot_at"]).total_seconds() > age_limit:
        flag("STALE_CASH_SNAPSHOT", True)
    for unresolved in position["unresolved_flags"]:
        flag(f"UNRESOLVED:{unresolved}", True)

    transactions = request["transactions"]
    if not isinstance(transactions, list):
        raise ContractError("transactions must be a list")
    ids, payments = set(), set()
    receivables = 0
    receivables_known = True
    for transaction in transactions:
        exact_keys(transaction, {"id", "kind", "amount_cents", "is_confirmed", "reference_id", "timestamp", "source_description"}, "transaction")
        if any(not isinstance(transaction[key], str) or not transaction[key].strip() for key in ("id", "reference_id")):
            raise ContractError("transaction id and reference_id must be non-empty strings")
        if not isinstance(transaction["source_description"], str):
            raise ContractError("source_description must be a string")
        if type(transaction["is_confirmed"]) is not bool:
            raise ContractError("is_confirmed must be boolean")
        amount = money(transaction["amount_cents"], "transaction.amount_cents")
        if amount is None:
            raise ContractError("transaction amount cannot be null")
        kind = transaction["kind"]
        if not isinstance(kind, str) or kind not in {"cash_sale", "credit_sale", "credit_collection", "supplier_payment", "operating_payment"}:
            raise ContractError("unsupported transaction kind")
        transaction_at = instant(transaction["timestamp"], "transaction.timestamp")
        if transaction_at > times["snapshot_at"]:
            flag("POST_SNAPSHOT_TRANSACTION", True)
        if transaction["id"] in ids:
            flag("DUPLICATE_TRANSACTION_ID", True)
        ids.add(transaction["id"])
        if not transaction["is_confirmed"]:
            flag("UNCONFIRMED_TRANSACTION", True)
            receivables_known = False
        if kind in {"supplier_payment", "operating_payment"}:
            # Same expense/invoice reference is suspected, not automatically removed.
            key = transaction["reference_id"]
            if key in payments:
                flag("POSSIBLE_DUPLICATE_PAYMENT", True)
            payments.add(key)
        if kind == "credit_sale":
            receivables += amount
            flag("CREDIT_SALES_NOT_CASH")
        elif kind == "credit_collection":
            receivables -= amount
    if receivables < 0:
        flag("RECEIVABLES_RECONCILIATION_REQUIRED", True)
        receivables_known = False

    # The snapshot already reflects received cash and paid expenses. Never add
    # sales or subtract historical payments again. The caller attests that due
    # liabilities and future committed spend are disjoint and unpaid.
    raw = None if blocking else (values["verified_cash_cents"] - values["due_liabilities_cents"] - values["minimum_buffer_cents"] - values["committed_spend_cents"])
    headroom = None if raw is None else max(0, raw)
    deficit = None if raw is None else max(0, -raw)
    if deficit:
        flag("PROTECTED_CASH_DEFICIT")
    if headroom == 0:
        flag("NO_DISCRETIONARY_HEADROOM")
    return {
        "schema_version": "kasimargin-summary-v1",
        "currency": "ZAR",
        "operating_margin_cents": margin,
        "cash_headroom_cents": headroom,
        "protected_cash_deficit_cents": deficit,
        "recorded_receivables_delta_cents": receivables if receivables_known else None,
        "status": "HOLD_INSUFFICIENT_DATA" if blocking else "CALCULATED",
        "flags": flags,
        "blocking_flags": blocking,
        "horizon_end": position["horizon_end"],
        "cash_basis": {**values, "snapshot_at": position["snapshot_at"], "decision_at": position["decision_at"]},
        "evidence_refs": list(position["evidence_refs"]),
        "evidence_scope": "synthetic_or_operator_attested; no bank verification",
    }
