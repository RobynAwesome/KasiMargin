"""Read-only reconciliation of operator-reported daily records against physical counts."""
from .engine import ContractError, exact_keys, money

FLAG_CHECKS = {
    "MISSING_OPENING_FLOAT": "Enter the opening drawer float from when the business day started.",
    "MISSING_CLOSING_CASH_COUNT": "Count the physical cash in the drawer at closing before judging cash available.",
    "HOLD_INCOMPLETE_CASH_MOVEMENTS": "Confirm whether every cash sale and cash expense for the day has been recorded.",
    "CASH_DRAWER_DISCREPANCY": "Counted closing cash does not match opening float plus recorded cash movement; check missing change, unrecorded payouts or misrecorded amounts.",
    "CARD_SALES_UNVERIFIED_UNTIL_SETTLED": "Recorded card sales are operator-reported and excluded from drawer cash until card settlement is checked.",
    "CARD_SETTLEMENT_MISMATCH": "Confirmed card settlement differs from recorded card sales; check batch totals or fees.",
    "CASH_EXPENSE_NOT_AUTOMATICALLY_ATTRIBUTABLE_COST": "Recorded cash spending stays separate until you decide which costs belong to your decision horizon.",
}


def _day_money(day_summary, key):
    value = day_summary.get(key)
    if type(value) is not int or value < 0:
        raise ContractError(f"day summary {key} must be a non-negative integer")
    return value


def _flag_reason(flag):
    return FLAG_CHECKS[flag]


def reconcile_day(day_summary, check):
    """Compare operator-reported totals with physical drawer counts without writing ledger or cash_position."""
    if not isinstance(day_summary, dict):
        raise ContractError("day summary must be an object")
    day = day_summary.get("business_day")
    if not isinstance(day, str) or len(day) != 10:
        raise ContractError("day summary business_day must be an ISO date")
    if day_summary.get("cash_position_status") != "NOT_PREPARED":
        raise ContractError("reconciliation requires unprepared operator-reported day summary")

    exact_keys(
        check,
        {
            "opening_cash_float_cents",
            "closing_cash_counted_cents",
            "cash_movements_complete",
            "settled_card_cents",
            "card_settlement_confirmed",
        },
        "reconciliation check",
    )
    if type(check["cash_movements_complete"]) is not bool:
        raise ContractError("cash_movements_complete must be boolean")
    if type(check["card_settlement_confirmed"]) is not bool:
        raise ContractError("card_settlement_confirmed must be boolean")

    opening_float = money(check["opening_cash_float_cents"], "opening_cash_float_cents")
    closing_counted = money(check["closing_cash_counted_cents"], "closing_cash_counted_cents")
    settled_card = money(check["settled_card_cents"], "settled_card_cents")

    recorded_sales = _day_money(day_summary, "recorded_sales_cents")
    cash_sales = _day_money(day_summary, "cash_sales_cents")
    card_sales = _day_money(day_summary, "card_sales_cents")
    cash_expenses = _day_money(day_summary, "cash_expenses_cents")
    record_count = _day_money(day_summary, "record_count")

    net_cash_movement = cash_sales - cash_expenses
    complete_cash = check["cash_movements_complete"]

    flags = []
    if opening_float is None:
        flags.append("MISSING_OPENING_FLOAT")
    if closing_counted is None:
        flags.append("MISSING_CLOSING_CASH_COUNT")
    if not complete_cash:
        flags.append("HOLD_INCOMPLETE_CASH_MOVEMENTS")

    # Never assume missing cash movements are zero when computing expected closing cash.
    if complete_cash and opening_float is not None:
        expected_closing = opening_float + net_cash_movement
        cash_variance = None if closing_counted is None else closing_counted - expected_closing
    else:
        expected_closing = None
        cash_variance = None

    if cash_variance is not None and cash_variance != 0:
        flags.append("CASH_DRAWER_DISCREPANCY")

    card_variance = None if settled_card is None else settled_card - card_sales
    if card_sales > 0 and (not check["card_settlement_confirmed"] or settled_card is None):
        flags.append("CARD_SALES_UNVERIFIED_UNTIL_SETTLED")
    if settled_card is not None and settled_card != card_sales:
        flags.append("CARD_SETTLEMENT_MISMATCH")

    if cash_expenses > 0:
        flags.append("CASH_EXPENSE_NOT_AUTOMATICALLY_ATTRIBUTABLE_COST")

    missing_or_incomplete = (
        opening_float is None
        or closing_counted is None
        or not complete_cash
        or (card_sales > 0 and not check["card_settlement_confirmed"])
        or (card_sales > 0 and settled_card is None)
    )
    discrepancy = (cash_variance is not None and cash_variance != 0) or (card_variance is not None and card_variance != 0)

    if missing_or_incomplete:
        status = "HOLD_INCOMPLETE_RECONCILIATION"
    elif discrepancy:
        status = "REVIEW_DISCREPANCY_BEFORE_CHECK"
    else:
        status = "RECONCILED_OPERATOR_REPORTED"

    return {
        "schema_version": "kasimargin-reconciliation-v1",
        "business_day": day,
        "source_kind": "OPERATOR_REPORTED",
        "cash_position_status": "NOT_VERIFIED_BANK_OR_LEDGER_AUTO_FILL",
        "auto_populate_permitted": False,
        "record_count": record_count,
        "recorded_sales_cents": recorded_sales,
        "cash_sales_cents": cash_sales,
        "card_sales_cents": card_sales,
        "cash_expenses_cents": cash_expenses,
        "net_cash_movement_cents": net_cash_movement,
        "opening_cash_float_cents": opening_float,
        "closing_cash_counted_cents": closing_counted,
        "expected_closing_cash_cents": expected_closing,
        "cash_variance_cents": cash_variance,
        "settled_card_cents": settled_card,
        "card_variance_cents": card_variance,
        "cash_movements_complete": complete_cash,
        "card_settlement_confirmed": check["card_settlement_confirmed"],
        "status": status,
        "flags": flags,
        "checks": [_flag_reason(flag) for flag in flags],
    }
