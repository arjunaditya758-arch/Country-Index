#!/usr/bin/env python3
"""Serve Country Index; persist trained toggles to trained_progress.json."""

from __future__ import annotations

import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
TRAINED_FILE = OUT_DIR / "trained_progress.json"
DEFAULT_PORT = 8765


def normalize_progress(raw: dict) -> dict:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, bool]] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        if value is True:
            out[key] = {"jsonl": True, "ongoing": False}
        elif value is False:
            out[key] = {"jsonl": False, "ongoing": False}
        elif isinstance(value, dict):
            out[key] = {
                "jsonl": value.get("jsonl") is True,
                "ongoing": value.get("ongoing") is True,
            }
    return out


class IndexHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUT_DIR), **kwargs)

    def do_GET(self) -> None:
        if self.path == "/api/trained":
            self._send_json(self._read_trained())
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/trained":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return
            if not isinstance(data, dict):
                self.send_error(400, "Expected JSON object")
                return
            TRAINED_FILE.write_text(
                json.dumps(normalize_progress(data), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self.send_response(204)
            self.end_headers()
            return
        super().do_POST()

    def _read_trained(self) -> dict:
        if not TRAINED_FILE.exists():
            return {}
        try:
            data = json.loads(TRAINED_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return normalize_progress(data if isinstance(data, dict) else {})

    def _send_json(self, data: dict) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:
        if args and "/api/trained" in str(args[0]):
            return
        super().log_message(format, *args)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    if not TRAINED_FILE.exists():
        TRAINED_FILE.write_text("{}\n", encoding="utf-8")

    server = ThreadingHTTPServer(("127.0.0.1", port), IndexHandler)
    url = f"http://127.0.0.1:{port}/index.html"
    print(f"Law Agent Country Index — {url}")
    print("  JSONL + ongoing toggles save to trained_progress.json")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
