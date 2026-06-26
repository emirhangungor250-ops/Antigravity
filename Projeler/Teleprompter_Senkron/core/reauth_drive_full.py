"""TAM Drive (drive) scope'lu bir OAuth token üretir.

Tam `drive` scope gerekli çünkü teleprompter uygulamasının KENDİ açtığı klasöre yazmamız
lazım; drive.file başka uygulamanın klasörünü göremez/yazamaz.

Hazırlık (bir kerelik):
  1. Google Cloud Console'da bir proje aç, Drive API'yi etkinleştir.
  2. "OAuth client ID" oluştur (tip: Desktop app). İnen JSON'u proje köküne
     `client_secret.json` adıyla koy.
  3. Bu script'i çalıştır: `python core/reauth_drive_full.py`
     Tarayıcı açılır, scriptlerinizin yazacağı Google hesabıyla "İzin ver"e basarsın.
  4. Token proje köküne `drive-full-token.json` olarak kaydedilir. Sunucuda/Actions'ta
     bu dosyanın içeriğini GOOGLE_DRIVE_TOKEN_JSON secret'ı olarak ver.
"""
from __future__ import annotations

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "client_secret.json"          # Google Cloud Console'dan inen OAuth client JSON
OUT = ROOT / "drive-full-token.json"       # üretilecek tam-drive token
SCOPES = ["https://www.googleapis.com/auth/drive"]


def main() -> None:
    if not SRC.exists():
        raise FileNotFoundError(
            f"OAuth client dosyası yok: {SRC}. Google Cloud Console'dan Desktop app "
            "OAuth client ID indirip proje köküne 'client_secret.json' olarak koyun."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(SRC), SCOPES)
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        authorization_prompt_message="Tarayıcı açılıyor — 'İzin ver'e bas: {url}",
        success_message="Tamamlandı! Bu sekmeyi kapatabilirsin.",
        open_browser=True,
    )
    OUT.write_text(creds.to_json())
    print(f"OK token kaydedildi: {OUT}")


if __name__ == "__main__":
    main()
