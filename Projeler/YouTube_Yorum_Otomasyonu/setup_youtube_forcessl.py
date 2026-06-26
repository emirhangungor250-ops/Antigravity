#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Faz 2 — YouTube 'yorum yazma' izni (youtube.force-ssl) TEK SEFERLİK kurulum.

Çalıştır (proje kökünden):  python setup_youtube_forcessl.py
Tarayıcı açılır; KENDİ YouTube hesabınla (kanal sahibi) onay verirsin. Sadece bir kez.

Çıktı: refresh_token'lı token JSON
  - dosyaya yazılır  (youtube_forcessl_token.json — lokal kullanım, .gitignore'da)
  - ekrana basılır   (production env YOUTUBE_FORCESSL_TOKEN_JSON'a yapıştırmak için)

Client id/secret env'den gelir (YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET).
"""
import json
import sys

import config

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def main() -> int:
    if not (config.YOUTUBE_CLIENT_ID and config.YOUTUBE_CLIENT_SECRET):
        print("❌ YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET yok (.env). Önce onları ekle.")
        return 1
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("❌ google-auth-oauthlib kurulu değil. Kur:  pip install google-auth-oauthlib")
        return 1

    client_config = {
        "installed": {
            "client_id": config.YOUTUBE_CLIENT_ID,
            "client_secret": config.YOUTUBE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    # access_type=offline + prompt=consent => kalıcı refresh_token
    creds = flow.run_local_server(port=8765, open_browser=True,
                                  access_type="offline", prompt="consent")

    if not creds.refresh_token:
        print("⚠️ refresh_token gelmedi (muhtemelen daha önce onay verilmiş). "
              "Google Hesabı > Güvenlik > Üçüncü taraf erişimi'nden uygulamayı kaldırıp tekrar dene.")

    token = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or SCOPES),
    }
    with open(config.YT_TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(token, f, indent=2)

    print(f"\n✅ Token kaydedildi: {config.YT_TOKEN_PATH}")
    print("\n── Production env'e yapıştır (YOUTUBE_FORCESSL_TOKEN_JSON) ──")
    print(json.dumps(token))
    return 0


if __name__ == "__main__":
    sys.exit(main())
