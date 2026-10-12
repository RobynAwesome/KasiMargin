"""Model may select approved IDs. No generated prose reaches this renderer."""
from .engine import ContractError, exact_keys


def catalogue(summary):
    facts = {}
    if summary["operating_margin_cents"] is not None:
        facts["operating_margin"] = {"label": "Estimated operating margin", "amount_cents": summary["operating_margin_cents"]}
    if summary["cash_headroom_cents"] is not None:
        facts["cash_headroom"] = {"label": "Cash headroom within the recorded horizon", "amount_cents": summary["cash_headroom_cents"]}
    if summary["protected_cash_deficit_cents"] is not None:
        facts["protected_cash_deficit"] = {"label": "Shortfall against protected obligations and buffer", "amount_cents": summary["protected_cash_deficit_cents"]}
    if summary["recorded_receivables_delta_cents"] is not None:
        facts["receivables_delta"] = {"label": "Recorded change in receivables; excluded from cash snapshot", "amount_cents": summary["recorded_receivables_delta_cents"]}
    if summary["status"] != "CALCULATED":
        options = {"confirm_records": "Confirm the missing or disputed records before evaluating spending."}
    elif summary["cash_headroom_cents"] == 0:
        options = {"protect_cash": "Protect cash reserved for recorded obligations and the minimum buffer."}
    else:
        options = {
            "preserve_headroom": "Keep the available headroom while checking tomorrow's needs.",
            "compare_restock_quote": "Compare an owner-supplied restock quote against the recorded headroom; no purchase has been assessed yet.",
        }
    return {"facts": facts, "required_flags": summary["flags"], "options": options}


def validate_selection(summary, selection):
    exact_keys(selection, {"fact_ids", "flag_ids", "action_ids"}, "model selection")
    allowed = catalogue(summary)
    for key in selection:
        values = selection[key]
        if not isinstance(values, list) or any(not isinstance(s, str) for s in values) or len(values) != len(set(values)):
            raise ContractError(f"{key} must be a list of unique strings")
    if not set(selection["fact_ids"]) <= set(allowed["facts"]):
        raise ContractError("unknown fact ID")
    required = {"cash_headroom"} if summary["cash_headroom_cents"] is not None else set()
    if summary["operating_margin_cents"] is not None:
        required.add("operating_margin")
    if summary["protected_cash_deficit_cents"]:
        required.add("protected_cash_deficit")
    if "CREDIT_SALES_NOT_CASH" in summary["flags"] and summary["recorded_receivables_delta_cents"] is not None:
        required.add("receivables_delta")
    if not required <= set(selection["fact_ids"]):
        raise ContractError("profit, cash and material risk facts must be surfaced")
    if set(selection["flag_ids"]) != set(allowed["required_flags"]):
        raise ContractError("all uncertainty and warning flags must be surfaced")
    if not selection["action_ids"] or not set(selection["action_ids"]) <= set(allowed["options"]):
        raise ContractError("unsupported or empty action options")
    if len(allowed["options"]) == 1 and selection["action_ids"] != list(allowed["options"]):
        raise ContractError("HOLD or zero headroom requires the designated action")
    return allowed


def warning_text(flag):
    messages = {
        "MARGIN_UNKNOWN": "Some sales or attributable costs are missing; estimated operating margin is unknown.",
        "UNKNOWN_VERIFIED_CASH_CENTS": "The current cash balance is unknown.",
        "UNKNOWN_DUE_LIABILITIES_CENTS": "The total unpaid obligations due within the horizon is unknown.",
        "UNKNOWN_COMMITTED_SPEND_CENTS": "Other committed spending has not been established.",
        "UNKNOWN_MINIMUM_BUFFER_CENTS": "The protected cash buffer has not been established.",
        "CASH_BASIS_UNCONFIRMED": "The cash position and obligation completeness still need your confirmation.",
        "MISSING_CASH_EVIDENCE": "The cash balance has no supporting evidence reference.",
        "STALE_CASH_SNAPSHOT": "The cash count is too old for this recorded decision time.",
        "POST_SNAPSHOT_TRANSACTION": "A transaction occurred after the cash snapshot; reconcile a fresh balance.",
        "DUPLICATE_TRANSACTION_ID": "Two transaction records share an identity; resolve the duplicate.",
        "UNCONFIRMED_TRANSACTION": "A transaction has not been confirmed.",
        "POSSIBLE_DUPLICATE_PAYMENT": "Payment records may refer to the same expense; check them before counting twice.",
        "CREDIT_SALES_NOT_CASH": "Uncollected credit sales are excluded from available cash.",
        "RECEIVABLES_RECONCILIATION_REQUIRED": "Credit collections exceed recorded credit sales; reconcile the customer balances.",
        "PROTECTED_CASH_DEFICIT": "Cash falls short of the recorded obligations and protected buffer.",
        "NO_DISCRETIONARY_HEADROOM": "There is no discretionary cash headroom within this horizon.",
        "UNRESOLVED:MISSING_RECEIPT": "A missing receipt prevents a complete cash assessment.",
        "UNRESOLVED:DUPLICATE_OR_OVERLAPPING_OBLIGATION": "The same obligation may be counted more than once.",
        "UNRESOLVED:OBLIGATIONS_INCOMPLETE": "The obligation list is not confirmed complete for this horizon.",
        "UNRESOLVED:UNCONFIRMED_OBLIGATION": "An obligation has not been confirmed.",
        "UNRESOLVED:UNKNOWN_OBLIGATION_AMOUNT": "An obligation or its paid amount is unknown.",
        "UNRESOLVED:OBLIGATION_OVERPAID": "A recorded payment exceeds its obligation; review the amounts.",
        "UNRESOLVED:PAYMENT_ALLOCATED_MORE_THAN_ONCE": "One payment is allocated to multiple obligations.",
        "UNRESOLVED:MISSING_OBLIGATION_PAYMENT": "A referenced payment record is missing.",
        "UNRESOLVED:OBLIGATION_PAYMENT_NOT_RECONCILED": "A payment does not match its obligation, confirmation or cutoff.",
        "UNRESOLVED:OBLIGATION_PAYMENT_TOTAL_MISMATCH": "The paid amount does not match its linked payment records.",
        "UNRESOLVED:UNALLOCATED_OBLIGATION_PAYMENT": "A payment is recorded but not allocated to its obligation.",
    }
    return messages.get(flag, "An unresolved record needs review before a cash decision.")


def render(summary, selection):
    allowed = validate_selection(summary, selection)
    lines = ["Spending assessment: HOLD — cash headroom is unknown." if summary["status"] != "CALCULATED" else "Calculation based on the confirmed inputs and recorded horizon."]
    for fact_id in selection["fact_ids"]:
        fact = allowed["facts"][fact_id]
        cents = fact["amount_cents"]
        sign = "-" if cents < 0 else ""
        value = abs(cents)
        lines.append(f"{fact['label']}: {sign}R{value // 100}.{value % 100:02d}")
    lines.extend(f"Check: {warning_text(flag)}" for flag in selection["flag_ids"])
    lines.extend(allowed["options"][action] for action in selection["action_ids"])
    return "\n".join(lines)
