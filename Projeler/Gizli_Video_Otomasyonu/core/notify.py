"""Ekibe haber maili (Google hesabı, gmail.send)."""
import base64
import json
import os
from email.mime.text import MIMEText

from config import NOTIFY_EMAILS, OUTREACH_TOKEN_ENV, OUTREACH_TOKEN_FILE


def _gmail():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    raw = os.getenv(OUTREACH_TOKEN_ENV)
    d = json.loads(raw) if raw else json.loads(OUTREACH_TOKEN_FILE.read_text(encoding="utf-8"))
    c = Credentials(token=d.get("token"), refresh_token=d.get("refresh_token"),
                    token_uri=d.get("token_uri"), client_id=d.get("client_id"),
                    client_secret=d.get("client_secret"), scopes=d.get("scopes"))
    c.refresh(Request())
    return build("gmail", "v1", credentials=c, cache_discovery=False)


def send(subject: str, html_body: str, to: list[str] | None = None) -> dict:
    to = to or NOTIFY_EMAILS
    msg = MIMEText(html_body, "html", "utf-8")
    msg["to"] = ", ".join(to)
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return _gmail().users().messages().send(userId="me", body={"raw": raw}).execute()


def ready_email(video_title: str, drive_folder_url: str, doc_link: str | None) -> tuple[str, str]:
    """Kapak + açıklama hazır maili (müşteri/ekip diline yakın, açık tema)."""
    subject = f"Yeni video hazır: {video_title}"
    doc_line = f'<p>Açıklama metni: <a href="{doc_link}">buradan aç</a></p>' if doc_link else ""
    body = f"""
    <div style="font-family:Arial,sans-serif;font-size:15px;color:#222">
      <p>Merhaba,</p>
      <p><b>{video_title}</b> videosu için kapaklar ve açıklama hazırlandı.</p>
      <p>Hepsi videonun Drive klasöründe: <a href="{drive_folder_url}">klasörü aç</a></p>
      {doc_line}
      <p>Kapaklar klasördeki <b>THUMBNAIL</b> alt klasöründe.</p>
      <p>Kolay gelsin.</p>
    </div>"""
    return subject, body
