import copy
import json
from pathlib import Path
import unittest
from kasimargin.engine import calculate, ContractError
from kasimargin.explanations import catalogue, render

ROOT = Path(__file__).resolve().parents[1]


def fixture(number="01"):
    return json.loads((ROOT / "fixtures" / f"{number}.json").read_text())


def selection(summary):
    allowed = catalogue(summary)
    return {"fact_ids": list(allowed["facts"]), "flag_ids": allowed["required_flags"], "action_ids": list(allowed["options"])}


class Acceptance(unittest.TestCase):
    def test_six_acceptance_fixtures(self):
        for path in sorted((ROOT / "fixtures").glob("*.json")):
            case = json.loads(path.read_text())
            with self.subTest(case=case["fixture_id"]):
                result = calculate(case["input"])
                for key, expected in case["expected"].items():
                    self.assertEqual(result[key], expected, key)
                self.assertIsInstance(render(result, selection(result)), str)

    def test_each_unknown_cash_component_holds(self):
        for key in ("verified_cash_cents", "due_liabilities_cents", "committed_spend_cents", "minimum_buffer_cents"):
            with self.subTest(key=key):
                request = fixture()["input"]
                request["cash_position"][key] = None
                result = calculate(request)
                self.assertIsNone(result["cash_headroom_cents"])
                self.assertEqual(result["status"], "HOLD_INSUFFICIENT_DATA")

    def test_profit_and_cash_are_independent(self):
        request = fixture("02")["input"]
        request["cash_position"]["verified_cash_cents"] = 100000
        result = calculate(request)
        self.assertEqual(result["operating_margin_cents"], 1000)
        self.assertEqual(result["cash_headroom_cents"], 91000)
        request["performance"]["attributable_costs_cents"] = 130000
        self.assertEqual(calculate(request)["cash_headroom_cents"], 91000)

    def test_unknown_margin_does_not_hide_independently_confirmed_cash(self):
        request = fixture()["input"]
        request["performance"]["attributable_costs_cents"] = None
        result = calculate(request)
        self.assertIsNone(result["operating_margin_cents"])
        self.assertEqual(result["cash_headroom_cents"], 40000)
        self.assertIn("MARGIN_UNKNOWN", result["flags"])

    def test_snapshot_not_double_counted(self):
        request = fixture()["input"]
        request["transactions"] = [
            {"id": "s1", "kind": "cash_sale", "amount_cents": 180000, "is_confirmed": True, "reference_id": "r1", "timestamp": "2026-10-13T17:00:00+02:00", "source_description": "cash already in snapshot"},
            {"id": "p1", "kind": "supplier_payment", "amount_cents": 50000, "is_confirmed": True, "reference_id": "supplier:invoice-1", "timestamp": "2026-10-13T17:01:00+02:00", "source_description": "paid before snapshot"},
        ]
        self.assertEqual(calculate(request)["cash_headroom_cents"], 40000)

    def test_stale_snapshot_holds(self):
        request = fixture()["input"]
        request["cash_position"]["decision_at"] = "2026-10-13T19:00:00+02:00"
        self.assertIn("STALE_CASH_SNAPSHOT", calculate(request)["blocking_flags"])

    def test_invalid_money_is_rejected(self):
        for bad in (True, 1.5, "100", -1):
            with self.subTest(bad=bad):
                request = fixture()["input"]
                request["cash_position"]["verified_cash_cents"] = bad
                with self.assertRaises(ContractError):
                    calculate(request)

    def test_timezone_and_horizon_required(self):
        for bad in ("2026-10-13T18:00:00", "not-a-time", "2026-10-13T20:00:00+02:00"):
            with self.subTest(bad=bad):
                request = fixture()["input"]
                request["cash_position"]["snapshot_at"] = bad
                with self.assertRaises(ContractError):
                    calculate(request)

    def test_duplicate_id_holds(self):
        request = fixture("05")["input"]
        request["transactions"].append(copy.deepcopy(request["transactions"][0]))
        self.assertIn("DUPLICATE_TRANSACTION_ID", calculate(request)["blocking_flags"])

    def test_post_snapshot_transaction_holds(self):
        request = fixture("05")["input"]
        request["transactions"][0]["timestamp"] = "2026-10-13T18:01:00+02:00"
        self.assertIn("POST_SNAPSHOT_TRANSACTION", calculate(request)["blocking_flags"])

    def test_free_text_and_unauthorized_facts_are_rejected(self):
        summary = calculate(fixture()["input"])
        for mutation in ({"explanation_text": "Spend R9999 now"}, {"fact_ids": ["supplier_price"]}, {"action_ids": ["buy_now"]}):
            chosen = selection(summary)
            chosen.update(mutation)
            with self.assertRaises(ContractError):
                render(summary, chosen)

    def test_hold_and_zero_cannot_offer_spending(self):
        for number in ("02", "03", "04", "06"):
            with self.subTest(number=number):
                summary = calculate(fixture(number)["input"])
                chosen = selection(summary)
                chosen["action_ids"] = ["compare_restock_quote"]
                with self.assertRaises(ContractError):
                    render(summary, chosen)

    def test_warning_omission_is_rejected(self):
        summary = calculate(fixture("05")["input"])
        chosen = selection(summary)
        chosen["flag_ids"] = []
        with self.assertRaises(ContractError):
            render(summary, chosen)

    def test_cash_fact_omission_is_rejected(self):
        summary = calculate(fixture()["input"])
        chosen = selection(summary)
        chosen["fact_ids"] = ["operating_margin"]
        with self.assertRaises(ContractError):
            render(summary, chosen)

    def test_integer_cents_render_without_float_rounding(self):
        request = fixture()["input"]
        request["cash_position"]["verified_cash_cents"] = 100001
        summary = calculate(request)
        self.assertIn("R400.01", render(summary, selection(summary)))

    def test_known_profit_and_credit_context_cannot_be_hidden(self):
        summary = calculate(fixture("05")["input"])
        for fact in ("operating_margin", "receivables_delta"):
            with self.subTest(fact=fact):
                chosen = selection(summary)
                chosen["fact_ids"].remove(fact)
                with self.assertRaises(ContractError): render(summary, chosen)


if __name__ == "__main__":
    unittest.main()
