import http.server
import json
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

PORT = int(os.environ.get("PORT", 5050))
STATIC_DIR = os.path.dirname(__file__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheet():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    sheet_id = os.environ.get("SHEET_ID")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id).sheet1


def append_entry(entry):
    sheet = get_sheet()
    if sheet.row_count == 0 or sheet.cell(1, 1).value is None:
        sheet.append_row(["שם", "ענק (נתת מתנות ל)", "גמד (ניחוש - מי נתן לך)", "זמן"])
    sheet.append_row([
        entry.get("name", ""),
        entry.get("anak", ""),
        entry.get("gamad", ""),
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    ])


def get_entries():
    sheet = get_sheet()
    rows = sheet.get_all_records()
    return [
        {
            "name": row.get("שם", ""),
            "anak": row.get("ענק (נתת מתנות ל)", ""),
            "gamad": row.get("גמד (ניחוש - מי נתן לך)", ""),
            "time": row.get("זמן", ""),
        }
        for row in rows
    ]


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
        try:
            entries = get_entries()
            body = json.dumps(entries, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

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
    print(f"Server running at http://localhost:{PORT}")
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
