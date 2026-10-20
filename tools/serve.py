#!/usr/bin/env python3
"""Development server: run the offline pipeline into data/ and serve the repository root.

    python3 tools/serve.py            # http://localhost:8000/?now=2026-10-20T18:00:00Z
    python3 tools/serve.py --keep     # do not run the pipeline again
    python3 tools/serve.py --port 9000

The fixtures are from 2026-10-20. The page parameter ?now= freezes the page clock,
so the data does not show as stale. This script is for development only.
"""
import argparse
import functools
import http.server
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOW = "2026-10-20T18:00:00Z"


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        if "--quiet" not in sys.argv:
            super().log_message(fmt, *args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--keep", action="store_true", help="keep data/; do not run the pipeline")
    ap.add_argument("--now", default=NOW, help="clock for the offline run")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    if not args.keep:
        subprocess.run([sys.executable, os.path.join(ROOT, "fetch", "run.py"), "--tier", "all",
                        "--offline", os.path.join(ROOT, "fixtures"), "--now", args.now], check=True)
    handler = functools.partial(Handler, directory=ROOT)
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as srv:
        print(f"Open http://localhost:{args.port}/?now={args.now}")
        srv.serve_forever()


if __name__ == "__main__":
    main()
