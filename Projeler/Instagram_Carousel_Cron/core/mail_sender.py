"""Carousel onay maili.

Twitter_Text_Paylasim/core/mail_sender.py pattern'ı + carousel-spesifik HTML grid.

Akış:
  - Notion'dan Status=Generated olanları çek
  - Her carousel için: slide thumbnail grid + caption preview + onay butonu
  - Gmail outreach (merkezi google_auth ile)

Token formatı twitter-onay-api ile uyumlu (HMAC-SHA256). Carousel için
ekstra `t=carousel` payload field'ı ile route edilir.
"""

import os
import sys
import json
import hmac
import html
import base64
import hashlib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import settings
from core.notion_repo import fetch_generated_for_mail
from ops_logger import get_ops_logger

ops = get_ops_logger("IG_Carousel_Cron", "Mail")


RECIPIENT = os.environ.get("APPROVAL_RECIPIENT_EMAIL", "<ADMIN_EMAIL>")
SENDER = os.environ.get("APPROVAL_SENDER_EMAIL", "<ADMIN_EMAIL>")


def _gmail_service():
    """Merkezi google_auth ile Gmail service döner (outreach hesabı)."""
    antigravity_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    sys.path.insert(0, os.path.join(
        antigravity_root, "_knowledge", "credentials", "oauth"
    ))
    from google_auth import get_gmail_service
    return get_gmail_service("outreach")


def _make_approval_url(row_id: str, title: str) -> str:
    """twitter-onay-api ile uyumlu HMAC token. t=carousel ile route ayrımı."""
    if not (settings.APPROVAL_BASE_URL and settings.APPROVAL_SECRET and row_id):
        return ""
    payload = {"t": "carousel", "r": row_id, "title": title[:80]}
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload, ensure_ascii=False).encode()
    ).decode().rstrip("=")
    sig = hmac.new(
        settings.APPROVAL_SECRET.encode(), payload_b64.encode(), hashlib.sha256
    ).hexdigest()
    return f"{settings.APPROVAL_BASE_URL}/approve-carousel?t={payload_b64}.{sig}"


def _build_carousel_card(carousel: dict) -> str:
    title = html.escape(carousel.get("title", "Untitled"))
    source = html.escape(carousel.get("source", "?"))
    score = carousel.get("score", "?")
    caption = carousel.get("caption") or ""
    slides = carousel.get("slides") or []
    approve_url = _make_approval_url(carousel.get("row_id", ""), carousel.get("title", ""))

    # Thumbnail grid (her satır 3 slide max)
    thumbs = []
    for s in slides:
        url = s.get("url", "")
        idx = s.get("index", "?")
        if not url:
            continue
        thumbs.append(f"""
<td style="padding:6px;width:33%;vertical-align:top;">
  <a href="{html.escape(url)}" style="text-decoration:none;">
    <img src="{html.escape(url)}" style="width:100%;border-radius:8px;display:block;" alt="Slide {idx}"/>
    <div style="font-size:11px;color:#888;text-align:center;margin-top:4px;">Slide {idx}</div>
  </a>
</td>""")

    # 3'lü satırlara grupla
    rows_html = []
    for i in range(0, len(thumbs), 3):
        chunk = thumbs[i:i + 3]
        # boş hücre doldur
        while len(chunk) < 3:
            chunk.append('<td style="width:33%;"></td>')
        rows_html.append(f"<tr>{''.join(chunk)}</tr>")
    grid_html = f'<table style="width:100%;border-collapse:separate;border-spacing:0;">{"".join(rows_html)}</table>'

    caption_preview_html = (
        html.escape(caption[:600] + ("…" if len(caption) > 600 else ""))
        .replace("\n", "<br>")
    )
    approve_btn = ""
    if approve_url:
        approve_btn = f"""
<a href="{approve_url}" style="display:inline-block;background:#16a34a;color:#fff;text-decoration:none;padding:12px 24px;border-radius:10px;font-size:15px;font-weight:600;margin-top:12px;">
  ✓ Onayla — Instagram'a Hazır Yap
</a>"""

    return f"""
<tr>
  <td style="padding:24px 0;border-bottom:1px solid #e5e7eb;">
    <div style="font-size:13px;color:#6b7280;margin-bottom:4px;">📷 {source} · {score}/10</div>
    <div style="font-size:18px;font-weight:700;color:#111827;margin-bottom:14px;">{title}</div>
    {grid_html}
    <div style="background:#f9fafb;border-left:3px solid #6366f1;padding:12px 14px;margin-top:14px;border-radius:6px;">
      <div style="font-size:11px;color:#6366f1;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Caption</div>
      <div style="font-size:13px;color:#374151;line-height:1.5;">{caption_preview_html}</div>
    </div>
    {approve_btn}
  </td>
</tr>"""


def _build_html(carousels: list[dict]) -> str:
    cards = "".join(_build_carousel_card(c) for c in carousels)
    today = datetime.now().strftime("%d %B %Y")
    return f"""<!DOCTYPE html>
<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f3f4f6;margin:0;padding:24px;">
<table style="max-width:680px;margin:0 auto;background:#fff;border-radius:14px;padding:32px;box-shadow:0 1px 6px rgba(0,0,0,0.06);">
  <tr><td>
    <div style="font-size:13px;color:#6b7280;text-transform:uppercase;letter-spacing:1.5px;">{today}</div>
    <h1 style="font-size:24px;color:#111827;margin:8px 0 4px;">Instagram Carousel Hazır</h1>
    <p style="font-size:14px;color:#6b7280;margin:0 0 16px;">{len(carousels)} carousel onayını bekliyor.</p>
  </td></tr>
  {cards}
  <tr><td style="padding-top:20px;font-size:12px;color:#9ca3af;">
    instagram-carousel-cron · Antigravity
  </td></tr>
</table>
</body></html>"""


def send_summary_mail(carousels: list[dict] | None = None) -> bool:
    if carousels is None:
        carousels = fetch_generated_for_mail(days=1)
    if not carousels:
        ops.info("Bugün generated carousel yok, mail atılmıyor")
        return False

    if settings.IS_DRY_RUN:
        ops.info(f"[DRY-RUN] Mail atılacaktı: {len(carousels)} carousel")
        return False

    try:
        service = _gmail_service()
    except Exception as e:
        ops.error("Gmail auth hatası", exception=e)
        return False

    subject = f"Instagram carousel onayı bekliyor ({len(carousels)})"
    html_body = _build_html(carousels)

    msg = MIMEMultipart("alternative")
    msg["to"] = RECIPIENT
    msg["from"] = SENDER
    msg["subject"] = subject
    text_fallback = "\n\n".join(
        f"{c['source']} ({c['score']}/10): {c['title']}\nSlides: {len(c.get('slides') or [])}"
        for c in carousels
    )
    msg.attach(MIMEText(text_fallback, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    try:
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        ops.success(f"Mail atıldı (id={result.get('id', '?')})")
        return True
    except Exception as e:
        ops.error("Gmail send exception", exception=e)
        return False
