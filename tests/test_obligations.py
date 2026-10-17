import copy
import json
from pathlib import Path
import unittest
from kasimargin.engine import calculate, ContractError

ROOT = Path(__file__).resolve().parents[1]


def request():
    return json.loads((ROOT / "fixtures/itemized/01.json").read_text())["input"]


class Obligations(unittest.TestCase):
    def test_partial_payment_is_subtracted_only_once(self):
        result = calculate(request())
        self.assertEqual(result["cash_headroom_cents"], 40000)
        self.assertEqual(result["cash_basis"]["due_liabilities_cents"], 30000)

    def test_duplicate_reference_across_buckets_holds(self):
        value = request()
        value["obligations"][1]["reference_id"] = value["obligations"][0]["reference_id"]
        result = calculate(value)
        self.assertIsNone(result["cash_headroom_cents"])
        self.assertIn("UNRESOLVED:DUPLICATE_OR_OVERLAPPING_OBLIGATION", result["blocking_flags"])

    def test_missing_or_unconfirmed_obligations_hold(self):
        mutations = [lambda v: v["cash_position"].update(obligations_complete=False), lambda v: v["obligations"][0].update(is_confirmed=False), lambda v: v["obligations"][0].update(amount_cents=None), lambda v: v["obligations"][0].update(paid_cents=None)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                value = request(); mutation(value)
                self.assertIsNone(calculate(value)["cash_headroom_cents"])

    def test_cash_evidence_cannot_be_replaced_by_invoice_evidence(self):
        value = request(); value["cash_position"]["evidence_refs"] = []
        result = calculate(value)
        self.assertIn("MISSING_CASH_EVIDENCE", result["blocking_flags"])
        self.assertIsNone(result["cash_headroom_cents"])
        self.assertEqual(result["status"], "HOLD_INSUFFICIENT_DATA")

    def test_unconfirmed_cash_basis_holds_despite_populated_entries(self):
        value = request()
        value["cash_position"]["basis_confirmed"] = False
        result = calculate(value)
        self.assertIn("CASH_BASIS_UNCONFIRMED", result["blocking_flags"])
        self.assertIsNone(result["cash_headroom_cents"])
        self.assertEqual(result["status"], "HOLD_INSUFFICIENT_DATA")

    def test_future_obligation_excluded_and_overdue_included(self):
        value = request()
        value["obligations"][0]["due_at"] = "2026-10-20T12:00:00+02:00"
        self.assertEqual(calculate(value)["cash_headroom_cents"], 70000)
        value["obligations"][0]["due_at"] = "2026-10-01T12:00:00+02:00"
        self.assertEqual(calculate(value)["cash_headroom_cents"], 40000)

    def test_paid_obligation_not_subtracted_again(self):
        value = request()
        value["obligations"][0]["amount_cents"] = 10000
        self.assertEqual(calculate(value)["cash_headroom_cents"], 70000)

    def test_payment_must_match_amount_reference_and_snapshot(self):
        mutations = [lambda v: v["obligations"][0].update(paid_cents=5000), lambda v: v["transactions"][0].update(reference_id="other:invoice"), lambda v: v["transactions"][0].update(timestamp="2026-10-13T18:01:00+02:00"), lambda v: v["transactions"][0].update(kind="cash_sale"), lambda v: v.update(transactions=[])]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                value = request(); mutation(value)
                self.assertIsNone(calculate(value)["cash_headroom_cents"])

    def test_one_payment_cannot_resolve_two_obligations(self):
        value = request()
        value["obligations"][1].update(paid_cents=10000, payment_transaction_ids=["payment-1"])
        self.assertIn("UNRESOLVED:PAYMENT_ALLOCATED_MORE_THAN_ONCE", calculate(value)["blocking_flags"])

    def test_unallocated_payment_prevents_double_subtraction(self):
        value = request()
        value["obligations"][0].update(paid_cents=0, payment_transaction_ids=[])
        self.assertIn("UNRESOLVED:UNALLOCATED_OBLIGATION_PAYMENT", calculate(value)["blocking_flags"])

    def test_overpayment_duplicate_ids_and_invalid_types(self):
        value = request(); value["obligations"][0]["paid_cents"] = 50000
        self.assertIsNone(calculate(value)["cash_headroom_cents"])
        value = request(); value["obligations"][1]["id"] = "invoice-1"
        self.assertIsNone(calculate(value)["cash_headroom_cents"])
        for key, bad in (("bucket", []), ("paid_cents", True), ("is_confirmed", "yes"), ("id", " invoice-1 ")):
            with self.subTest(key=key):
                value = request(); value["obligations"][0][key] = bad
                with self.assertRaises(ContractError): calculate(value)

    def test_payment_reference_reuse_across_transaction_kinds_holds(self):
        value = request()
        second = copy.deepcopy(value["transactions"][0]); second.update(id="payment-2",kind="operating_payment")
        value["transactions"].append(second)
        self.assertIn("POSSIBLE_DUPLICATE_PAYMENT", calculate(value)["blocking_flags"])
