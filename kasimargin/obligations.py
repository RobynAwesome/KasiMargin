"""Convert itemized obligations to the v1 engine without guessing missing totals."""
from copy import deepcopy
from .engine import ContractError, exact_keys, instant, money


def nonempty(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a non-empty string")
    if value != value.strip():
        raise ContractError(f"{name} cannot have surrounding whitespace")
    return value.strip()


def prepare_request(request):
    exact_keys(request, {"schema_version", "currency", "performance", "cash_position", "transactions", "obligations"}, "v2 request")
    position = request["cash_position"]
    exact_keys(position, {"verified_cash_cents", "minimum_buffer_cents", "snapshot_at", "decision_at", "horizon_end", "max_snapshot_age_seconds", "basis_confirmed", "unresolved_flags", "evidence_refs", "obligations_complete"}, "v2 cash_position")
    if type(position["obligations_complete"]) is not bool:
        raise ContractError("obligations_complete must be boolean")
    if not isinstance(position["unresolved_flags"], list):
        raise ContractError("unresolved_flags must be a list")
    for value in position["unresolved_flags"]:
        nonempty(value, "unresolved flag")
    if not isinstance(position["evidence_refs"], list):
        raise ContractError("evidence_refs must be a list")
    for value in position["evidence_refs"]:
        nonempty(value, "cash evidence reference")
    if not isinstance(request["obligations"], list) or not isinstance(request["transactions"], list):
        raise ContractError("obligations and transactions must be lists")
    snapshot = instant(position["snapshot_at"], "snapshot_at")
    horizon = instant(position["horizon_end"], "horizon_end")
    flags = list(position["unresolved_flags"])
    totals = {"liability": 0, "committed": 0}
    identities, references, allocated_payments = set(), set(), set()
    transactions = {}
    for item in request["transactions"]:
        if not isinstance(item, dict):
            raise ContractError("transaction must be an object")
        identity = nonempty(item.get("id"), "transaction.id")
        if identity in transactions:
            flags.append("DUPLICATE_TRANSACTION_ID")
        transactions[identity] = item

    for item in request["obligations"]:
        exact_keys(item, {"id", "reference_id", "bucket", "amount_cents", "paid_cents", "due_at", "is_confirmed", "payment_transaction_ids", "evidence_ref"}, "obligation")
        identity = nonempty(item["id"], "obligation.id")
        reference = nonempty(item["reference_id"], "obligation.reference_id")
        nonempty(item["evidence_ref"], "obligation.evidence_ref")
        bucket = item["bucket"]
        if not isinstance(bucket, str) or bucket not in totals:
            raise ContractError("obligation bucket must be liability or committed")
        if type(item["is_confirmed"]) is not bool:
            raise ContractError("obligation.is_confirmed must be boolean")
        amount = money(item["amount_cents"], "obligation.amount_cents")
        paid = money(item["paid_cents"], "obligation.paid_cents")
        due = instant(item["due_at"], "obligation.due_at")
        payment_ids = item["payment_transaction_ids"]
        if not isinstance(payment_ids, list):
            raise ContractError("payment_transaction_ids must be a list")
        payment_ids = [nonempty(value, "payment transaction ID") for value in payment_ids]
        if identity in identities or reference in references:
            flags.append("DUPLICATE_OR_OVERLAPPING_OBLIGATION")
        identities.add(identity)
        references.add(reference)
        if not item["is_confirmed"]:
            flags.append("UNCONFIRMED_OBLIGATION")
        if amount is None or paid is None:
            flags.append("UNKNOWN_OBLIGATION_AMOUNT")
        elif paid > amount:
            flags.append("OBLIGATION_OVERPAID")

        payment_total = 0
        for payment_id in payment_ids:
            if payment_id in allocated_payments:
                flags.append("PAYMENT_ALLOCATED_MORE_THAN_ONCE")
            allocated_payments.add(payment_id)
            transaction = transactions.get(payment_id)
            if transaction is None:
                flags.append("MISSING_OBLIGATION_PAYMENT")
                continue
            value = money(transaction.get("amount_cents"), "payment.amount_cents")
            if value is None:
                raise ContractError("payment amount cannot be null")
            payment_total += value
            if (transaction.get("kind") not in ("supplier_payment", "operating_payment")
                    or transaction.get("reference_id") != item["reference_id"]
                    or transaction.get("is_confirmed") is not True
                    or instant(transaction.get("timestamp"), "payment.timestamp") > snapshot):
                flags.append("OBLIGATION_PAYMENT_NOT_RECONCILED")
        if paid is not None and payment_total != paid:
            flags.append("OBLIGATION_PAYMENT_TOTAL_MISMATCH")
        # Only the outstanding amount due within the horizon is reserved.
        # Already-paid entries remain in the trace and are never subtracted again.
        if amount is not None and paid is not None and paid <= amount and due <= horizon:
            totals[bucket] += amount - paid

    # A payment to an item marked wholly unpaid also needs correction.
    for transaction in request["transactions"]:
        if (transaction.get("kind") in ("supplier_payment", "operating_payment")
                and isinstance(transaction.get("reference_id"), str)
                and transaction["reference_id"].strip() in references
                and transaction["id"].strip() not in allocated_payments):
            flags.append("UNALLOCATED_OBLIGATION_PAYMENT")
    if not position["obligations_complete"]:
        flags.append("OBLIGATIONS_INCOMPLETE")
    result = deepcopy(request)
    del result["schema_version"]
    del result["obligations"]
    del result["cash_position"]["obligations_complete"]
    result["cash_position"].update(
        due_liabilities_cents=totals["liability"],
        committed_spend_cents=totals["committed"],
        unresolved_flags=list(dict.fromkeys(flags)),
    )
    return result
