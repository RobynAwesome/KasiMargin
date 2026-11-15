from copy import deepcopy
from http.client import HTTPConnection
import json
from pathlib import Path
import sqlite3
import tempfile
from threading import Thread
import unittest

from kasimargin.engine import ContractError, calculate
from kasimargin.event_store import EventStore, MAX_BROWSER_CENTS
from kasimargin.governance import evaluate_ccp_ecv_01, kmec_observations, reveal_envelope
from kasimargin.kpgs import LocalKpgs
from kasimargin.obligations import prepare_request
from kasimargin.ollama import LocalOllama
from kasimargin.server import create_app, make_server

ROOT = Path(__file__).resolve().parents[1]


class GovernanceAndServerExtensions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.ledger_path = Path(cls.directory.name) / "ledger.sqlite3"
        cls.server = make_server(0, cls.directory.name, cls.ledger_path)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        conn = HTTPConnection("127.0.0.1", cls.server.server_port, timeout=5)
        conn.request("GET", "/api/session")
        cls.token = json.loads(conn.getresponse().read())["token"]
        conn.close()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.directory.cleanup()

    def call(self, method, path, value=None, headers=None):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        body = None if value is None else json.dumps(value)
        conn.request(
            method,
            path,
            body=body,
            headers={"Content-Type": "application/json", "X-KasiMargin-Session": self.token, **(headers or {})},
        )
        res = conn.getresponse()
        data = res.read()
        status = res.status
        conn.close()
        return status, data

    def test_ccp_ecv_01_enforces_maybe_hold_when_unmeasured(self):
        gate = evaluate_ccp_ecv_01(0)
        self.assertEqual(gate["gate_id"], "CCP-ECV-01")
        self.assertEqual(gate["economic_gate_state"], "MAYBE_HOLD")
        self.assertEqual(gate["measurement_status"], "UNMEASURED_NO_OPERATOR_TRIAL")
        self.assertFalse(gate["gemma_value_proven"])
        self.assertFalse(gate["eligible_to_claim_value"])
        self.assertTrue(gate["owner_approval_required"])

        small_sample = evaluate_ccp_ecv_01(12)
        self.assertEqual(small_sample["economic_gate_state"], "MAYBE_HOLD")
        self.assertEqual(small_sample["measurement_status"], "INSUFFICIENT_SAMPLE")

        safety_fail = evaluate_ccp_ecv_01(
            30,
            control_comprehension_accuracy=0.60,
            treatment_comprehension_accuracy=0.90,
            safety_regressions=1,
            p_value=0.01,
        )
        self.assertEqual(safety_fail["economic_gate_state"], "HOLD_SAFETY_REGRESSION")
        self.assertFalse(safety_fail["eligible_to_claim_value"])

        non_significant = evaluate_ccp_ecv_01(
            30,
            control_comprehension_accuracy=0.60,
            treatment_comprehension_accuracy=0.70,
            safety_regressions=0,
            p_value=0.12,
        )
        self.assertEqual(non_significant["economic_gate_state"], "REJECT_NO_NET_BENEFIT")
        self.assertFalse(non_significant["eligible_to_claim_value"])

    def test_reveal_envelope_and_adapter_boundary_never_grant_write_authority(self):
        env = reveal_envelope("RESULT", ui_class="REVEAL", receipt_sha256="a" * 64, owner_approval_required=True)
        self.assertEqual(env["ledger_write_authority"], "NONE")
        self.assertEqual(env["purchase_authority"], "NONE")
        self.assertEqual(env["merge_authority"], "NONE")

        with self.assertRaises(ContractError):
            reveal_envelope("RESULT", ledger_write_authority="WRITE")
        with self.assertRaises(ContractError):
            reveal_envelope("UNKNOWN_STAGE")

        # Verify Ollama and KPGS classes expose no ledger-write methods.
        self.assertFalse(hasattr(LocalOllama(), "append"))
        self.assertFalse(hasattr(LocalOllama(), "correct"))
        self.assertFalse(hasattr(LocalKpgs, "append"))
        self.assertFalse(hasattr(LocalKpgs, "correct"))

    def test_kmec_observations_confirm_integer_cents_and_ledger_isolation(self):
        fixture = json.loads((ROOT / "fixtures/itemized/01.json").read_text())["input"]
        summary = calculate(prepare_request(fixture))
        day = EventStore(self.ledger_path).current_day("2026-10-17")
        obs = kmec_observations(summary, ledger_day=day)
        self.assertTrue(obs["passed"])
        self.assertTrue(obs["integer_cents_exact"])
        self.assertTrue(obs["ledger_isolated_from_cash_basis"])

        bad = deepcopy(summary)
        bad["cash_headroom_cents"] = 100.5
        with self.assertRaises(ContractError):
            kmec_observations(bad)

    def test_duplicate_transaction_id_not_double_flagged_in_v2_and_whitespace_payment_caught_in_v1(self):
        v2 = json.loads((ROOT / "fixtures/itemized/01.json").read_text())["input"]
        dup_v2 = deepcopy(v2)
        tx = deepcopy(dup_v2["transactions"][0])
        dup_v2["transactions"].append(tx)
        summary_v2 = calculate(prepare_request(dup_v2))
        self.assertIn("DUPLICATE_TRANSACTION_ID", summary_v2["flags"])
        self.assertNotIn("UNRESOLVED:DUPLICATE_TRANSACTION_ID", summary_v2["flags"])

        v1 = deepcopy(json.loads((ROOT / "fixtures/01.json").read_text())["input"])
        v1["transactions"] = [
            {
                "id": "pay-1",
                "kind": "supplier_payment",
                "amount_cents": 5000,
                "reference_id": "inv-42",
                "timestamp": v1["cash_position"]["snapshot_at"],
                "source_description": "First",
                "is_confirmed": True,
            },
            {
                "id": "pay-2",
                "kind": "supplier_payment",
                "amount_cents": 5000,
                "reference_id": "inv-42 ",
                "timestamp": v1["cash_position"]["snapshot_at"],
                "source_description": "Whitespace-padded ref",
                "is_confirmed": True,
            },
        ]
        summary_v1 = calculate(v1)
        self.assertIn("POSSIBLE_DUPLICATE_PAYMENT", summary_v1["blocking_flags"])

    def test_ledger_history_reconcile_and_browser_range_routes(self):
        # Missing session header rejected cleanly on new endpoints.
        self.assertEqual(self.call("GET", "/api/ledger/events/ev-1/history", headers={"X-KasiMargin-Session": ""})[0], 403)
        self.assertEqual(self.call("POST", "/api/ledger/reconcile", value={}, headers={"X-KasiMargin-Session": ""})[0], 403)

        # 404 for unknown event, 400 for malformed ID.
        self.assertEqual(self.call("GET", "/api/ledger/events/does-not-exist/history")[0], 404)
        self.assertEqual(self.call("GET", "/api/ledger/events/%20bad-id/history")[0], 400)

        # Record + correct a barber cash sale, verify HTTP history chain & read-only reconciliation.
        status, _ = self.call(
            "POST",
            "/api/ledger/events",
            {
                "id": "barber-sale-1",
                "idempotency_key": "bk1",
                "business_day": "2026-10-18",
                "event_type": "sale",
                "payment_method": "cash",
                "amount_cents": 5000,
                "occurred_at": "2026-10-18T10:00:00+02:00",
                "source_kind": "OPERATOR_REPORTED",
            },
        )
        self.assertEqual(status, 200)
        status, _ = self.call(
            "POST",
            "/api/ledger/corrections",
            {
                "id": "barber-sale-1-v2",
                "idempotency_key": "bk2",
                "replaces_id": "barber-sale-1",
                "expected_revision": 1,
                "amount_cents": 6000,
                "occurred_at": "2026-10-18T10:00:00+02:00",
                "reason": "Updated price",
            },
        )
        self.assertEqual(status, 200)

        hist_status, hist_raw = self.call("GET", "/api/ledger/events/barber-sale-1-v2/history")
        self.assertEqual(hist_status, 200)
        hist = json.loads(hist_raw)
        self.assertEqual(hist["count"], 2)
        self.assertEqual([item["amount_cents"] for item in hist["history"]], [5000, 6000])

        rec_status, rec_raw = self.call(
            "POST",
            "/api/ledger/reconcile",
            {
                "business_day": "2026-10-18",
                "opening_cash_float_cents": 5000,
                "closing_cash_counted_cents": 10000,
                "cash_movements_complete": True,
                "settled_card_cents": 0,
                "card_settlement_confirmed": True,
            },
        )
        self.assertEqual(rec_status, 200)
        report = json.loads(rec_raw)
        self.assertEqual(report["expected_closing_cash_cents"], 11000)
        self.assertEqual(report["cash_variance_cents"], -1000)
        self.assertEqual(report["status"], "REVIEW_DISCREPANCY_BEFORE_CHECK")
        self.assertFalse(report["auto_populate_permitted"])

        # Ledger day sum exceeding browser range must be rejected with 400 (never silently rounded in JS).
        huge_day = "2026-10-19"
        store = EventStore(self.ledger_path)
        store.append(
            {
                "id": "huge-1",
                "idempotency_key": "hk1",
                "business_day": huge_day,
                "event_type": "sale",
                "payment_method": "cash",
                "amount_cents": MAX_BROWSER_CENTS,
                "occurred_at": "2026-10-19T10:00:00+02:00",
                "source_kind": "OPERATOR_REPORTED",
            }
        )
        store.append(
            {
                "id": "huge-2",
                "idempotency_key": "hk2",
                "business_day": huge_day,
                "event_type": "sale",
                "payment_method": "cash",
                "amount_cents": 100,
                "occurred_at": "2026-10-19T10:05:00+02:00",
                "source_kind": "OPERATOR_REPORTED",
            }
        )
        overflow_status, _ = self.call("GET", f"/api/ledger/days/{huge_day}")
        self.assertEqual(overflow_status, 400)
        overflow_rec_status, _ = self.call(
            "POST",
            "/api/ledger/reconcile",
            {
                "business_day": huge_day,
                "opening_cash_float_cents": 0,
                "closing_cash_counted_cents": 0,
                "cash_movements_complete": True,
                "settled_card_cents": None,
                "card_settlement_confirmed": False,
            },
        )
        self.assertEqual(overflow_rec_status, 400)
