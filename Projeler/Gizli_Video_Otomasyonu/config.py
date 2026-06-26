"""Merkezi ayarlar + yol/kimlik çözümleme.

Yeni gizli (unlisted) YouTube videosu yüklenince kapak + açıklama üretip
Drive'a koyan, sonra ekibe haber veren köprü servisi.

Yaratıcı iş sıfırdan değil: açıklama bu paketteki Youtube_Aciklama_Otomasyonu
motorunu, kapak bu paketteki Otonom_Kapak_Uretici motorunu kullanır. Bu servis
sadece tespit + eşleştirme + transkript + tetikleme + haber işini yapar.

Komşu motorların klasör adları env ile değiştirilebilir; varsayılanlar bu paketteki
isimlerdir. Kanal/Notion/alıcı gibi her sahibe özel değerler de env'den okunur.
"""
import os
from pathlib import Path


def _find_repo_root() -> Path:
    """Paket kökünü bulur (içinde 'Projeler' + '_knowledge' olan en yakın üst klasör)."""
    p = Path(__file__).resolve()
    for anc in [p] + list(p.parents):
        if (anc / "Projeler").is_dir() and (anc / "_knowledge").is_dir():
            return anc
    return p.parents[2]


REPO_ROOT = _find_repo_root()
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Komşu motorlar (yeniden kullanım) — klasör adlarını env ile değiştirebilirsin.
ACIKLAMA_ENGINE_DIR_NAME = os.getenv("ACIKLAMA_ENGINE_DIR_NAME", "Youtube_Aciklama_Otomasyonu")
KAPAK_ENGINE_DIR_NAME = os.getenv("KAPAK_ENGINE_DIR_NAME", "Otonom_Kapak_Uretici")
YT_ACIKLAMA_DIR = REPO_ROOT / "Projeler" / ACIKLAMA_ENGINE_DIR_NAME
KAPAK_DIR = REPO_ROOT / "Projeler" / KAPAK_ENGINE_DIR_NAME

# Kanal + Notion (kendi değerlerini .env'de ver)
CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "<YOUTUBE_CHANNEL_ID>")
NOTION_DB = os.getenv("NOTION_DB_REELS_YT", "<NOTION_DB_ID>")

# YouTube sahip token'ı (kanalı okuma + altyazı indirme).
# Railway'de token JSON'unun tamamını env'e koy; lokal'de bir komşu YouTube projesiyle
# ortak token dosyası kullanabilirsin (klasör adını env ile ver).
FORCESSL_TOKEN_ENV = "YOUTUBE_FORCESSL_TOKEN_JSON"
FORCESSL_PROJECT_DIR_NAME = os.getenv("FORCESSL_PROJECT_DIR_NAME", "YouTube_Otomasyonu")
FORCESSL_TOKEN_FILE = REPO_ROOT / "Projeler" / FORCESSL_PROJECT_DIR_NAME / "youtube_forcessl_token.json"

# Drive yazma + mail için Google token'ı (drive.file + gmail.send)
OUTREACH_TOKEN_ENV = "GOOGLE_OUTREACH_TOKEN_JSON"
OUTREACH_TOKEN_FILE = REPO_ROOT / "_knowledge" / "credentials" / "oauth" / "google-oauth-token.json"

# Eşleştirme güven eşiği. Bunun altı = körlemesine yazma, insan onayı istenir.
MATCH_MIN_SCORE = float(os.getenv("MATCH_MIN_SCORE", "0.45"))
MATCH_MIN_GAP = float(os.getenv("MATCH_MIN_GAP", "0.12"))

# Haber alıcıları (virgülle birden çok adres verebilirsin)
NOTIFY_EMAILS = [e.strip() for e in os.getenv("NOTIFY_EMAILS", "").split(",") if e.strip()]
# Belirsiz eşleşmede "kime sorulacağı" — boşsa ilk NOTIFY_EMAILS adresine sorulur.
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip()

# Güvenlik: varsayılan KURU çalışma. Canlı için DRY_RUN=0.
DRY_RUN = os.getenv("DRY_RUN", "1") != "0"

GLOSSARY_PATH = DATA_DIR / "glossary.json"
STATE_PATH = DATA_DIR / "processed.json"
