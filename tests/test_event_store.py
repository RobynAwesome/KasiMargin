import tempfile
import unittest
from pathlib import Path

from kasimargin.engine import ContractError
from kasimargin.event_store import EventStore, IdempotencyConflict


def sale(event_id, key, amount=5000, payment_method="cash"):
    return {"id": event_id, "idempotency_key": key, "business_day": "2026-10-17", "event_type": "sale",
            "payment_method": payment_method, "amount_cents": amount,
            "occurred_at": "2026-10-17T09:00:00+02:00", "source_kind": "OPERATOR_REPORTED"}


class EventStoreContract(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "private-ledger.sqlite3"
        self.store = EventStore(self.path)

    def tearDown(self):
        self.directory.cleanup()

    def test_atomic_local_day_review_survives_restart(self):
        self.store.append(sale("sale-cash", "key-cash", 10000))
        self.store.append(sale("sale-card", "key-card", 5000, "card"))
        self.store.append({**sale("expense-cash", "key-expense", 2000), "event_type": "expense", "payment_method": "cash"})
        review = EventStore(self.path).current_day("2026-10-17")
        self.assertEqual({key: review[key] for key in ("recorded_sales_cents", "cash_sales_cents", "card_sales_cents", "cash_expenses_cents")},
                         {"recorded_sales_cents": 15000, "cash_sales_cents": 10000, "card_sales_cents": 5000, "cash_expenses_cents": 2000})
        self.assertEqual(review["cash_position_status"], "NOT_PREPARED")
        self.assertEqual(review["record_status"], "OPERATOR_REPORTED_RECORDS_MAY_BE_INCOMPLETE")

    def test_retry_is_idempotent_and_conflicting_retry_is_rejected(self):
        first = self.store.append(sale("sale-1", "same-key"))
        retry = self.store.append(sale("sale-1", "same-key"))
        self.assertFalse(first["idempotent_replay"])
        self.assertTrue(retry["idempotent_replay"])
        with self.assertRaises(IdempotencyConflict):
            self.store.append(sale("sale-1", "same-key", 6000))
        self.assertEqual(self.store.current_day("2026-10-17")["record_count"], 1)

    def test_correction_preserves_lineage_and_replaces_projection(self):
        original = self.store.append(sale("sale-1", "create-key"))
        corrected = self.store.correct({"id": "sale-1-revision-2", "idempotency_key": "correct-key", "replaces_id": original["id"],
                                        "expected_revision": 1, "amount_cents": 6000,
                                        "occurred_at": "2026-10-17T09:00:00+02:00", "reason": "amount corrected"})
        self.assertEqual(corrected["revision"], 2)
        self.assertEqual(corrected["replaces_id"], original["id"])
        self.assertEqual(self.store.current_day("2026-10-17")["recorded_sales_cents"], 6000)
        history = self.store.history(corrected["id"])
        self.assertEqual([(row["id"], row["is_current"]) for row in history], [("sale-1", 0), ("sale-1-revision-2", 1)])
        with self.assertRaises(IdempotencyConflict):
            self.store.correct({"id": "ignored", "idempotency_key": "stale-key", "replaces_id": "sale-1",
                                "expected_revision": 1, "amount_cents": 7000, "occurred_at": "2026-10-17T09:00:00+02:00", "reason": None})

    def test_unsupported_or_invalid_entry_never_creates_a_row(self):
        invalid = [
            {**sale("refund", "refund-key"), "event_type": "refund"},
            {**sale("card-expense", "expense-key"), "event_type": "expense", "payment_method": "card"},
            {**sale("too-large", "large-key"), "amount_cents": 9_007_199_254_740_992},
        ]
        for value in invalid:
            with self.subTest(value=value["id"]):
                with self.assertRaises(ContractError):
                    self.store.append(value)
        self.assertEqual(self.store.current_day("2026-10-17")["record_count"], 0)

    def test_database_constraint_rolls_back_a_conflicting_event_identifier(self):
        self.store.append(sale("sale-1", "first-key"))
        with self.assertRaises(ContractError):
            self.store.append(sale("sale-1", "different-key", 6000))
        review = self.store.current_day("2026-10-17")
        self.assertEqual(review["record_count"], 1)
        self.assertEqual(review["recorded_sales_cents"], 5000)
