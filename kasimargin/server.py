"""Small loopback-only demo; no persistence unless the operator asks to save."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from .engine import ContractError, exact_keys
from .jsonio import loads
from .ollama import MODELS
from .receipts import save
from .workflow import decision

ROOT = Path(__file__).resolve().parents[1]
WEB = Path(__file__).resolve().parent / "web"
MAX_INPUT_BYTES = 262144


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Never log merchant inputs, model output or exception contents.
        pass

    def reply(self, status, body, content_type="application/json; charset=utf-8"):
        raw = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(raw)

    def local_request(self):
        port = self.server.server_port
        hosts = (f"127.0.0.1:{port}", f"localhost:{port}")
        if self.headers.get("Host") not in hosts:
            self.reply(403, {"error": "Open this demo through its local address."})
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin not in tuple(f"http://{host}" for host in hosts):
            self.reply(403, {"error": "Cross-origin requests are disabled."})
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        if self.path == "/health":
            self.reply(200, {"status": "LOCAL_DEMO", "model_execution": "ON_EXPLICIT_REQUEST_ONLY"})
        elif self.path == "/api/fixtures":
            cases = [loads((ROOT / "fixtures" / f"{number:02}.json").read_text(encoding="utf-8")) for number in range(1, 7)]
            cases.append(loads((ROOT / "fixtures" / "itemized" / "01.json").read_text(encoding="utf-8")))
            self.reply(200, cases)
        elif self.path in ("/", "/app.js", "/theme.js", "/style.css", "/assets/kasimargin-ribbon-emblem.png"):
            filename, content_type = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                "/theme.js": ("theme.js", "text/javascript; charset=utf-8"),
                "/style.css": ("style.css", "text/css; charset=utf-8"),
                "/assets/kasimargin-ribbon-emblem.png": ("assets/kasimargin-ribbon-emblem.png", "image/png"),
            }[self.path]
            self.reply(200, (WEB / filename).read_bytes(), content_type)
        else:
            self.reply(404, {"error": "Not found"})

    def do_POST(self):
        if not self.local_request():
            return
        if self.path not in ("/api/decision", "/api/validate", "/api/receipt"):
            self.reply(404, {"error": "Not found"})
            return
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            self.reply(415, {"error": "Use application/json"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_INPUT_BYTES:
                self.reply(413, {"error": "Request size is outside the demo limit"})
                return
            value = loads(self.rfile.read(length).decode("utf-8"))
            if self.path == "/api/receipt":
                exact_keys(value, {"input", "result", "data_class"}, "save reviewed decision")
                path = save(value["input"], value["result"], value["data_class"], self.server.receipt_directory)
                self.reply(200, {"receipt_filename": path.name, "human_review": "NOT_RECORDED"})
                return
            if self.path == "/api/validate":
                exact_keys(value, {"raw_json"}, "record review")
                if not isinstance(value["raw_json"], str):
                    raise ContractError("raw_json must be a JSON string")
                reviewed = loads(value["raw_json"])
                def browser_range(item):
                    if type(item) is int and abs(item) > 9007199254740991:
                        raise ContractError("use the CLI for integers outside the browser range")
                    if isinstance(item, dict):
                        for child in item.values():
                            browser_range(child)
                    elif isinstance(item, list):
                        for child in item:
                            browser_range(child)
                browser_range(reviewed)
                decision(reviewed)
                self.reply(200, reviewed)
                return
            exact_keys(value, {"input", "model", "save_receipt", "data_class"}, "decision request")
            if value["model"] is not None and value["model"] not in MODELS:
                raise ContractError("unsupported model candidate")
            if type(value["save_receipt"]) is not bool:
                raise ContractError("save_receipt must be boolean")
            if value["data_class"] not in ("SYNTHETIC", "OPERATOR_ATTESTED"):
                raise ContractError("choose a valid evidence class")
            result = decision(value["input"], value["model"])
            if value["save_receipt"]:
                path = save(value["input"], result, value["data_class"], self.server.receipt_directory)
                result["receipt_filename"] = path.name
            self.reply(200, result)
        except (ContractError, ValueError, KeyError, TypeError, UnicodeError):
            self.reply(400, {"error": "Input rejected. Check exact integer cents, required fields, timestamps and evidence."})
        except OSError:
            self.reply(500, {"error": "Local file operation failed; no saved receipt is confirmed."})


def make_server(port=8765, receipt_directory=None):
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("port must be from 0 to 65535")
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.receipt_directory = Path(receipt_directory) if receipt_directory is not None else ROOT / "local-data" / "decisions"
    return server


def serve(port=8765):
    with make_server(port) as server:
        print(f"KasiMargin local demo: http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
