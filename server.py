from __future__ import annotations

import json
import threading
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from local_model_client import LocalModelError
from twin_core import DigitalAITwin


ROOT_DIR = Path(__file__).resolve().parent
WEB_DIR = ROOT_DIR / "web"
TWIN = DigitalAITwin()
TWIN_LOCK = threading.Lock()


class AppHandler(BaseHTTPRequestHandler):
    server_version = "DigitalTwinHTTP/1.0"

    def __init__(self, *args, twin: DigitalAITwin, twin_lock: threading.Lock, **kwargs):
        self.twin = twin
        self.twin_lock = twin_lock
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self._send_json(HTTPStatus.OK, self.twin.api_status())
            return
        if parsed.path == "/api/memories":
            self._send_json(HTTPStatus.OK, {"memories": self._serialize_memories()})
            return
        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        payload = self._read_json_body()
        if payload is None:
            return

        try:
            if parsed.path == "/api/settings":
                with self.twin_lock:
                    if "user_name" in payload:
                        self.twin.set_user_name(str(payload.get("user_name", "")), persist=True)
                    if "model_name" in payload or "base_url" in payload:
                        self.twin.set_local_model(str(payload.get("model_name", self.twin.model.model_name)), str(payload.get("base_url", self.twin.model.base_url)), persist=True)
                    status = self.twin.api_status()
                self._send_json(HTTPStatus.OK, {"message": "Settings saved.", "status": status})
                return

            if parsed.path == "/api/survey":
                with self.twin_lock:
                    self.twin.process_survey(payload)
                    status = self.twin.api_status()
                self._send_json(HTTPStatus.OK, {"message": "Survey processed.", "status": status})
                return

            if parsed.path == "/api/chat":
                message = str(payload.get("message", "")).strip()
                if not message:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Message is required."})
                    return
                with self.twin_lock:
                    reply = self.twin.chat(message)
                self._send_json(HTTPStatus.OK, {"reply": reply})
                return

            if parsed.path == "/api/simulate":
                situation = str(payload.get("situation", "")).strip()
                if not situation:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Situation is required."})
                    return
                with self.twin_lock:
                    reply = self.twin.simulate_decision(situation)
                self._send_json(HTTPStatus.OK, {"reply": reply})
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Unknown endpoint."})
        except LocalModelError as exc:
            self._send_json(HTTPStatus.BAD_GATEWAY, {"error": str(exc), "status": self.twin.api_status()})
        except Exception as exc:  # pragma: no cover - last-resort guard
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Unexpected server error: {exc}"})

    def log_message(self, format: str, *args) -> None:
        return

    def _read_json_body(self) -> dict | None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body."})
            return None

    def _serialize_memories(self) -> list[dict[str, object]]:
        with self.twin_lock:
            memories = self.twin.memories.list()
        return [
            {
                "type": memory.type,
                "text": memory.text,
                "timestamp": memory.timestamp.isoformat(),
                "permanent": memory.permanent,
                "meta": memory.meta,
            }
            for memory in memories
        ]

    def _serve_static(self, request_path: str) -> None:
        relative = request_path.lstrip("/") or "index.html"
        file_path = (WEB_DIR / relative).resolve()
        if WEB_DIR.resolve() not in file_path.parents and file_path != (WEB_DIR / "index.html").resolve():
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Forbidden."})
            return
        if not file_path.exists() or not file_path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "File not found."})
            return

        content_type = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".obj": "text/plain; charset=utf-8",
        }.get(file_path.suffix.lower(), "application/octet-stream")
        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    handler = partial(AppHandler, twin=TWIN, twin_lock=TWIN_LOCK)
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    server = create_server()
    print("Digital AI Twin server running at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
