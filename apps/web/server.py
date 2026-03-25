from http.server import SimpleHTTPRequestHandler
import os
from pathlib import Path
from socketserver import TCPServer

WEB_ROOT = Path(__file__).parent
DEFAULT_PORT = 3000


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)


if __name__ == "__main__":
    port = int(os.environ.get("WEB_PORT", DEFAULT_PORT))

    try:
        with TCPServer(("0.0.0.0", port), Handler) as httpd:
            print(f"web server listening on http://0.0.0.0:{port}")
            httpd.serve_forever()
    except OSError as exc:
        if getattr(exc, "winerror", None) == 10048:
            raise SystemExit(
                f"Port {port} is already in use. Set WEB_PORT to another value, for example: "
                f"WEB_PORT={port + 1} uv run python apps/web/server.py"
            ) from exc
        raise
