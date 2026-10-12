from http.client import HTTPConnection
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from kasimargin.server import make_server
from kasimargin.receipts import verify

ROOT = Path(__file__).resolve().parents[1]


class LocalDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.server = make_server(0, cls.directory.name)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(); cls.directory.cleanup()

    def call(self, method, path, value=None, headers=None, raw=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        body = raw if raw is not None else None if value is None else json.dumps(value)
        connection.request(method, path, body=body, headers={"Content-Type":"application/json", **(headers or {})})
        response = connection.getresponse(); data = response.read(); status = response.status; reply_headers = dict(response.getheaders()); connection.close()
        return status, data, reply_headers

    def payload(self):
        return {"input":json.loads((ROOT / "fixtures/itemized/01.json").read_text())["input"],"model":None,"save_receipt":False,"data_class":"SYNTHETIC"}

    def test_assets_and_fixtures_are_served_without_external_dependencies(self):
        for path in ("/", "/app.js", "/style.css", "/health"):
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

    def test_unknown_cash_and_bad_money_do_not_return_reassuring_amounts(self):
        payload = self.payload(); payload["input"]["cash_position"]["verified_cash_cents"] = None
        status, data, _ = self.call("POST", "/api/decision", payload)
        self.assertEqual(status, 200); self.assertIsNone(json.loads(data)["summary"]["cash_headroom_cents"])
        payload["input"]["cash_position"]["verified_cash_cents"] = True
        self.assertEqual(self.call("POST", "/api/decision", payload)[0], 400)

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
