"""Tiny stdlib static file server for the auto-money-agent demo.

Serves:
  /                          → dashboard
  /dashboard/                → dashboard
  /tools_output/             → generated static site (tools + index + policies)

Usage:  python serve.py [port]
"""
from __future__ import annotations
import http.server
import socketserver
import os
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[serve] {self.address_string()} - {fmt % args}\n")


if __name__ == "__main__":
    handler = Handler
    os.chdir(str(HERE))
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        print(f"[serve] listening on http://127.0.0.1:{PORT}")
        print("  dashboard:   http://127.0.0.1:{}/dashboard/".format(PORT))
        print("  site root:   http://127.0.0.1:{}/tools_output/index.html".format(PORT))
        httpd.serve_forever()
