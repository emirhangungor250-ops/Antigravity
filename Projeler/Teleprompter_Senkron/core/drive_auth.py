"""Google Drive erişimi (TAM drive scope, refresh token).

Lokal: proje kökündeki drive-full-token.json dosyasından okur.
GitHub Actions/sunucu: GOOGLE_DRIVE_TOKEN_JSON env değişkeninden (tek satır JSON) okur.

Neden TAM drive (drive.file değil): teleprompter uygulamasının KENDİ açtığı klasöre
yazıyoruz. drive.file başka uygulamanın oluşturduğu klasörü göremez/yazamaz; o yüzden
tam drive scope'lu AYRI bir token kullanılır (paylaşılan başka token'ları bozmaz).
Token'ı core/reauth_drive_full.py üretir.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive"]
ENV_VAR = "GOOGLE_DRIVE_TOKEN_JSON"

# Lokal token yolu (proje kökünde). Sunucuda bulunmaz, env'e düşer.
_LOCAL_TOKEN: Path = Path(__file__).resolve().parents[1] / "drive-full-token.json"


def _credentials() -> Credentials:
    raw = os.environ.get(ENV_VAR)
    if raw:
        creds = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)
    elif _LOCAL_TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(_LOCAL_TOKEN), SCOPES)
    else:
        raise FileNotFoundError(
            f"Drive token yok: ne {ENV_VAR} env ne de {_LOCAL_TOKEN} mevcut."
        )

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError("Drive token geçersiz ve yenilenemiyor.")
    return creds


def drive_service():
    return build("drive", "v3", credentials=_credentials(), cache_discovery=False)


def authed_email(service) -> str:
    return service.about().get(fields="user(emailAddress)").execute()["user"]["emailAddress"]
