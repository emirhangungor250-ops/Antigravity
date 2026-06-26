"""
Personel Mail Hatırlatıcı — E-posta Bildirim Sistemi
======================================================
Tek bir digest mail gönderir: üç bölüm halinde.
- Yeni: bu run'da ilk kez hatırlatılan açık thread'ler (mail kaynaklı)
- Hala bekleyen: önceki digest'lerde de geçmiş, hala kapanmamış (mail kaynaklı)
- Pipeline: Notion pipeline'ında hareket bekleyen kartlar (mail dışı kanal, opsiyonel)

Her satırda iki tek-tıkla buton:
- 🔇 Sustur   → o taraf adına ait tüm thread'leri Brand Muted=true yapar
- ⏰ Ertele   → küçük HTML formda gün sayısı sorar, Snoozed Until set eder
"""

import os
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

from services.gmail_service import get_gmail_service
from services.token_signer import make_token

logger = logging.getLogger(__name__)

# Gmail OAuth ile gönderim — izlenen personel hesabı üzerinden
FROM_EMAIL = os.environ.get("STAFF_EMAIL", "staff@example.com")

# Alıcı: ALERT_EMAIL env'i. Ek izleyici: ALERT_CC (virgülle ayrılmış adresler).
REPORT_EMAIL = os.environ.get("ALERT_EMAIL", "admin@example.com")
REPORT_CC = [
    addr.strip()
    for addr in os.environ.get("ALERT_CC", "").split(",")
    if addr.strip()
]

WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL", "").rstrip("/")


def _send_email(to: str, subject: str, body_html: str, cc: list = None):
    cc = cc or []
    msg = MIMEMultipart("alternative")
    msg["From"] = FROM_EMAIL
    msg["To"] = to
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
    body = {'raw': raw_message}

    try:
        service = get_gmail_service()
        service.users().messages().send(userId='me', body=body).execute()
        cc_label = f" (cc: {', '.join(cc)})" if cc else ""
        logger.info(f"📧 E-posta gönderildi: {to}{cc_label} — {subject}")
    except Exception as e:
        logger.error(f"E-posta gönderilemedi: {to} — {e}", exc_info=True)
        raise


def _action_buttons_html(page_id: str) -> str:
    """Her satır için mute + snooze buton hücresi."""
    if not WEBHOOK_BASE_URL or not page_id:
        return ""
    try:
        mute_token = make_token("mute", page_id)
        snooze_token = make_token("snooze", page_id)
    except Exception as e:
        logger.warning(f"Token üretilemedi ({page_id}): {e}")
        return ""

    mute_url = f"{WEBHOOK_BASE_URL}/mute?token={mute_token}"
    snooze_url = f"{WEBHOOK_BASE_URL}/snooze?token={snooze_token}"
    return (
        f'<a href="{mute_url}" '
        f'style="display:inline-block;padding:5px 9px;margin-right:6px;'
        f'background:#fde2e2;color:#b91c1c;border-radius:5px;'
        f'font-size:12px;text-decoration:none;">🔇 Sustur</a>'
        f'<a href="{snooze_url}" '
        f'style="display:inline-block;padding:5px 9px;'
        f'background:#fef3c7;color:#b45309;border-radius:5px;'
        f'font-size:12px;text-decoration:none;">⏰ Ertele</a>'
    )


def _row_html(idx: int, item: Dict[str, Any]) -> str:
    """Mail kaynaklı tek satır HTML üretir."""
    brand = item.get("brand") or "Bilinmeyen Taraf"
    subj = item.get("subject") or "(Konu yok)"
    reason = item.get("reason") or "Cevap bekleniyor"
    days = item.get("business_days_open", "?")
    link = item.get("gmail_link") or "#"
    reminder_count = int(item.get("reminder_count") or 0)
    counter_label = (
        f"{reminder_count + 1}. kez hatırlatılıyor" if reminder_count > 0 else "İlk hatırlatma"
    )
    actions = _action_buttons_html(item.get("page_id", ""))

    return f"""
    <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 10px 8px; vertical-align: top; color:#999;">{idx}</td>
        <td style="padding: 10px 8px; vertical-align: top;">
            <strong>{brand}</strong>
            <div style="color:#666; font-size:13px; margin-top:2px;">{subj[:80]}</div>
            <div style="color:#999; font-size:11px; margin-top:2px;">{counter_label}</div>
        </td>
        <td style="padding: 10px 8px; vertical-align: top; color:#444; font-size:13px;">{reason}</td>
        <td style="padding: 10px 8px; vertical-align: top; white-space:nowrap;">{days} iş günü</td>
        <td style="padding: 10px 8px; vertical-align: top;">
            <a href="{link}" style="color:#1a73e8; text-decoration:none;">Aç →</a>
            <div style="margin-top:6px;">{actions}</div>
        </td>
    </tr>
    """


def _section_html(title: str, color: str, items: List[Dict[str, Any]]) -> str:
    if not items:
        return ""
    rows = "".join(_row_html(i + 1, item) for i, item in enumerate(items))
    return f"""
    <h3 style="color: {color}; margin-top: 28px; margin-bottom: 8px;">{title} ({len(items)})</h3>
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
        <thead>
            <tr style="background: #f7f7f7; text-align:left;">
                <th style="padding: 8px;">#</th>
                <th style="padding: 8px;">Taraf / Konu</th>
                <th style="padding: 8px;">Durum</th>
                <th style="padding: 8px;">Sessizlik</th>
                <th style="padding: 8px;">Aksiyon</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """


def _pipeline_row_html(idx: int, item: Dict[str, Any]) -> str:
    name = item.get("name") or "(başlık yok)"
    collab = item.get("collab") or ""
    status = item.get("status") or ""
    page_url = item.get("page_url") or "#"
    return f"""
    <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 10px 8px; vertical-align: top; color:#999;">{idx}</td>
        <td style="padding: 10px 8px; vertical-align: top;">
            <strong>{collab or name}</strong>
            <div style="color:#666; font-size:13px; margin-top:2px;">{name[:80]}</div>
        </td>
        <td style="padding: 10px 8px; vertical-align: top;">
            <span style="background:#eef2ff;color:#4338ca;padding:3px 8px;border-radius:4px;font-size:12px;">{status}</span>
        </td>
        <td style="padding: 10px 8px; vertical-align: top;">
            <a href="{page_url}" style="color:#1a73e8; text-decoration:none;">Notion'da aç →</a>
        </td>
    </tr>
    """


def _pipeline_section_html(items: List[Dict[str, Any]]) -> str:
    if not items:
        return ""
    rows = "".join(_pipeline_row_html(i + 1, it) for i, it in enumerate(items))
    return f"""
    <h3 style="color:#7c3aed; margin-top: 28px; margin-bottom: 8px;">📋 Pipeline'da hareket bekliyor ({len(items)})</h3>
    <p style="color:#666; font-size:13px; margin:0 0 8px 0;">
        Mail dışı kanaldan gelmiş, pipeline'da aksiyon bekleyen kartlar.
        Mail digest'inde görünmüyorlar — Notion kartında durum değişince otomatik düşer.
    </p>
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
        <thead>
            <tr style="background: #f7f7f7; text-align:left;">
                <th style="padding: 8px;">#</th>
                <th style="padding: 8px;">Taraf / Başlık</th>
                <th style="padding: 8px;">Status</th>
                <th style="padding: 8px;">Link</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """


def send_digest(
    new_items: List[Dict[str, Any]],
    ongoing_items: List[Dict[str, Any]],
    pipeline_items: List[Dict[str, Any]] = None,
):
    """
    Üç bölümlü digest gönder.
    new_items / ongoing_items: mail kaynaklı stale entries.
    pipeline_items: Notion pipeline'da olup mail digest'inde olmayan markalar.
    """
    pipeline_items = pipeline_items or []
    total = len(new_items) + len(ongoing_items) + len(pipeline_items)
    if total == 0:
        logger.info("Digest gönderilmiyor: ne mail ne pipeline kaynaklı açık iş var.")
        return

    parts = []
    if new_items:
        parts.append(f"{len(new_items)} yeni")
    if ongoing_items:
        parts.append(f"{len(ongoing_items)} devam eden")
    if pipeline_items:
        parts.append(f"{len(pipeline_items)} pipeline")
    subject = f"🔔 Personel Mail Takip: {' + '.join(parts)}"

    new_section = _section_html("🆕 Yeni gelenler", "#1a73e8", new_items)
    ongoing_section = _section_html("⏳ Hala bekleyenler", "#d97706", ongoing_items)
    pipeline_section = _pipeline_section_html(pipeline_items)

    body_html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 760px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333; margin-bottom: 6px;">🔔 Geciken Mailler Digest'i</h2>
        <p style="color: #666; font-size: 14px; margin-top: 0;">
            48+ iş saati cevapsız kalmış mailler + pipeline'da hareket bekleyen kartlar.
            Her satırda <b>🔇 Sustur</b> (tarafı kalıcı olarak listeden çıkar) ve
            <b>⏰ Ertele</b> (X gün boyunca gösterme) butonları var.
        </p>

        {new_section}
        {ongoing_section}
        {pipeline_section}

        <p style="color: #999; font-size: 12px; margin-top: 32px; border-top: 1px solid #eee; padding-top: 14px;">
            Susturduğun taraf Notion'da <code>Brand Muted</code> alanından geri açılabilir.<br>
            Personel Mail Hatırlatıcı
        </p>
    </div>
    """

    _send_email(REPORT_EMAIL, subject, body_html, cc=REPORT_CC)
    cc_summary = f" + cc {','.join(REPORT_CC)}" if REPORT_CC else ""
    logger.info(
        f"✅ Digest: {len(new_items)} yeni + {len(ongoing_items)} devam + "
        f"{len(pipeline_items)} pipeline → {REPORT_EMAIL}{cc_summary}"
    )
