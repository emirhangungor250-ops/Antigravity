"""
Google OAuth Yardımcısı — Drive yükleme için token yönetimi
===========================================================
Bu modül Google API (Drive) erişimi sağlar. Token'lar lokal bir dosyada
saklanır veya bir environment variable'dan okunur, gerekirse otomatik yenilenir.

Desteklenen ortamlar:
  - Lokal: _knowledge/credentials/oauth/ dizinindeki token dosyası
  - Railway/Cloud: GOOGLE_OUTREACH_TOKEN_JSON environment variable'ından
    JSON string olarak okunur

Kullanım:
    from core.google_auth import get_drive_service
    drive = get_drive_service()   # bölümleri Drive'a yükler

Token nasıl üretilir:
    Kendi Google Cloud projende OAuth credential oluştur, drive.file scope'u ile
    yetkilendir, dönen token JSON'ını ya aşağıdaki dosya yoluna koy ya da
    GOOGLE_OUTREACH_TOKEN_JSON env değişkenine yapıştır.
"""

import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Öncelik 1: paket içindeki _knowledge dizini (paket köküne göre dinamik)
_PRIMARY_OAUTH_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "_knowledge", "credentials", "oauth")
# Öncelik 2: /tmp/ köprüsü (sandbox kullanıcıları için)
_FALLBACK_OAUTH_DIR = "/tmp/oauth_creds"

# Hangisi erişilebilir ise onu kullan
if os.path.exists(_PRIMARY_OAUTH_DIR) and os.access(_PRIMARY_OAUTH_DIR, os.R_OK):
    OAUTH_DIR = _PRIMARY_OAUTH_DIR
elif os.path.exists(_FALLBACK_OAUTH_DIR):
    OAUTH_DIR = _FALLBACK_OAUTH_DIR
else:
    OAUTH_DIR = _PRIMARY_OAUTH_DIR  # default fallback

# Hesap → token dosyası eşlemesi (tek jenerik hesap; istersen çoğaltabilirsin)
TOKEN_FILES = {
    "outreach": "gmail-outreach-token.json",
}

# Hesap → environment variable eşlemesi
TOKEN_ENV_VARS = {
    "outreach": "GOOGLE_OUTREACH_TOKEN_JSON",
}

ALL_SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
]


def _get_credentials(account: str = "outreach") -> Credentials:
    """
    Token deposundan credentials al ve gerekirse yenile.

    Öncelik sırası:
      1. Lokal dosya: _knowledge/credentials/oauth/gmail-{account}-token.json
      2. Environment variable: GOOGLE_{ACCOUNT}_TOKEN_JSON (Railway/Cloud)

    Returns:
        Geçerli Google OAuth Credentials objesi

    Raises:
        FileNotFoundError: Token ne dosyada ne env'de bulunamazsa
        ValueError: Bilinmeyen hesap adı
    """
    if account not in TOKEN_FILES:
        raise ValueError(
            f"Bilinmeyen hesap: '{account}'. "
            f"Geçerli hesaplar: {', '.join(TOKEN_FILES.keys())}"
        )

    token_path = os.path.join(OAUTH_DIR, TOKEN_FILES[account])
    env_var = TOKEN_ENV_VARS[account]
    loaded_from = None

    # 1) Lokal dosyadan oku
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, ALL_SCOPES)
        loaded_from = "file"
    # 2) Environment variable'dan oku (Railway/Cloud)
    elif os.environ.get(env_var):
        token_json = json.loads(os.environ[env_var])
        creds = Credentials.from_authorized_user_info(token_json, ALL_SCOPES)
        loaded_from = "env"
    else:
        raise FileNotFoundError(
            f"Token bulunamadı: Ne dosya ({token_path}) ne de env ({env_var}) mevcut.\n"
            f"Lokal çözüm: token JSON'ını {token_path} yoluna koy.\n"
            f"Railway çözüm: {env_var} env variable'ını token JSON'ı ile set et."
        )

    # Token süresi dolmuşsa otomatik yenile
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Yenilenen token'ı kaydet (sadece dosya varsa)
            if loaded_from == "file":
                try:
                    _save_token(creds, token_path)
                except PermissionError:
                    pass  # Sandbox ortamında dosyaya yazılamaz, sorun değil
        else:
            raise RuntimeError(
                f"Token geçersiz ve yenilenemiyor. "
                f"Yeni bir OAuth token üret ve {token_path} yoluna koy."
            )

    return creds


def _save_token(creds: Credentials, token_path: str):
    """Yenilenen token'ı dosyaya kaydet."""
    token_data = {
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
    with open(token_path, 'w') as f:
        json.dump(token_data, f, indent=2)


def get_drive_service(account: str = "outreach"):
    """Google Drive API service objesi döndür."""
    return build('drive', 'v3', credentials=_get_credentials(account))


if __name__ == "__main__":
    # Quick test
    print("Google Auth modül testi...\n")
    for acc in TOKEN_FILES:
        try:
            creds = _get_credentials(acc)
            print(f"  OK {acc}: Token gecerli")
            print(f"     Scopes: {len(creds.scopes)} izin")
            print(f"     Expiry: {creds.expiry}")
        except Exception as e:
            print(f"  HATA {acc}: {e}")
        print()
