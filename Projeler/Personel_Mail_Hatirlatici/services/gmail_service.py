"""
Personel Mail Hatırlatıcı — Gmail API Servis Wrapper
======================================================
OAuth2 ile Gmail API erişimi sağlar.
Hem lokal (token dosyası) hem Railway (env var) ortamında çalışır.

Tek bir gelen kutusunu izler. Hangi hesap izleneceği STAFF_EMAIL env var'ı
ile belirlenir; OAuth token GMAIL_TOKEN_JSON env var'ından (Railway) veya
data/gmail-token.json dosyasından (lokal) okunur.
"""

import os
import json
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Lokal token dosyası — proje köküne göre
TOKEN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
TOKEN_FILE = os.path.join(TOKEN_DIR, "gmail-token.json")
TOKEN_ENV = "GMAIL_TOKEN_JSON"

ALL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
]


def _get_credentials() -> Credentials:
    """Token al — lokal dosya veya Railway env variable."""
    loaded_from = None

    # 1) Lokal dosya
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, ALL_SCOPES)
        loaded_from = "file"
    # 2) Railway env variable (JSON string)
    elif os.environ.get(TOKEN_ENV):
        token_json = json.loads(os.environ[TOKEN_ENV])
        creds = Credentials.from_authorized_user_info(token_json, ALL_SCOPES)
        loaded_from = "env"
    else:
        raise FileNotFoundError(
            f"Token bulunamadı: ne dosya ({TOKEN_FILE}) ne de env ({TOKEN_ENV}) mevcut."
        )

    # Süresi dolmuşsa yenile
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            if loaded_from == "file":
                _save_token(creds)
            logger.info("Gmail token yenilendi")
        else:
            raise RuntimeError("Gmail token geçersiz ve yenilenemiyor")

    return creds


def _save_token(creds: Credentials):
    """Yenilenen token'ı dosyaya kaydet."""
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else ALL_SCOPES,
        "universe_domain": "googleapis.com",
        "expiry": creds.expiry.isoformat() + "Z" if creds.expiry else None,
    }
    os.makedirs(TOKEN_DIR, exist_ok=True)
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)


def get_gmail_service(account: str = None):
    """Gmail API service objesi döndür. (account parametresi geriye dönük uyumluluk için.)"""
    creds = _get_credentials()
    service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
    logger.debug("Gmail service hazır")
    return service
