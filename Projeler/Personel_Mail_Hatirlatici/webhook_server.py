"""
Personel Mail Hatırlatıcı — Buton Webhook Servisi
===================================================
Mail digest'indeki "🔇 Sustur" ve "⏰ Ertele" butonları bu servise
HMAC-imzalı token ile gelir. Tek bir Railway servisi olarak çalışır
(uvicorn webhook_server:app).

Endpoint'ler:
- GET  /healthz
- GET  /mute?token=...                 → o thread'in tarafını tüm satırlarda mute eder
- GET  /snooze?token=...               → küçük HTML form (kaç gün?)
- POST /snooze/confirm?token=...       → form gönderiminden sonra Snoozed Until set eder
"""

import os
import sys
import logging
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse

from services import notion_threads
from services.token_signer import verify_token

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("personel_mail_webhook")

app = FastAPI(title="Personel Mail Hatırlatıcı Webhook")


def _page(title: str, body_html: str, color: str = "#1a73e8") -> str:
    return f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><title>{title}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background:#f7f7f7; margin:0; padding:0; min-height:100vh; display:flex;
  align-items:center; justify-content:center; }}
.card {{ background:#fff; border-radius:12px; padding:32px 28px; max-width:440px;
  box-shadow:0 4px 24px rgba(0,0,0,0.08); text-align:center; }}
h1 {{ color:{color}; margin:0 0 12px 0; font-size:22px; }}
p  {{ color:#444; line-height:1.5; }}
input[type=number] {{ font-size:18px; padding:10px 14px; width:120px;
  border:1px solid #ddd; border-radius:8px; text-align:center; }}
button {{ background:{color}; color:#fff; border:none; padding:12px 22px;
  font-size:15px; border-radius:8px; cursor:pointer; margin-top:14px; }}
button:hover {{ filter: brightness(1.05); }}
small {{ color:#999; }}
</style></head>
<body><div class="card">{body_html}</div></body></html>"""


@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@app.get("/mute", response_class=HTMLResponse)
def mute(token: str = ""):
    parsed = verify_token(token)
    if not parsed or parsed[0] != "mute":
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş bağlantı")
    _, page_id = parsed

    rec = notion_threads.find_page_by_id(page_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Thread bulunamadı")

    brand = rec.get("brand") or ""
    if not brand:
        # Brand boşsa sadece bu page'i mute et
        notion_threads._request(
            "PATCH",
            f"/pages/{page_id}",
            {"properties": {"Brand Muted": {"checkbox": True}}},
        )
        return HTMLResponse(_page(
            "Susturuldu",
            "<h1>✅ Susturuldu</h1><p>Bu thread bir daha hatırlatılmayacak.</p>",
        ))

    n = notion_threads.mute_brand(brand)
    return HTMLResponse(_page(
        f"{brand} susturuldu",
        f"<h1>✅ {brand} susturuldu</h1>"
        f"<p>Bu markaya ait <b>{n}</b> konuşma artık hatırlatılmayacak.<br>"
        f"Yeni mailler gelse bile bu marka digest'e girmez.</p>"
        f"<small>Tekrar açmak için Notion'da Brand Muted alanını kapatabilirsin.</small>",
    ))


@app.get("/snooze", response_class=HTMLResponse)
def snooze_form(token: str = ""):
    parsed = verify_token(token)
    if not parsed or parsed[0] != "snooze":
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş bağlantı")
    _, page_id = parsed

    rec = notion_threads.find_page_by_id(page_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Thread bulunamadı")

    brand = rec.get("brand") or "(marka adı yok)"
    subject = (rec.get("subject") or "")[:80]

    body = f"""
    <h1 style="color:#d97706">⏰ Ertele</h1>
    <p><b>{brand}</b><br><small>{subject}</small></p>
    <form method="post" action="/snooze/confirm?token={token}">
      <p>Kaç gün sonra tekrar hatırlatılsın?</p>
      <input type="number" name="days" min="1" max="60" value="3" required>
      <br><button type="submit">Ertele</button>
    </form>
    <small style="display:block;margin-top:14px">1–60 gün arası, iş günü değil takvim günü.</small>
    """
    return HTMLResponse(_page("Ertele", body, color="#d97706"))


@app.post("/snooze/confirm", response_class=HTMLResponse)
def snooze_confirm(token: str = "", days: int = Form(...)):
    parsed = verify_token(token)
    if not parsed or parsed[0] != "snooze":
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş bağlantı")
    _, page_id = parsed

    if days < 1 or days > 60:
        raise HTTPException(status_code=400, detail="Gün sayısı 1–60 arasında olmalı")

    until = datetime.utcnow() + timedelta(days=days)
    ok = notion_threads.set_snooze(page_id, until)
    if not ok:
        raise HTTPException(status_code=500, detail="Notion güncellenemedi")

    until_str = until.strftime("%d %b %Y")
    return HTMLResponse(_page(
        "Ertelendi",
        f"<h1 style='color:#d97706'>✅ {days} gün ertelendi</h1>"
        f"<p>{until_str} tarihinden önce tekrar hatırlatılmayacak.</p>",
        color="#d97706",
    ))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
