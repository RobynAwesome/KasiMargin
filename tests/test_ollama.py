from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread
import unittest
from pathlib import Path
from kasimargin.engine import calculate
from kasimargin.explanations import catalogue
from kasimargin.ollama import LocalOllama, ModelUnavailable
from kasimargin.workflow import decision

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gemma4:e2b"


class MockOllama(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def response(self, value, status=200):
        raw = json.dumps(value).encode()
        self.send_response(status); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)

    def do_GET(self):
        self.server.tag_reads += 1
        digest = "changed" if self.server.change_digest and self.server.tag_reads > 1 else "synthetic-digest"
        self.response({"models": [{"name": MODEL, "digest": digest}]} if not self.server.missing else {"models": []})

    def do_POST(self):
        self.server.calls.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        if self.server.error:
            self.response({"error": "fake service failure"}, 500)
        else:
            self.response({"model": MODEL, "done": True, "message": {"content": self.server.output}, "eval_count": 42})


class OllamaBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), MockOllama)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.client = LocalOllama(port=cls.server.server_port, timeout=2)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def setUp(self):
        self.server.calls = []; self.server.tag_reads = 0
        self.server.error = self.server.missing = self.server.change_digest = False
        self.request = json.loads((ROOT / "fixtures/05.json").read_text())["input"]
        allowed = catalogue(calculate(self.request))
        self.selection = {"fact_ids": list(allowed["facts"]), "flag_ids": list(allowed["required_flags"]), "action_ids": ["preserve_headroom"]}
        self.server.output = json.dumps(self.selection)

    def test_local_http_adapter_admits_selection_and_records_identity(self):
        result = decision(self.request, MODEL, self.client)
        self.assertEqual(result["inference"]["status"], "ADMITTED")
        self.assertEqual(result["inference"]["digest"], "synthetic-digest")
        self.assertEqual(result["inference"]["ollama_metrics"]["eval_count"], 42)
        sent = self.server.calls[0]
        self.assertFalse(sent["stream"])
        self.assertFalse(sent["think"])
        self.assertNotIn("source_description", json.dumps(sent))
        self.assertEqual(sent["format"]["properties"]["flag_ids"]["items"]["enum"], ["CREDIT_SALES_NOT_CASH"])

    def test_invalid_model_prose_warning_omission_and_actions_fall_back(self):
        cases = ["not JSON", '{"fact_ids":[],"flag_ids":[],"action_ids":["buy_now"]}', json.dumps({**self.selection,"flag_ids":[]}), json.dumps({**self.selection,"advice":"Spend R9000"}), '{"fact_ids":[],"fact_ids":[],"flag_ids":[],"action_ids":[]}']
        for output in cases:
            with self.subTest(output=output):
                self.server.output = output
                result = decision(self.request, MODEL, self.client)
                self.assertEqual(result["inference"]["status"], "REJECTED_OR_UNAVAILABLE")
                self.assertEqual(result["explanation"], result["baseline_explanation"])
                self.assertNotIn("Spend R9000", result["explanation"])

    def test_missing_model_http_error_and_digest_drift_fall_back(self):
        for name in ("missing", "error", "change_digest"):
            with self.subTest(name=name):
                self.setUp(); setattr(self.server, name, True)
                result = decision(self.request, MODEL, self.client)
                self.assertEqual(result["inference"]["status"], "REJECTED_OR_UNAVAILABLE")

    def test_hold_selection_cannot_offer_quote_comparison(self):
        request = json.loads((ROOT / "fixtures/04.json").read_text())["input"]
        self.assertEqual(decision(request, MODEL, self.client)["inference"]["status"], "REJECTED_OR_UNAVAILABLE")

    def test_no_model_call_without_explicit_request(self):
        self.assertEqual(decision(self.request, client=self.client)["inference"]["status"], "NOT_REQUESTED")
        self.assertEqual(self.server.tag_reads, 0)
        self.assertEqual(self.server.calls, [])

    def test_cloud_tag_and_bad_connection_settings_rejected(self):
        with self.assertRaises(ModelUnavailable): self.client.select(calculate(self.request), "gemma4:cloud")
        for setting in ({"port": True}, {"port": 0}, {"timeout": float("nan")}, {"timeout": 500}):
            with self.subTest(setting=setting):
                with self.assertRaises(ValueError): LocalOllama(**setting)

    def test_private_trace_records_transport_without_bypassing_selection_gate(self):
        records = []
        client = LocalOllama(port=self.server.server_port, timeout=2, trace=records.append)
        self.server.output = json.dumps({**self.selection, "advice": "Spend R9000"})
        result = decision(self.request, MODEL, client)
        self.assertEqual(result["inference"]["status"], "REJECTED_OR_UNAVAILABLE")
        self.assertTrue(any(row["path"] == "/api/chat" and "Spend R9000" in row["raw_response"] for row in records))
        self.assertNotIn("Spend R9000", result["explanation"])
        self.assertEqual(self.server.calls[0]["options"]["num_ctx"], 4096)
