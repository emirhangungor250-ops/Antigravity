"""Notion 'Reels & YouTube' DB'sini okur/yazar.

DB ID: NOTION_DB_YOUTUBE_ISBIRLIKLERI (env)
   (Reels ve YouTube videoları aynı DB'de; YouTube ayrımı page icon ile yapılır:
    icon.custom_emoji.name == 'youtube_logo' → YouTube)

Tetikleyici: Durum = "Yayınlandı" + icon=youtube_logo + URL dolu + Drive dolu.
İdempotency check Drive klasöründe yapılır (find_existing_draft).
"""

import os
import re
from typing import Optional
import requests

NOTION_VERSION = "2022-06-28"
DEFAULT_TIMEOUT = 30
YOUTUBE_ICON_NAME = "youtube_logo"
# Notion DB'deki select property adı "Durum"; yayına çıkmış videolar "Yayınlandı".
STATUS_PROPERTY = "Durum"
READY_STATUSES = ["Yayınlandı"]


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def _get_token() -> str:
    return (
        os.getenv("NOTION_SOCIAL_TOKEN")
        or os.getenv("NOTION_API_TOKEN")
        or os.getenv("NOTION_TOKEN")
        or ""
    )


def _get_db_id() -> str:
    return os.getenv("NOTION_DB_YOUTUBE_ISBIRLIKLERI", "")


def _extract_text(prop: dict) -> str:
    """rich_text / title / url property'sinden düz metin çek."""
    if not prop:
        return ""
    if prop.get("type") == "title":
        return "".join(t.get("plain_text", "") for t in prop.get("title", []))
    if prop.get("type") == "rich_text":
        return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))
    if prop.get("type") == "url":
        return prop.get("url") or ""
    return ""


def _is_youtube_url(url: str) -> bool:
    if not url:
        return False
    return bool(re.search(r"(youtube\.com|youtu\.be)/", url))


def _is_youtube_page(item: dict) -> bool:
    """Sayfa icon'u 'youtube_logo' custom_emoji'si ise YouTube videosudur."""
    icon = item.get("icon") or {}
    if icon.get("type") != "custom_emoji":
        return False
    return (icon.get("custom_emoji") or {}).get("name") == YOUTUBE_ICON_NAME


def get_published_videos() -> list[dict]:
    """Status='Yayına Hazır' (veya benzer ready statuses) + icon=youtube_logo satırları döndürür."""
    token = _get_token()
    db_id = _get_db_id()
    if not token or not db_id:
        print("[notion] NOTION_SOCIAL_TOKEN veya NOTION_DB_YOUTUBE_ISBIRLIKLERI eksik.")
        return []

    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    status_filters = [{"property": STATUS_PROPERTY, "select": {"equals": s}} for s in READY_STATUSES]
    payload = {
        "filter": {"or": status_filters} if len(status_filters) > 1 else status_filters[0],
        "page_size": 100,
    }
    try:
        r = requests.post(url, headers=_headers(token), json=payload, timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:
            print(f"[notion] query error {r.status_code}: {r.text[:200]}")
            return []
        results = r.json().get("results", [])
    except Exception as e:
        print(f"[notion] query exception: {e}")
        return []

    videos: list[dict] = []
    for item in results:
        if not _is_youtube_page(item):
            continue
        props = item.get("properties", {})
        video_name = _extract_text(props.get("Name", {})) or _extract_text(props.get("Başlık", {}))
        video_url = _extract_text(props.get("URL", {}))
        drive_url = _extract_text(props.get("Drive", {}))
        brief_url = _extract_text(props.get("Breif", {}))

        if not _is_youtube_url(video_url):
            continue
        if not drive_url:
            continue

        videos.append({
            "page_id": item["id"],
            "video_name": video_name or "Adsız",
            "video_url": video_url,
            "drive_url": drive_url,
            "brief_url": brief_url,
        })
    print(f"[notion] Hazır YT + URL + Drive dolu satır: {len(videos)}")
    return videos


def get_page_content(page_id: str) -> str:
    """Sayfa body'sindeki tüm rich_text bloklarını düz metin olarak birleştir."""
    token = _get_token()
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    try:
        r = requests.get(url, headers=_headers(token), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:
            return ""
        data = r.json()
    except Exception as e:
        print(f"[notion] page content exception: {e}")
        return ""

    lines: list[str] = []
    for block in data.get("results", []):
        btype = block.get("type")
        if not btype or btype not in block:
            continue
        rt = block[btype].get("rich_text", []) if isinstance(block[btype], dict) else []
        text = "".join(t.get("plain_text", "") for t in rt)
        if text:
            lines.append(text)
    return "\n".join(lines).strip()


def append_status_block(page_id: str, message: str, is_error: bool = False) -> bool:
    """Sayfa altına başarı/hata bilgisi paragraph block'u ekler."""
    token = _get_token()
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    prefix = "❌ Açıklama Üretimi:" if is_error else "✅ Açıklama Üretildi:"
    color = "red" if is_error else "green"
    payload = {
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": prefix + " "}, "annotations": {"bold": True, "color": color}},
                        {"type": "text", "text": {"content": message}},
                    ]
                },
            }
        ]
    }
    try:
        r = requests.patch(url, headers=_headers(token), json=payload, timeout=DEFAULT_TIMEOUT)
        return r.status_code == 200
    except Exception as e:
        print(f"[notion] append block exception: {e}")
        return False
