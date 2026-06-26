"""Gmail API üzerinden mail gönderimi."""
from __future__ import annotations
import base64
import os
import sys
from email.mime.text import MIMEText

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_auth import get_gmail_service  # noqa: E402

from config import GMAIL_ACCOUNT, SENDER_EMAIL, SENDER_NAME


def send_mail(to_email: str, subject: str, body_text: str) -> str:
    """Mail gönder, Gmail message id döndür."""
    svc = get_gmail_service(GMAIL_ACCOUNT)
    msg = MIMEText(body_text, "plain", "utf-8")
    msg["To"] = to_email
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = svc.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()
    return sent.get("id", "")
