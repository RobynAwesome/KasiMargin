"""Flask application factory for the loopback-only decision demo."""
import logging
from pathlib import Path
from flask import Flask, Response, request
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.serving import make_server as make_wsgi_server
from .engine import ContractError, exact_keys
from .jsonio import dumps, loads
from .ollama import MODELS
from .receipts import save
from .workflow import decision

ROOT = Path(__file__).resolve().parents[1]
WEB = Path(__file__).resolve().parent / "web"
MAX_INPUT_BYTES = 262144


def create_app(receipt_directory=None, port=8765):
    app = Flask(__name__, static_folder=None)
    app.config.update(MAX_CONTENT_LENGTH=MAX_INPUT_BYTES,
                      ALLOWED_LOCAL_HOSTS=(f"127.0.0.1:{port}", f"localhost:{port}"),
                      RECEIPT_DIRECTORY=Path(receipt_directory) if receipt_directory is not None else ROOT / "local-data/decisions")

    def reply(value, status=200):
        return Response(dumps(value), status=status, content_type="application/json; charset=utf-8")

    @app.before_request
    def local_request():
        if request.host not in app.config["ALLOWED_LOCAL_HOSTS"]:
            return reply({"error": "Open this demo through its local address."}, 403)
        origin = request.headers.get("Origin")
        if origin is not None and origin not in tuple(f"http://{host}" for host in app.config["ALLOWED_LOCAL_HOSTS"]):
            return reply({"error": "Cross-origin requests are disabled."}, 403)
        if request.method == "POST" and request.mimetype != "application/json":
            return reply({"error": "Use application/json"}, 415)

    @app.after_request
    def response_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        return response

    @app.errorhandler(RequestEntityTooLarge)
    def oversized(error):
        return reply({"error": "Request size is outside the demo limit"}, 413)

    @app.errorhandler(404)
    def missing(error):
        return reply({"error": "Not found"}, 404)

    @app.get("/health")
    def health():
        return reply({"status": "LOCAL_DEMO", "framework": "Flask", "model_execution": "ON_EXPLICIT_REQUEST_ONLY"})

    @app.get("/api/fixtures")
    def fixtures():
        paths = [ROOT / "fixtures" / f"{number:02}.json" for number in range(1, 7)]
        paths.append(ROOT / "fixtures/itemized/01.json")
        return reply([loads(path.read_text(encoding="utf-8")) for path in paths])

    assets = {"/": ("index.html", "text/html; charset=utf-8"),
              "/app.js": ("build/app.js", "text/javascript; charset=utf-8"),
              "/theme.js": ("build/theme.js", "text/javascript; charset=utf-8"),
              "/style.css": ("style.css", "text/css; charset=utf-8"),
              "/assets/kasimargin-ribbon-emblem.png": ("assets/kasimargin-ribbon-emblem.png", "image/png")}

    def asset():
        filename, mime = assets[request.path]
        path = WEB / filename
        if not path.is_file():
            return reply({"error": "Browser assets are missing. Run npm ci and npm run build."}, 503)
        return Response(path.read_bytes(), content_type=mime)

    for index, route in enumerate(assets):
        app.add_url_rule(route, f"asset_{index}", asset, methods=["GET"])

    def browser_range(item):
        if type(item) is int and abs(item) > 9007199254740991:
            raise ContractError("use the CLI for integers outside the browser range")
        if isinstance(item, dict):
            for child in item.values(): browser_range(child)
        elif isinstance(item, list):
            for child in item: browser_range(child)

    @app.post("/api/decision")
    @app.post("/api/validate")
    @app.post("/api/receipt")
    def submit():
        try:
            # Use the shared strict parser: Flask's normal JSON loader would
            # accept duplicate keys. Preserve the existing contract gate.
            raw = request.get_data(cache=False)
            if not raw:
                return reply({"error": "Request size is outside the demo limit"}, 413)
            value = loads(raw.decode("utf-8"))
            if request.path == "/api/receipt":
                exact_keys(value, {"input", "result", "data_class"}, "save reviewed decision")
                path = save(value["input"], value["result"], value["data_class"], app.config["RECEIPT_DIRECTORY"])
                return reply({"receipt_filename": path.name, "human_review": "NOT_RECORDED"})
            if request.path == "/api/validate":
                exact_keys(value, {"raw_json"}, "record review")
                if not isinstance(value["raw_json"], str):
                    raise ContractError("raw_json must be a JSON string")
                reviewed = loads(value["raw_json"])
                browser_range(reviewed)
                decision(reviewed)
                return reply(reviewed)
            exact_keys(value, {"input", "model", "save_receipt", "data_class"}, "decision request")
            if value["model"] is not None and value["model"] not in MODELS:
                raise ContractError("unsupported model candidate")
            if type(value["save_receipt"]) is not bool:
                raise ContractError("save_receipt must be boolean")
            if value["data_class"] not in ("SYNTHETIC", "OPERATOR_ATTESTED"):
                raise ContractError("choose a valid evidence class")
            result = decision(value["input"], value["model"])
            if value["save_receipt"]:
                path = save(value["input"], result, value["data_class"], app.config["RECEIPT_DIRECTORY"])
                result["receipt_filename"] = path.name
            return reply(result)
        except (ContractError, ValueError, KeyError, TypeError, UnicodeError):
            return reply({"error": "Input rejected. Check exact integer cents, required fields, timestamps and evidence."}, 400)
        except OSError:
            return reply({"error": "Local file operation failed; no saved receipt is confirmed."}, 500)

    return app


def make_server(port=8765, receipt_directory=None):
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("port must be from 0 to 65535")
    app = create_app(receipt_directory, port)
    # Tests and CLI share the real Flask WSGI transport. No debug/reloader.
    server = make_wsgi_server("127.0.0.1", port, app, threaded=True)
    app.config["ALLOWED_LOCAL_HOSTS"] = (f"127.0.0.1:{server.server_port}", f"localhost:{server.server_port}")
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    return server


def serve(port=8765):
    with make_server(port) as server:
        print(f"KasiMargin local Flask demo: http://127.0.0.1:{server.server_port}", flush=True)
        try: server.serve_forever()
        except KeyboardInterrupt: pass
