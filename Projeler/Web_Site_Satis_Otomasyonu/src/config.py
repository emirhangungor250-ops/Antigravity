"""
Merkezi konfigürasyon — env okuma, Apify fail-over, Notion bağlantı bilgileri.
"""
from __future__ import annotations

import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("web_satis")

# ---------------------------------------------------------------------------
# ENV dosyasından oku  (.env → lokal geliştirme)
# ---------------------------------------------------------------------------
ENV_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


def _load_env(path: str) -> dict[str, str]:
    """.env dosyasından key=value satırlarını parse et."""
    env = {}
    if not os.path.exists(path):
        logger.warning(".env bulunamadı: %s", path)
        return env
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip().strip("\"'")
    return env


_env = _load_env(ENV_FILE_PATH)


def get(key: str, default: str | None = None) -> str | None:
    """Önce os.environ, sonra .env dosyasından oku."""
    return os.environ.get(key) or _env.get(key) or default


# ---------------------------------------------------------------------------
# Apify — fail-over destekli
# ---------------------------------------------------------------------------
APIFY_API_KEY_1 = get("APIFY_API_KEY_1")
APIFY_API_KEY_2 = get("APIFY_API_KEY_2")

if not APIFY_API_KEY_1:
    raise EnvironmentError("APIFY_API_KEY_1 eksik! .env dosyanizi kontrol edin.")

# ---------------------------------------------------------------------------
# Notion
# ---------------------------------------------------------------------------
NOTION_TOKEN = get("NOTION_API_TOKEN")
if not NOTION_TOKEN:
    raise EnvironmentError("NOTION_API_TOKEN eksik! .env dosyanizi kontrol edin.")

# Notion kokpit sayfası — kendi Notion sayfa ID'nizi .env'e girin
NOTION_COCKPIT_PAGE_ID = get("NOTION_COCKPIT_PAGE_ID")

# Lead Onay DB ID — ilk çalıştırmada oluşturulacak ve buraya set edilecek
NOTION_LEAD_DB_ID: str | None = get("NOTION_LEAD_DB_ID")

# ---------------------------------------------------------------------------
# Apify Google Maps Scraper Actor ID
# ---------------------------------------------------------------------------
APIFY_ACTOR_ID = "nwua9Gu5YrADL7ZDj"

# ---------------------------------------------------------------------------
# Scoring eşikleri
# ---------------------------------------------------------------------------
SCORE_THRESHOLD_MIN = 50       # altı otomatik elenir
SCORE_THRESHOLD_HIGH = 70      # üstü yüksek öncelik

# ---------------------------------------------------------------------------
# Supabase (ANA Logger — Gölge Modu)
# ---------------------------------------------------------------------------
SUPABASE_URL = get("SUPABASE_URL")
SUPABASE_KEY = get("SUPABASE_ANON_KEY")
# Yoksa logger disabled modda çalışır — ana akışı etkilemez

# ---------------------------------------------------------------------------
# Günlük limitler
# ---------------------------------------------------------------------------
MAX_PLACES_PER_SEARCH = 5      # MVP test limiti (prodda 200-300)
