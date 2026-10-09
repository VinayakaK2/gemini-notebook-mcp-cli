from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.request import urlopen

INTERNAL_READY_URL = "http://127.0.0.1:10001/readyz"


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/healthz":
            self.send_error(404)
            return
        try:
            with urlopen(INTERNAL_READY_URL, timeout=1) as response:
                ready = 200 <= response.status < 300
        except (URLError, TimeoutError, OSError):
            ready = False
        body = b"ready\n" if ready else b"not ready\n"
        self.send_response(200 if ready else 503)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        return


def main() -> int:
    required = ("CONTROL_PLANE_API_KEY", "CONTROL_PLANE_TUNNEL_ID")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print("Missing required environment variable(s): " + ", ".join(missing), file=sys.stderr)
        return 2

    port = int(os.environ.get("PORT", "10000"))
    command = [
        "tunnel-client",
        "run",
        "--health.listen-addr", "127.0.0.1:10001",
        "--mcp.command", "notebooklm-mcp",
        "--log.level=info",
        "--log.format=struct-text",
    ]
    child = subprocess.Popen(command, env=os.environ.copy())

    def stop_child(signum: int, _frame: object) -> None:
        if child.poll() is None:
            child.terminate()

    signal.signal(signal.SIGTERM, stop_child)
    signal.signal(signal.SIGINT, stop_child)

    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()

    try:
        while child.poll() is None:
            time.sleep(1)
        return int(child.returncode or 0)
    finally:
        server.shutdown()
        server.server_close()
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()


if __name__ == "__main__":
    raise SystemExit(main())
