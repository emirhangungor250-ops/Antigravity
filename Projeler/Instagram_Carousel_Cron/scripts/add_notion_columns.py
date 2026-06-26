"""Bir kerelik migration: Twitter_Text_Paylasim Notion DB'sine carousel
property'lerini ekle.

Mevcut property'lere dokunmaz. Idempotent — daha önce eklenmiş property'ler
PATCH'te ignore edilir.

Kullanım:
    python -m scripts.add_notion_columns
veya
    RUN_MODE=migrate python main.py
"""

import sys
from pathlib import Path

# Allow running both as module and script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import requests

from config import settings
from ops_logger import get_ops_logger

ops = get_ops_logger("IG_Carousel_Cron", "Migrate")

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


CAROUSEL_PROPERTIES = {
    "Carousel Status": {
        "select": {
            "options": [
                {"name": "Pending", "color": "gray"},
                {"name": "Generating", "color": "yellow"},
                {"name": "Generated", "color": "blue"},
                {"name": "Approved", "color": "green"},
                {"name": "Failed", "color": "red"},
            ]
        }
    },
    "Carousel Slides": {"rich_text": {}},        # JSON array of slide URLs + texts
    "Instagram Caption": {"rich_text": {}},
    "Carousel Generated At": {"date": {}},
    "Carousel Approved At": {"date": {}},
}


def fetch_db_schema() -> dict:
    headers = {
        "Authorization": f"Bearer {settings.NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
    }
    r = requests.get(
        f"{NOTION_API}/databases/{settings.NOTION_X_DB_ID}",
        headers=headers,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def add_missing_properties() -> int:
    """Eksik carousel property'lerini DB'ye ekler. Eklenen sayısını döner."""
    schema = fetch_db_schema()
    existing = set(schema.get("properties", {}).keys())

    to_add = {k: v for k, v in CAROUSEL_PROPERTIES.items() if k not in existing}
    if not to_add:
        ops.info("Migration: tüm property'ler zaten var, atlanıyor")
        return 0

    headers = {
        "Authorization": f"Bearer {settings.NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    payload = {"properties": to_add}
    r = requests.patch(
        f"{NOTION_API}/databases/{settings.NOTION_X_DB_ID}",
        headers=headers,
        json=payload,
        timeout=20,
    )
    if r.status_code not in (200, 201):
        ops.error(f"Notion DB patch fail ({r.status_code})", message=r.text[:400])
        raise RuntimeError(f"Notion patch failed: {r.status_code}")

    ops.success(f"Migration: {len(to_add)} property eklendi", message=", ".join(to_add.keys()))
    return len(to_add)


def main():
    ops.info("Migration başladı", "Twitter DB'ye carousel property'leri eklenecek")
    try:
        n = add_missing_properties()
        ops.info("Migration bitti", f"{n} yeni property")
    except Exception as e:
        ops.error("Migration exception", exception=e)
        sys.exit(1)


if __name__ == "__main__":
    main()
