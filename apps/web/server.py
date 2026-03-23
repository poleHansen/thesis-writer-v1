from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import TCPServer

WEB_ROOT = Path(__file__).parent
PORT = 3000


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)


if __name__ == "__main__":
    with TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"web server listening on http://0.0.0.0:{PORT}")
        httpd.serve_forever()
