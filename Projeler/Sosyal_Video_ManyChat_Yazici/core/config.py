"""Merkezi config — varsa paket kök master.env + proje .env'inden env yükler.

Fail-fast: zorunlu anahtar eksikse boot'ta crash eder (deploy'da erken hata).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MASTER_ENV = PROJECT_ROOT.parent.parent / "_knowledge" / "credentials" / "master.env"
LOCAL_ENV = PROJECT_ROOT / ".env"

if MASTER_ENV.exists():
    load_dotenv(MASTER_ENV)
if LOCAL_ENV.exists():
    load_dotenv(LOCAL_ENV, override=False)


def _required(key: str, *alts: str) -> str:
    for k in (key, *alts):
        val = os.getenv(k)
        if val:
            return val
    raise RuntimeError(f"Env var eksik: {key} (master.env veya .env'de yok)")


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str
    notion_token: str
    notion_db_id: str
    # SADECE manuel yedek koşum için (main.py + core/llm.py). API'siz hatta (routine_io.py)
    # kullanılmaz. Maliyet bilinci: pahalı modeli varsayılan YAPMA; üst sınıf model istersen
    # MANYCHAT_MODEL env'i ile bilinçli seç.
    model: str
    # Tek koşumda işlenecek max video (maliyet + gözden geçirilebilirlik sınırı).
    max_videos: int
    # Script bu uzunluğun altındaysa video "metni yok" sayılır, atlanır.
    min_script_chars: int
    dry_run: bool

    @staticmethod
    def from_env() -> "Config":
        return Config(
            anthropic_api_key=_required("ANTHROPIC_API_KEY"),
            notion_token=_required("NOTION_SOCIAL_TOKEN", "NOTION_REELS_TOKEN", "NOTION_TOKEN"),
            notion_db_id=_required("NOTION_DB_REELS_KAPAK", "NOTION_DB_REELS", "NOTION_REELS_PROD_DB_ID"),
            model=os.getenv("MANYCHAT_MODEL", "claude-haiku-4-5"),
            max_videos=int(os.getenv("MAX_VIDEOS_PER_RUN", "5")),
            min_script_chars=int(os.getenv("MIN_SCRIPT_CHARS", "150")),
            dry_run=os.getenv("DRY_RUN", "0") == "1",
        )
