# -*- coding: utf-8 -*-
"""Minik statik host — YouTube yorum cevabı 'kopyala' sayfası.

Neden ayrı bir servis: HTML mailler JavaScript çalıştıramaz, yani çalışan bir
"kopyala" butonu mailin içine konamaz. Buton bir web sayfasında olmak zorunda.
Bu servis o tek sayfayı (cevap_kopyala.html) doğru HTML mime ile servis eder.

Tasarım: SUNUCUSUZ veri. Cevap metni + YouTube linki, mail butonundaki linkin
'#d=' hash'inde gelir (istemci tarafı). Sunucu hiçbir veri görmez/saklamaz,
hiçbir anahtara/DB'ye ihtiyaç duymaz -> yanlış config'le çökemez, app-sleep güvenli.

Çalıştırma: python server.py  (PORT env'i Railway verir). Stdlib, bağımlılık yok.
"""
import http.server
import os
import socketserver

PORT = int(os.environ.get("PORT", "8080"))
_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cevap_kopyala.html")
with open(_HTML_PATH, "rb") as _f:
    _PAGE = _f.read()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/health"):
            self._send(b"ok", "text/plain; charset=utf-8")
            return
        # Her yol kopyala sayfasını döndürür (veri hash'te, sunucu görmez).
        self._send(_PAGE, "text/html; charset=utf-8", cache=True)

    def _send(self, body: bytes, ctype: str, cache: bool = False):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        if cache:
            self.send_header("Cache-Control", "public, max-age=300")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # Railway log'unu sessiz tut
        pass


if __name__ == "__main__":
    with socketserver.ThreadingTCPServer(("", PORT), Handler) as httpd:
        print(f"kopyala sayfasi {PORT} portunda")
        httpd.serve_forever()
