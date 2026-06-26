"""Self-contained Google OAuth helper (Gmail + Sheets).

İki OAuth token kullanır:
  - GMAIL_TOKEN_JSON   → mail gönderim hesabı (gmail.send scope)
  - SHEETS_TOKEN_JSON  → Google Sheet okuma/yazma hesabı (spreadsheets scope)

Token'lar Railway'de env var olarak JSON string halinde tutulur.
Lokal'de aynı env var'ları .env üzerinden yükleyebilir veya
data/ altındaki dosyalardan okuyabilirsin.

Aynı hesap hem mail hem sheet için kullanılacaksa iki env var'a aynı token'ı koy.
"""
from __future__ import annotations
import json
import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# account adı → (env var, lokal dosya, scope) eşlemesi
_PROFILES = {
    "gmail": ("GMAIL_TOKEN_JSON", "data/gmail-token.json", GMAIL_SCOPES),
    "sheets": ("SHEETS_TOKEN_JSON", "data/sheets-token.json", SHEETS_SCOPES),
}


def _load_credentials(account: str) -> Credentials:
    if account not in _PROFILES:
        raise ValueError(f"Bilinmeyen hesap: {account!r}. Geçerli: {list(_PROFILES)}")
    env_var, local_file, scopes = _PROFILES[account]

    raw = os.environ.get(env_var)
    if raw:
        creds = Credentials.from_authorized_user_info(json.loads(raw), scopes)
    else:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), local_file)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{account} token bulunamadı: ne {env_var} env'i ne de {path} mevcut."
            )
        creds = Credentials.from_authorized_user_file(path, scopes)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError(f"{account} token geçersiz ve yenilenemiyor")
    return creds


def get_gmail_service(account: str = "gmail"):
    """Gmail API service objesi döndür."""
    creds = _load_credentials(account)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def get_sheets_service(account: str = "sheets"):
    """Google Sheets API service objesi döndür."""
    creds = _load_credentials(account)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)
