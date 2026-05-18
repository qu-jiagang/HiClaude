from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from .render import render_svg
from .storage import load_state


class Handler(BaseHTTPRequestHandler):
    state_path: Path | None = None
    collect_mode: bool = False

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if self.collect_mode:
            from .collector import collect
            state = collect()
        else:
            state = load_state(self.state_path)
        if parsed.path in {"/", "/index.html"}:
            body = (
                "<!doctype html><meta charset='utf-8'>"
                "<title>Agent E-Paper</title>"
                "<style>body{margin:24px;font-family:sans-serif;background:#ddd}"
                "iframe{width:960px;max-width:100%;aspect-ratio:16/9;border:0;background:white}</style>"
                "<iframe src='/screen.svg'></iframe>"
            ).encode("utf-8")
            self.respond(body, "text/html; charset=utf-8")
        elif parsed.path == "/screen.svg":
            mode = qs.get("mode", ["overview"])[0]
            if mode not in ("overview", "agent0", "agent1"):
                mode = "overview"
            self.respond(render_svg(state, mode=mode).encode("utf-8"), "image/svg+xml; charset=utf-8")
        elif parsed.path == "/state.json":
            self.respond(json.dumps(state.to_dict(), ensure_ascii=False, indent=2).encode("utf-8"), "application/json; charset=utf-8")
        else:
            self.send_error(404)

    def log_message(self, fmt: str, *args: object) -> None:
        print("%s - %s" % (self.address_string(), fmt % args))

    def respond(self, body: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the current e-paper state.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--state", type=Path, default=None)
    parser.add_argument("--collect", action="store_true",
                        help="Collect real-time data on every request instead of reading a state file.")
    args = parser.parse_args(argv)

    Handler.state_path = args.state
    Handler.collect_mode = args.collect
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving on http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
