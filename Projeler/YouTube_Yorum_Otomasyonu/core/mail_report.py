# -*- coding: utf-8 -*-
"""Günlük yorum raporu — açık tema HTML mail (mail istemcisi koyu zemini ezer).

Faz 1: her cevaplanabilir yorum bir kart; "Yorumu Yanıtla" = YouTube derin linki.
Faz 2: AI taslağı varsa karta "Onayla ve Yayınla" (HMAC imzalı) butonu eklenir.
Gönderim: Resend + kendi doğrulanmış domain'in (DKIM/SPF/DMARC) -> rapor alıcısına.
"""
from __future__ import annotations

import html
import json
import hmac
import base64
import hashlib
from datetime import datetime, timezone, timedelta

import requests

import config


def _send_resend(subject: str, html_body: str, text_body: str) -> str:
    """Resend + kendi doğrulanmış domain'in (DKIM/SPF/DMARC) ile gönder.
    Gmail API kendine-gönderim DKIM imzalanmadığı için 'kimliği doğrulanamadı'
    uyarısı verebiliyor; Resend bunu çözer. Döner: Resend mesaj id'si."""
    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {config.RESEND_API_KEY}", "Content-Type": "application/json"},
        json={
            "from": config.REPORT_FROM,
            "to": [config.RECIPIENT],
            "reply_to": config.REPORT_REPLY_TO,
            "subject": subject,
            "html": html_body,
            "text": text_body,
        },
        timeout=30,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Resend HTTP {r.status_code}: {r.text[:200]}")
    return r.json().get("id", "?")


def send_failure_alert(reason: str) -> bool:
    """Koşu çökünce rapor alıcısına kısa, ürün dilinde uyarı; teknik sebep loga gider, maile değil.
    Subject 'YouTube yorumların' ile başlar ki mevcut mail etiketi kuralına düşsün."""
    print(f"⚠️ failure alert tetiklendi: {reason[:200]}")
    if config.DRY_RUN or not config.RESEND_API_KEY:
        return False
    html_body = (
        "<div style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
        "font-size:15px;color:#222;line-height:1.55;max-width:560px;margin:24px auto;\">"
        "<p>Bugünkü YouTube yorum taraman çalışmadı, bu yüzden yorum raporu gelmedi.</p>"
        "<p>Sistem bir sonraki zamanlamada yeniden deneyecek. Yapman gereken bir şey yok; "
        "sorun birkaç gün üst üste sürerse ayrıca haber veririm.</p>"
        "<p style=\"color:#999;font-size:12px;\">YouTube Yorum Otomasyonu</p></div>"
    )
    text = "Bugünkü YouTube yorum taraman çalışmadı, rapor gelmedi. Sistem yarın tekrar deneyecek."
    try:
        _send_resend("YouTube yorumların: bugün tarama çalışmadı", html_body, text)
        return True
    except Exception as e:
        print(f"⚠️ failure alert maili de gönderilemedi: {e}")
        return False


def deep_link(video_id: str, comment_id: str) -> str:
    """Yorumu watch sayfasında açar; kanal sahibi olarak orada cevaplanır."""
    return f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}"


def make_reply_url(comment_id: str, ttl_days: int = 14) -> str:
    """Faz 2: AI taslağını düzenleyip yayınlama sayfasının HMAC imzalı + SÜRELİ linki."""
    if not (config.APPROVAL_BASE_URL and config.APPROVAL_SECRET and comment_id):
        return ""
    exp = int((datetime.now(timezone.utc) + timedelta(days=ttl_days)).timestamp())
    payload = {"c": comment_id, "exp": exp}
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(config.APPROVAL_SECRET.encode(), p_b64.encode(), hashlib.sha256).hexdigest()
    return f"{config.APPROVAL_BASE_URL}/reply?t={p_b64}.{sig}"


def verify_reply_token(token: str) -> str | None:
    """make_reply_url token'ını doğrula. Geçerli + süresi dolmamışsa comment_id döner, yoksa None.
    Onay servisi (web/app.py) bununla aynı şemayı kullanır — tek kaynak."""
    if not (config.APPROVAL_SECRET and token and "." in token):
        return None
    p_b64, _, sig = token.partition(".")
    expected = hmac.new(config.APPROVAL_SECRET.encode(), p_b64.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        pad = "=" * (-len(p_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(p_b64 + pad))
    except (ValueError, json.JSONDecodeError):
        return None
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        return None
    return payload.get("c") or None


def _ago(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return ""
    secs = (datetime.now(timezone.utc) - dt).total_seconds()
    if secs < 3600:
        return f"{int(secs // 60)} dk önce"
    if secs < 86400:
        return f"{int(secs // 3600)} saat önce"
    return f"{int(secs // 86400)} gün önce"


def make_copy_url(c: dict) -> str:
    """Sade 'kopyala' sayfasının linki — cevap + YouTube derin linki hash'te taşınır (sunucusuz).
    Sayfa cevabı panoya kopyalar ve YouTube'u açar. Veri gizli değil (zaten herkese açık yorum)."""
    reply = (c.get("ai_draft") or "").strip()
    if not (config.COPY_PAGE_URL and reply):
        return ""
    payload = {
        "r": reply,
        "y": deep_link(c.get("video_id", ""), c.get("comment_id", "")),
        "a": (c.get("author") or "")[:80],
        "c": (c.get("text") or "")[:400],
        "t": (c.get("video_title") or "")[:80],
    }
    b = base64.urlsafe_b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode().rstrip("=")
    return f"{config.COPY_PAGE_URL}#d={b}"


def _btn(href: str, label: str, bg: str = "#16a34a") -> str:
    return (f'<a href="{href}" style="display:inline-block;background:{bg};color:#fff;'
            f'text-decoration:none;padding:11px 20px;border-radius:9px;font-size:15px;font-weight:700;">'
            f'{label}</a>')


def _card(c: dict) -> str:
    """Sade kart: yorum + önerilen cevap + TEK buton. Rozet/yıldız/beğeni/güven yok (kalabalık)."""
    author = html.escape(c.get("author", "") or "İzleyici")
    text = html.escape(c.get("text", "")).replace("\n", "<br>")
    vtitle = html.escape((c.get("video_title") or "video")[:80])
    ago = _ago(c.get("published_at", ""))
    tag = "Soru" if c.get("worth_kind") == "question" else ""
    meta = " · ".join(x for x in (tag, ago) if x)
    meta_html = f'<span style="color:#999;"> · {html.escape(meta)}</span>' if meta else ""

    draft = (c.get("ai_draft") or "").strip()
    if draft:
        draft_safe = html.escape(draft).replace("\n", "<br>")
        reply_block = (
            f'<div style="background:#f0fdf4;border-left:3px solid #16a34a;padding:10px 14px;'
            f'margin:10px 0;border-radius:6px;">'
            f'<div style="font-size:11px;color:#16a34a;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:.5px;margin-bottom:4px;">Önerilen cevap</div>'
            f'<div style="font-size:15px;color:#333;line-height:1.5;">{draft_safe}</div></div>'
        )
        copy_url = make_copy_url(c)
        if copy_url:
            btn = _btn(copy_url, "📋 Cevabı kopyala")
        else:  # link üretilemediyse (COPY_PAGE_URL yok) en azından YouTube'da yanıtla
            btn = _btn(deep_link(c.get("video_id", ""), c.get("comment_id", "")), "▶ YouTube'da yanıtla")
    else:
        # Taslak yoksa kopyalanacak bir şey yok — doğrudan YouTube'da elle yanıtla.
        reply_block = ""
        btn = _btn(deep_link(c.get("video_id", ""), c.get("comment_id", "")), "▶ Yorumu yanıtla", bg="#ef4444")

    return f"""
<tr><td style="padding:18px 0;border-bottom:1px solid #eee;">
  <div style="font-size:12px;color:#888;margin-bottom:6px;">📺 {vtitle}{meta_html}</div>
  <div style="font-size:15px;color:#222;line-height:1.55;margin-bottom:2px;"><b>{author}</b></div>
  <div style="font-size:15px;color:#333;line-height:1.55;margin-bottom:10px;">{text}</div>
  {reply_block}{btn}
</td></tr>"""


def build_html(cards: list[dict], total_new: int, corpus_ready: bool = False) -> str:
    # corpus_ready artık mailde gösterilmiyor (mühendislik sinyali — kalabalık yapıyordu).
    shown = cards[:config.MAX_EMAIL_CARDS]
    rows = "".join(_card(c) for c in shown)
    today = datetime.now().strftime("%d.%m.%Y")
    more = ""
    if total_new > len(shown):
        more = (f'<tr><td style="padding:12px 0;font-size:13px;color:#888;">'
                f'+ {total_new - len(shown)} yorum daha (en önemli {len(shown)} tanesi üstte).</td></tr>')
    intro = ("Her yorumun altında hazır bir cevap önerisi var. "
             "\"Cevabı kopyala\"ya bas, cevap kopyalanır ve YouTube açılır; sen sadece yapıştır.")
    return f"""<!DOCTYPE html>
<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f6f8fa;margin:0;padding:24px;">
  <table style="max-width:640px;margin:0 auto;background:#fff;border-radius:12px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
    <tr><td>
      <div style="font-size:13px;color:#888;text-transform:uppercase;letter-spacing:1px;">{today}</div>
      <h1 style="font-size:22px;color:#111;margin:6px 0 4px;">YouTube yorumların</h1>
      <p style="font-size:14px;color:#666;margin:0 0 4px;">{total_new} yorum cevabını bekliyor. En önemlileri üstte.</p>
      <p style="font-size:13px;color:#888;margin:0;">{intro}</p>
    </td></tr>
    {rows}
    {more}
    <tr><td style="padding-top:16px;font-size:12px;color:#999;">YouTube Yorum Otomasyonu</td></tr>
  </table>
</body></html>"""


def send_report(cards: list[dict], total_new: int, corpus_ready: bool) -> bool:
    if not cards:
        return False
    if config.DRY_RUN:
        print(f"[DRY_RUN] mail atılacaktı: {total_new} yorum, {len(cards)} kart")
        return False
    html_body = build_html(cards, total_new, corpus_ready)
    subject = f"YouTube yorumların hazır — {total_new} yeni"
    text = "\n\n".join(
        f"{c.get('author','')}: {c.get('text','')[:120]}\n"
        f"{deep_link(c.get('video_id',''), c.get('comment_id',''))}"
        for c in cards[:config.MAX_EMAIL_CARDS]
    )
    mid = _send_resend(subject, html_body, text)
    print(f"✅ Mail atıldı (Resend id={mid})")
    return True
