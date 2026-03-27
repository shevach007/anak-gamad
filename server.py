import http.server
import json
import csv
import os
from datetime import datetime

PORT = int(os.environ.get("PORT", 5050))
CSV_FILE = os.path.join(os.path.dirname(__file__), "anak_gamad.csv")
STATIC_DIR = os.path.dirname(__file__)

CSV_HEADERS = ["שם", "ענק (נתת מתנות ל)", "גמד (ניחוש - מי נתן לך)", "זמן"]


def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def append_entry(entry):
    ensure_csv()
    with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            entry.get("name", ""),
            entry.get("anak", ""),
            entry.get("gamad", ""),
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        ])


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/results":
            self.path = "/results.html"
        elif self.path == "/data":
            self._serve_data()
            return
        super().do_GET()

    def _serve_data(self):
        entries = []
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entries.append({
                        "name": row.get("שם", ""),
                        "anak": row.get("ענק (נתת מתנות ל)", ""),
                        "gamad": row.get("גמד (ניחוש - מי נתן לך)", ""),
                        "time": row.get("זמן", ""),
                    })
        body = json.dumps(entries, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/save":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                entry = json.loads(body)
                append_entry(entry)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok": true}')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}]", format % args)


if __name__ == "__main__":
    ensure_csv()
    print(f"Server running at http://localhost:{PORT}")
    print(f"CSV will be saved to: {CSV_FILE}")
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
