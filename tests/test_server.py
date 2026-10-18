from http.client import HTTPConnection
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from kasimargin.server import make_server, create_app
from kasimargin.receipts import verify

ROOT = Path(__file__).resolve().parents[1]


class LocalDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.server = make_server(0, cls.directory.name, Path(cls.directory.name) / "ledger.sqlite3")
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        connection = HTTPConnection("127.0.0.1", cls.server.server_port, timeout=5)
        connection.request("GET", "/api/session")
        cls.token = json.loads(connection.getresponse().read())["token"]
        connection.close()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(); cls.directory.cleanup()

    def call(self, method, path, value=None, headers=None, raw=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        body = raw if raw is not None else None if value is None else json.dumps(value)
        connection.request(method, path, body=body, headers={"Content-Type":"application/json", "X-KasiMargin-Session":self.token, **(headers or {})})
        response = connection.getresponse(); data = response.read(); status = response.status; reply_headers = dict(response.getheaders()); connection.close()
        return status, data, reply_headers

    def payload(self):
        return {"input":json.loads((ROOT / "fixtures/itemized/01.json").read_text())["input"],"model":None,"save_receipt":False,"data_class":"SYNTHETIC"}

    def test_assets_and_fixtures_are_served_without_external_dependencies(self):
        for path in ("/", "/app.js", "/presentation.js", "/ledger.js", "/style.css", "/health"):
            with self.subTest(path=path):
                status, data, headers = self.call("GET", path)
                self.assertEqual(status, 200); self.assertTrue(data)
                self.assertEqual(headers["Cache-Control"], "no-store")
                self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        status, data, _ = self.call("GET", "/api/fixtures")
        self.assertEqual(status, 200); self.assertEqual(len(json.loads(data)), 7)
        self.assertEqual(self.call("GET", "/../.git/config")[0], 404)

    def test_calculation_is_read_only_unless_save_is_explicit(self):
        before = set(Path(self.directory.name).iterdir())
        status, data, _ = self.call("POST", "/api/decision", self.payload())
        self.assertEqual(status, 200); self.assertEqual(json.loads(data)["summary"]["cash_headroom_cents"], 40000)
        self.assertEqual(set(Path(self.directory.name).iterdir()), before)
        payload = self.payload(); payload["save_receipt"] = True
        status, data, _ = self.call("POST", "/api/decision", payload)
        self.assertEqual(status, 200)
        self.assertEqual(verify(Path(self.directory.name) / json.loads(data)["receipt_filename"])["status"], "REPRODUCED")

    def test_local_ledger_requires_session_and_preserves_reviewable_lineage(self):
        day = "2026-10-21"
        event = {"id": "ledger-sale-1", "idempotency_key": "ledger-sale-key", "business_day": day,
                 "event_type": "sale", "payment_method": "card", "amount_cents": 5000,
                 "occurred_at": "2026-10-21T09:00:00+02:00", "source_kind": "OPERATOR_REPORTED"}
        self.assertEqual(self.call("GET", f"/api/ledger/days/{day}", headers={"X-KasiMargin-Session":"other"})[0], 403)
        status, data, _ = self.call("POST", "/api/ledger/events", event)
        self.assertEqual(status, 200)
        saved = json.loads(data)["event"]
        self.assertFalse(saved["idempotent_replay"])
        self.assertEqual(json.loads(self.call("POST", "/api/ledger/events", event)[1])["event"]["idempotent_replay"], True)
        conflicting = {**event, "amount_cents": 6000}
        self.assertEqual(self.call("POST", "/api/ledger/events", conflicting)[0], 409)
        correction = {"id": "ledger-sale-1-r2", "idempotency_key": "ledger-correct-key", "replaces_id": saved["id"],
                      "expected_revision": 1, "amount_cents": 6000, "occurred_at": event["occurred_at"], "reason": "amount corrected"}
        self.assertEqual(self.call("POST", "/api/ledger/corrections", correction)[0], 200)
        status, data, _ = self.call("GET", f"/api/ledger/days/{day}")
        self.assertEqual(status, 200)
        reveal = json.loads(data)
        self.assertEqual(reveal["recorded_sales_cents"], 6000)
        self.assertEqual(reveal["card_sales_cents"], 6000)
        self.assertEqual(reveal["cash_position_status"], "NOT_PREPARED")

    def test_ledger_rejects_unsupported_movement_without_creating_a_record(self):
        day = "2026-10-22"
        invalid = {"id": "ledger-refund-1", "idempotency_key": "ledger-refund-key", "business_day": day,
                   "event_type": "refund", "payment_method": "cash", "amount_cents": 5000,
                   "occurred_at": "2026-10-22T09:00:00+02:00", "source_kind": "OPERATOR_REPORTED"}
        self.assertEqual(self.call("POST", "/api/ledger/events", invalid)[0], 400)
        status, data, _ = self.call("GET", f"/api/ledger/days/{day}")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)["record_count"], 0)

    def test_unknown_cash_and_bad_money_do_not_return_reassuring_amounts(self):
        payload = self.payload(); payload["input"]["cash_position"]["verified_cash_cents"] = None
        status, data, _ = self.call("POST", "/api/decision", payload)
        self.assertEqual(status, 200); self.assertIsNone(json.loads(data)["summary"]["cash_headroom_cents"])
        payload["input"]["cash_position"]["verified_cash_cents"] = True
        self.assertEqual(self.call("POST", "/api/decision", payload)[0], 400)

    def test_cash_check_does_not_require_optional_sales_or_invent_unknown_bills(self):
        payload = self.payload()
        payload["input"]["performance"] = {"recorded_sales_cents":None,"attributable_costs_cents":None,"complete":False}
        status, data, _ = self.call("POST", "/api/decision", payload)
        self.assertEqual(status, 200)
        result = json.loads(data)
        self.assertEqual(result["summary"]["cash_headroom_cents"], 40000)
        self.assertIsNone(result["summary"]["operating_margin_cents"])
        self.assertIn("MARGIN_UNKNOWN", result["selection"]["flag_ids"])
        payload["input"]["obligations"][0]["amount_cents"] = None
        status, data, _ = self.call("POST", "/api/decision", payload)
        self.assertEqual(status, 200)
        self.assertIsNone(json.loads(data)["summary"]["cash_headroom_cents"])

    def test_save_reviewed_result_preserves_selection_without_reinference(self):
        payload = self.payload()
        status, data, _ = self.call("POST", "/api/decision", payload)
        result = json.loads(data)
        saved = {"input":payload["input"], "result":result, "data_class":"SYNTHETIC"}
        status, data, _ = self.call("POST", "/api/receipt", saved)
        self.assertEqual(status, 200)
        path = Path(self.directory.name) / json.loads(data)["receipt_filename"]
        receipt = json.loads(path.read_text())
        self.assertEqual(receipt["payload"]["result"], result)
        saved["result"]["summary"]["cash_headroom_cents"] = 999999
        self.assertEqual(self.call("POST", "/api/receipt", saved)[0], 400)

    def test_cross_origin_host_and_form_requests_rejected(self):
        self.assertEqual(self.call("POST", "/api/decision", self.payload(), {"Origin":"https://example.com"})[0], 403)
        self.assertEqual(self.call("GET", "/", headers={"Host":"attacker.example"})[0], 403)
        self.assertEqual(self.call("POST", "/api/decision", self.payload(), {"Content-Type":"text/plain"})[0], 415)

    def test_strict_json_editing_and_browser_integer_range(self):
        payload = self.payload()
        status, data, _ = self.call("POST", "/api/validate", {"raw_json":json.dumps(payload["input"])})
        self.assertEqual(status, 200); self.assertEqual(json.loads(data), payload["input"])
        for raw in ('{"currency":"ZAR","currency":"USD"}', '{"value":NaN}'):
            self.assertEqual(self.call("POST", "/api/validate", {"raw_json":raw})[0], 400)
        payload["input"]["cash_position"]["verified_cash_cents"] = 9007199254740992
        self.assertEqual(self.call("POST", "/api/validate", {"raw_json":json.dumps(payload["input"])})[0], 400)

    def test_invalid_and_oversized_requests(self):
        self.assertEqual(self.call("POST", "/api/decision", raw="{}")[0], 400)
        self.assertEqual(self.call("POST", "/api/decision", raw="x"*262145)[0], 413)
        payload = self.payload(); payload["model"] = "gemma4:cloud"
        self.assertEqual(self.call("POST", "/api/decision", payload)[0], 400)

    def test_flask_factory_keeps_strict_wire_json_and_size_gate(self):
        client = create_app(self.directory.name).test_client()
        token = client.get("/api/session", base_url="http://127.0.0.1:8765").json["token"]
        raw = json.dumps(self.payload())
        raw = raw[:-1] + ',"model":"gemma4:cloud"}'
        rejected = client.post("/api/decision", base_url="http://127.0.0.1:8765", data=raw, content_type="application/json", headers={"X-KasiMargin-Session":token})
        self.assertEqual(rejected.status_code, 400)
        oversized = client.post("/api/decision", base_url="http://127.0.0.1:8765", data=b"x"*262145, content_type="application/json")
        self.assertEqual(oversized.status_code, 413)
        health = client.get("/health", base_url="http://127.0.0.1:8765")
        self.assertEqual(health.json["framework"], "Flask")

    def test_missing_or_other_process_session_cannot_calculate_or_save(self):
        before = set(Path(self.directory.name).iterdir())
        for token in ("", "another-process-token", "invalid-é-token"):
            self.assertEqual(self.call("POST", "/api/decision", self.payload(), {"X-KasiMargin-Session":token})[0], 403)
        self.assertEqual(self.call("GET", "/api/session", headers={"Origin":"https://example.com"})[0], 403)
        self.assertEqual(set(Path(self.directory.name).iterdir()), before)

    def test_local_request_budget_rejects_excess_without_writing(self):
        app = create_app(self.directory.name, request_limit=1)
        client = app.test_client()
        base = "http://127.0.0.1:8765"
        session = client.get("/api/session", base_url=base)
        headers = {"X-KasiMargin-Session":session.json["token"]}
        self.assertEqual(session.headers["Cache-Control"], "no-store")
        self.assertEqual(client.post("/api/decision", base_url=base, json=self.payload(), headers=headers).status_code, 200)
        before = set(Path(self.directory.name).iterdir())
        rejected = client.post("/api/decision", base_url=base, json=self.payload(), headers=headers)
        self.assertEqual(rejected.status_code, 429)
        self.assertGreater(int(rejected.headers["Retry-After"]), 0)
        self.assertEqual(set(Path(self.directory.name).iterdir()), before)

    def test_hybrid_context_route_is_scoped_and_separate_from_financial_validation(self):
        class Runtime:
            def probe(self):
                return {"status":"UNAVAILABLE", "checked_at":"2026-10-15T08:00:00+02:00", "scope":"READ_ONLY_CONTEXT_ENTRY", "financial_admission":"NOT_ESTABLISHED", "bank_verification":"NOT_PERFORMED"}
        client = create_app(self.directory.name, context_runtime=Runtime()).test_client()
        base = "http://127.0.0.1:8765"
        token = client.get("/api/session", base_url=base).json["token"]
        headers = {"X-KasiMargin-Session":token}
        self.assertEqual(client.post("/api/context",base_url=base,json={}).status_code,403)
        context = client.post("/api/context",base_url=base,json={},headers=headers)
        self.assertEqual(context.json["status"],"UNAVAILABLE")
        self.assertEqual(client.post("/api/context",base_url=base,json={"input":"private records"},headers=headers).status_code,400)
        payload = self.payload(); payload["input"]["cash_position"]["verified_cash_cents"] = None
        result = client.post("/api/decision",base_url=base,json=payload,headers=headers)
        self.assertEqual(result.status_code,200)
        self.assertIsNone(result.json["summary"]["cash_headroom_cents"])
        self.assertEqual(result.json["context_check"],context.json)

    def test_browser_decision_cannot_round_money_outside_its_integer_range(self):
        payload = self.payload(); payload["input"]["cash_position"]["verified_cash_cents"] = 9007199254740992
        self.assertEqual(self.call("POST","/api/decision",payload)[0],400)

    def test_browser_cannot_round_a_derived_shortfall_from_individually_exact_inputs(self):
        from kasimargin.workflow import decision
        payload = self.payload()
        payload["input"] = json.loads((ROOT / "fixtures/01.json").read_text())["input"]
        cash = payload["input"]["cash_position"]
        cash.update(verified_cash_cents=0,due_liabilities_cents=9007199254740991,committed_spend_cents=9007199254740991)
        self.assertGreater(decision(payload["input"])["summary"]["protected_cash_deficit_cents"],9007199254740991)
        before = set(Path(self.directory.name).iterdir())
        status,data,_ = self.call("POST","/api/decision",payload)
        self.assertEqual(status,400); self.assertIn("Python CLI",json.loads(data)["error"])
        self.assertEqual(set(Path(self.directory.name).iterdir()),before)

    def test_operator_decision_meaning_and_ledger_reference_markup_and_id_uniqueness(self):
        from html.parser import HTMLParser

        class StructureParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.ids = []
                self.stack = []
                self.parent_chains = {}

            def handle_starttag(self, tag, attrs):
                attr_map = dict(attrs)
                self.stack.append((tag, attr_map.get("id"), attr_map.get("class", "")))
                element_id = attr_map.get("id")
                if element_id:
                    self.ids.append(element_id)
                    self.parent_chains[element_id] = list(self.stack[:-1])

            def handle_endtag(self, tag):
                for idx in range(len(self.stack) - 1, -1, -1):
                    if self.stack[idx][0] == tag:
                        del self.stack[idx:]
                        break

        status, data, _ = self.call("GET", "/")
        self.assertEqual(status, 200)
        html_text = data.decode("utf-8")
        parser = StructureParser()
        parser.feed(html_text)
        self.assertEqual(len(parser.ids), len(set(parser.ids)), "Duplicate element IDs found in index.html")
        self.assertIn("What this means for your next decision", html_text)
        for visible_id in ("explanation", "model-state"):
            chain = parser.parent_chains[visible_id]
            self.assertTrue(any("decision-meaning" in cls for _, _, cls in chain))
            self.assertFalse(any(tag == "details" for tag, _, _ in chain))
        for technical_id in ("check-source", "context-state", "model-detail"):
            chain = parser.parent_chains[technical_id]
            self.assertTrue(any(tag == "details" and "explanation" in cls for tag, _, cls in chain))
        for bridge_id in ("ledger-to-check", "ledger-reference", "check-to-ledger", "ledger-reference-note", "ledger-reference-totals"):
            self.assertIn(bridge_id, parser.parent_chains)

    def test_decision_explanation_scenarios_and_admitted_or_fallback_gemma_bounds(self):
        from kasimargin.ollama import ModelUnavailable
        from kasimargin.workflow import decision

        # Scenario A: Unpaid credit sale (fixture 05) keeps receivables separate from cash headroom
        fixture_05 = json.loads((ROOT / "fixtures/05.json").read_text())["input"]
        status, data, _ = self.call("POST", "/api/decision", {"input": fixture_05, "model": None, "save_receipt": False, "data_class": "SYNTHETIC"})
        self.assertEqual(status, 200)
        res_05 = json.loads(data)
        self.assertEqual(res_05["summary"]["operating_margin_cents"], 30000)
        self.assertEqual(res_05["summary"]["cash_headroom_cents"], 5000)
        self.assertEqual(res_05["summary"]["protected_cash_deficit_cents"], 0)
        self.assertEqual(res_05["summary"]["recorded_receivables_delta_cents"], 60000)
        self.assertIn("CREDIT_SALES_NOT_CASH", res_05["selection"]["flag_ids"])
        self.assertIn("Check: Uncollected credit sales are excluded from available cash.", res_05["explanation"])

        # Scenario B: Missing obligations / unconfirmed balance (fixture 04) holds and never approves spending
        fixture_04 = json.loads((ROOT / "fixtures/04.json").read_text())["input"]
        status, data, _ = self.call("POST", "/api/decision", {"input": fixture_04, "model": None, "save_receipt": False, "data_class": "SYNTHETIC"})
        self.assertEqual(status, 200)
        res_04 = json.loads(data)
        self.assertEqual(res_04["summary"]["status"], "HOLD_INSUFFICIENT_DATA")
        self.assertTrue(res_04["explanation"].startswith("Spending assessment: HOLD — cash headroom is unknown."))
        self.assertIn("confirm_records", res_04["selection"]["action_ids"])
        self.assertNotIn("compare_restock_quote", res_04["selection"]["action_ids"])

        # Scenario C: Positive calculated headroom (fixture 01) allows quote comparison without claiming bank verification
        fixture_01 = json.loads((ROOT / "fixtures/01.json").read_text())["input"]
        status, data, _ = self.call("POST", "/api/decision", {"input": fixture_01, "model": None, "save_receipt": False, "data_class": "SYNTHETIC"})
        self.assertEqual(status, 200)
        res_01 = json.loads(data)
        self.assertEqual(res_01["summary"]["cash_headroom_cents"], 40000)
        self.assertIn("Compare an owner-supplied restock quote against the recorded headroom; no purchase has been assessed yet.", res_01["explanation"])

        # Scenario D: Admitted Gemma selection on Scenario 05 retains all facts & warnings while omitting optional quote comparison
        class AdmittedScenario05Client:
            def select(self, summary, model):
                return (
                    {
                        "fact_ids": ["operating_margin", "cash_headroom", "protected_cash_deficit", "receivables_delta"],
                        "flag_ids": ["CREDIT_SALES_NOT_CASH"],
                        "action_ids": ["preserve_headroom"],
                    },
                    {"model_digest": "sha256:b37049369adf"},
                )

        admitted = decision(fixture_05, model="gemma4:e2b-it-q4_K_M", client=AdmittedScenario05Client())
        self.assertEqual(admitted["inference"]["status"], "ADMITTED")
        self.assertEqual(admitted["selection"]["action_ids"], ["preserve_headroom"])
        for required_phrase in ("R300.00", "R50.00", "R0.00", "R600.00", "Check: Uncollected credit sales are excluded from available cash."):
            self.assertIn(required_phrase, admitted["explanation"])
        self.assertNotIn("Compare an owner-supplied restock quote", admitted["explanation"])
        self.assertIn("Compare an owner-supplied restock quote", admitted["baseline_explanation"])

        # Rejecting or unavailable model falls back cleanly to deterministic baseline
        from kasimargin.engine import ContractError
        from kasimargin.explanations import validate_selection

        class InvalidSelectionClient:
            def select(self, summary, model):
                try:
                    validate_selection(summary, {"fact_ids": ["operating_margin"], "flag_ids": [], "action_ids": ["preserve_headroom"]})
                except ContractError as exc:
                    raise ModelUnavailable(str(exc)) from exc

        class OfflineClient:
            def select(self, summary, model):
                raise ModelUnavailable("Ollama connection refused")

        for bad_client in (InvalidSelectionClient(), OfflineClient()):
            fallback = decision(fixture_05, model="gemma4:e2b-it-q4_K_M", client=bad_client)
            self.assertEqual(fallback["inference"]["status"], "REJECTED_OR_UNAVAILABLE")
            self.assertEqual(fallback["explanation"], fallback["baseline_explanation"])
