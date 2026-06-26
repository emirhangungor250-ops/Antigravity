"""Merkezi Google OAuth (Drive erişimi için).

Sadece `outreach` hesabını destekler; Drive scope yeterli (drive.file).
OAuth token'ı lokal'de _knowledge/credentials/oauth/ altında veya
Railway'de GOOGLE_OUTREACH_TOKEN_JSON env değişkeninde aranır.
"""

import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

_PRIMARY_OAUTH_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "_knowledge", "credentials", "oauth",
)
_FALLBACK_OAUTH_DIR = "/tmp/antigravity_creds/oauth"

if os.path.exists(_PRIMARY_OAUTH_DIR) and os.access(_PRIMARY_OAUTH_DIR, os.R_OK):
    OAUTH_DIR = _PRIMARY_OAUTH_DIR
elif os.path.exists(_FALLBACK_OAUTH_DIR):
    OAUTH_DIR = _FALLBACK_OAUTH_DIR
else:
    OAUTH_DIR = _PRIMARY_OAUTH_DIR

TOKEN_FILE = "gmail-outreach-token.json"
TOKEN_ENV_VAR = "GOOGLE_OUTREACH_TOKEN_JSON"

ALL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]


def _get_credentials() -> Credentials:
    token_path = os.path.join(OAUTH_DIR, TOKEN_FILE)
    loaded_from = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, ALL_SCOPES)
        loaded_from = "file"
    elif os.environ.get(TOKEN_ENV_VAR):
        token_json = json.loads(os.environ[TOKEN_ENV_VAR])
        creds = Credentials.from_authorized_user_info(token_json, ALL_SCOPES)
        loaded_from = "env"
    else:
        raise FileNotFoundError(
            f"Token bulunamadı. Lokal: {token_path}; Railway env: {TOKEN_ENV_VAR}."
        )

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            if loaded_from == "file":
                try:
                    _save_token(creds, token_path)
                except PermissionError:
                    pass
        else:
            raise RuntimeError("Token geçersiz ve yenilenemiyor. auth_helper.py outreach çalıştır.")

    return creds


def _save_token(creds: Credentials, token_path: str):
    data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else ALL_SCOPES,
        "universe_domain": "googleapis.com",
        "account": "",
        "expiry": creds.expiry.isoformat() + "Z" if creds.expiry else None,
    }
    with open(token_path, "w") as f:
        json.dump(data, f, indent=2)


def get_drive_service():
    return build("drive", "v3", credentials=_get_credentials())
