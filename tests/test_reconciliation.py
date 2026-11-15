from pathlib import Path
import sqlite3
import tempfile
import unittest

from kasimargin.engine import ContractError
from kasimargin.event_store import EventNotFoundError, EventStore, MAX_BROWSER_CENTS
from kasimargin.reconciliation import reconcile_day


def _seed_barber_day(store):
    store.append(
        {
            "id": "sale-cash-1",
            "idempotency_key": "k1",
            "business_day": "2026-10-17",
            "event_type": "sale",
            "payment_method": "cash",
            "amount_cents": 5000,
            "occurred_at": "2026-10-17T09:10:00+02:00",
            "source_kind": "OPERATOR_REPORTED",
        }
    )
    store.append(
        {
            "id": "sale-cash-2",
            "idempotency_key": "k2",
            "business_day": "2026-10-17",
            "event_type": "sale",
            "payment_method": "cash",
            "amount_cents": 5000,
            "occurred_at": "2026-10-17T10:10:00+02:00",
            "source_kind": "OPERATOR_REPORTED",
        }
    )
    store.append(
        {
            "id": "sale-card-1",
            "idempotency_key": "k3",
            "business_day": "2026-10-17",
            "event_type": "sale",
            "payment_method": "card",
            "amount_cents": 5000,
            "occurred_at": "2026-10-17T11:10:00+02:00",
            "source_kind": "OPERATOR_REPORTED",
        }
    )
    store.append(
        {
            "id": "expense-cash-1",
            "idempotency_key": "k4",
            "business_day": "2026-10-17",
            "event_type": "expense",
            "payment_method": "cash",
            "amount_cents": 2000,
            "occurred_at": "2026-10-17T12:10:00+02:00",
            "source_kind": "OPERATOR_REPORTED",
        }
    )
    store.correct(
        {
            "id": "sale-cash-2-rev2",
            "idempotency_key": "k5",
            "replaces_id": "sale-cash-2",
            "expected_revision": 1,
            "amount_cents": 6000,
            "occurred_at": "2026-10-17T10:10:00+02:00",
            "reason": "Corrected haircut price from R50 to R60",
        }
    )
    return store.current_day("2026-10-17")


class ReconciliationAndStoreContract(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.directory.name) / "ledger.sqlite3"
        self.store = EventStore(self.db_path)

    def tearDown(self):
        self.directory.cleanup()

    def test_synthetic_barber_day_surfaces_minus_r10_drawer_discrepancy_and_unverified_card(self):
        day = _seed_barber_day(self.store)
        self.assertEqual(day["recorded_sales_cents"], 16000)
        self.assertEqual(day["cash_sales_cents"], 11000)
        self.assertEqual(day["card_sales_cents"], 5000)
        self.assertEqual(day["cash_expenses_cents"], 2000)

        report = reconcile_day(
            day,
            {
                "opening_cash_float_cents": 5000,
                "closing_cash_counted_cents": 13000,
                "cash_movements_complete": True,
                "settled_card_cents": None,
                "card_settlement_confirmed": False,
            },
        )
        self.assertEqual(report["source_kind"], "OPERATOR_REPORTED")
        self.assertEqual(report["cash_position_status"], "NOT_VERIFIED_BANK_OR_LEDGER_AUTO_FILL")
        self.assertFalse(report["auto_populate_permitted"])
        self.assertEqual(report["net_cash_movement_cents"], 9000)
        self.assertEqual(report["expected_closing_cash_cents"], 14000)
        self.assertEqual(report["cash_variance_cents"], -1000)
        self.assertIsNone(report["card_variance_cents"])
        self.assertEqual(report["status"], "HOLD_INCOMPLETE_RECONCILIATION")
        self.assertEqual(
            report["flags"],
            [
                "CASH_DRAWER_DISCREPANCY",
                "CARD_SALES_UNVERIFIED_UNTIL_SETTLED",
                "CASH_EXPENSE_NOT_AUTOMATICALLY_ATTRIBUTABLE_COST",
            ],
        )
        self.assertNotIn("verified_cash_cents", report)
        # Re-read stored day to guarantee reconcile_day performed zero writes.
        self.assertEqual(self.store.current_day("2026-10-17"), day)

    def test_exact_match_after_settled_card_stays_operator_reported(self):
        day = _seed_barber_day(self.store)
        report = reconcile_day(
            day,
            {
                "opening_cash_float_cents": 5000,
                "closing_cash_counted_cents": 14000,
                "cash_movements_complete": True,
                "settled_card_cents": 5000,
                "card_settlement_confirmed": True,
            },
        )
        self.assertEqual(report["status"], "RECONCILED_OPERATOR_REPORTED")
        self.assertEqual(report["cash_variance_cents"], 0)
        self.assertEqual(report["card_variance_cents"], 0)
        self.assertEqual(report["flags"], ["CASH_EXPENSE_NOT_AUTOMATICALLY_ATTRIBUTABLE_COST"])

    def test_discrepancy_with_settled_card_requires_review_before_check(self):
        day = _seed_barber_day(self.store)
        report = reconcile_day(
            day,
            {
                "opening_cash_float_cents": 5000,
                "closing_cash_counted_cents": 13000,
                "cash_movements_complete": True,
                "settled_card_cents": 4850,
                "card_settlement_confirmed": True,
            },
        )
        self.assertEqual(report["status"], "REVIEW_DISCREPANCY_BEFORE_CHECK")
        self.assertEqual(report["cash_variance_cents"], -1000)
        self.assertEqual(report["card_variance_cents"], -150)
        self.assertIn("CASH_DRAWER_DISCREPANCY", report["flags"])
        self.assertIn("CARD_SETTLEMENT_MISMATCH", report["flags"])

    def test_incomplete_movements_or_missing_counts_stay_unknown_and_hold(self):
        day = _seed_barber_day(self.store)
        report = reconcile_day(
            day,
            {
                "opening_cash_float_cents": 5000,
                "closing_cash_counted_cents": 13000,
                "cash_movements_complete": False,
                "settled_card_cents": None,
                "card_settlement_confirmed": False,
            },
        )
        self.assertEqual(report["status"], "HOLD_INCOMPLETE_RECONCILIATION")
        self.assertIsNone(report["expected_closing_cash_cents"])
        self.assertIsNone(report["cash_variance_cents"])
        self.assertIn("HOLD_INCOMPLETE_CASH_MOVEMENTS", report["flags"])

        missing_counts = reconcile_day(
            day,
            {
                "opening_cash_float_cents": None,
                "closing_cash_counted_cents": None,
                "cash_movements_complete": True,
                "settled_card_cents": None,
                "card_settlement_confirmed": False,
            },
        )
        self.assertEqual(missing_counts["status"], "HOLD_INCOMPLETE_RECONCILIATION")
        self.assertIsNone(missing_counts["expected_closing_cash_cents"])
        self.assertIn("MISSING_OPENING_FLOAT", missing_counts["flags"])
        self.assertIn("MISSING_CLOSING_CASH_COUNT", missing_counts["flags"])

    def test_rejects_booleans_or_negative_amounts_and_preserves_not_found_distinction(self):
        day = _seed_barber_day(self.store)
        for bad_float in (True, -100, 12.5, "5000"):
            with self.subTest(bad_float=bad_float):
                with self.assertRaises(ContractError):
                    reconcile_day(
                        day,
                        {
                            "opening_cash_float_cents": bad_float,
                            "closing_cash_counted_cents": 14000,
                            "cash_movements_complete": True,
                            "settled_card_cents": 5000,
                            "card_settlement_confirmed": True,
                        },
                    )

        with self.assertRaises(EventNotFoundError):
            self.store.history("missing-event-id")
        with self.assertRaises(ContractError) as ctx:
            self.store.history(" ")
        self.assertNotIsInstance(ctx.exception, EventNotFoundError)

        # Verify large exact integers stay intact at SQLite level while MAX_BROWSER_CENTS constant remains defined.
        self.assertEqual(MAX_BROWSER_CENTS, 9_007_199_254_740_991)
        conn = self.store._connect()
        try:
            busy_timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
            self.assertEqual(busy_timeout, 5000)
        finally:
            conn.close()
