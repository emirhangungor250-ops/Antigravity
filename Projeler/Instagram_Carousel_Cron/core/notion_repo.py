"""Notion repo — Twitter DB sorguları + carousel state update.

DB schema (Twitter_Text_Paylasim/core/notion_logger.py'dan + scripts/add_notion_columns.py):
  Title, Source, Score, Status, Tweet Text, Thread, LinkedIn Text, Source URL,
  Typefully Draft URL, Typefully Draft ID, Date,
  Carousel Status, Carousel Slides, Instagram Caption,
  Carousel Generated At, Carousel Approved At
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests

from config import settings
from ops_logger import get_ops_logger

ops = get_ops_logger("IG_Carousel_Cron", "NotionRepo")

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _rich_text(prop: dict) -> str:
    return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))


def _title(prop: dict) -> str:
    return "".join(t.get("plain_text", "") for t in prop.get("title", []))


def fetch_carousel_candidates(days: int = 1, limit: int = 25) -> list[dict]:
    """Bugün/dün üretilmiş Status=Draft + Carousel Status≠Generated/Approved satırları."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    payload = {
        "filter": {
            "and": [
                {"property": "Status", "select": {"equals": "Draft"}},
                {"property": "Date", "date": {"on_or_after": cutoff}},
                {
                    "or": [
                        {"property": "Carousel Status", "select": {"is_empty": True}},
                        {"property": "Carousel Status", "select": {"equals": "Pending"}},
                        {"property": "Carousel Status", "select": {"equals": "Failed"}},
                    ]
                },
            ]
        },
        "sorts": [{"property": "Score", "direction": "descending"}],
        "page_size": limit,
    }
    try:
        r = requests.post(
            f"{API}/databases/{settings.NOTION_X_DB_ID}/query",
            headers=_headers(),
            json=payload,
            timeout=20,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
    except Exception as e:
        ops.error("Notion query exception", exception=e)
        return []

    candidates = []
    for row in results:
        props = row.get("properties", {})
        candidates.append({
            "row_id": row.get("id", ""),
            "title": _title(props.get("Title", {})),
            "source": (props.get("Source", {}).get("select") or {}).get("name") or "?",
            "score": props.get("Score", {}).get("number") or 0,
            "tweet_text": _rich_text(props.get("Tweet Text", {})),
            "thread": _rich_text(props.get("Thread", {})),
            "linkedin_text": _rich_text(props.get("LinkedIn Text", {})),
            "source_url": props.get("Source URL", {}).get("url") or "",
        })
    return candidates


def fetch_generated_for_mail(days: int = 1) -> list[dict]:
    """Mail için: Carousel Status=Generated olanlar (henüz Approved değil)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    payload = {
        "filter": {
            "and": [
                {"property": "Carousel Status", "select": {"equals": "Generated"}},
                {"property": "Carousel Generated At", "date": {"on_or_after": cutoff}},
            ]
        },
        "sorts": [{"property": "Carousel Generated At", "direction": "descending"}],
        "page_size": 50,
    }
    try:
        r = requests.post(
            f"{API}/databases/{settings.NOTION_X_DB_ID}/query",
            headers=_headers(),
            json=payload,
            timeout=20,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
    except Exception as e:
        ops.error("Notion mail query exception", exception=e)
        return []

    out = []
    for row in results:
        props = row.get("properties", {})
        slides_raw = _rich_text(props.get("Carousel Slides", {}))
        try:
            slides = json.loads(slides_raw) if slides_raw else []
        except Exception:
            slides = []
        out.append({
            "row_id": row.get("id", ""),
            "title": _title(props.get("Title", {})),
            "source": (props.get("Source", {}).get("select") or {}).get("name") or "?",
            "score": props.get("Score", {}).get("number") or 0,
            "slides": slides,
            "caption": _rich_text(props.get("Instagram Caption", {})),
        })
    return out


def update_status(row_id: str, status: str) -> None:
    """Carousel Status güncelle."""
    payload = {"properties": {"Carousel Status": {"select": {"name": status}}}}
    try:
        r = requests.patch(
            f"{API}/pages/{row_id}",
            headers=_headers(),
            json=payload,
            timeout=15,
        )
        if r.status_code not in (200, 201):
            ops.error(f"update_status fail {r.status_code}", message=r.text[:200])
    except Exception as e:
        ops.error("update_status exception", exception=e)


def save_generated_carousel(
    row_id: str,
    slides: list[dict],
    caption: str,
) -> None:
    """Slides + caption + status=Generated kaydet.

    slides: list of {"index": 1, "url": "https://...", "overlay_text": "..."}
    """
    slides_json = json.dumps(slides, ensure_ascii=False)[:1990]
    payload = {
        "properties": {
            "Carousel Status": {"select": {"name": "Generated"}},
            "Carousel Slides": {"rich_text": [{"text": {"content": slides_json}}]},
            "Instagram Caption": {"rich_text": [{"text": {"content": caption[:1990]}}]},
            "Carousel Generated At": {
                "date": {"start": datetime.now(timezone.utc).isoformat()}
            },
        }
    }
    try:
        r = requests.patch(
            f"{API}/pages/{row_id}",
            headers=_headers(),
            json=payload,
            timeout=20,
        )
        if r.status_code not in (200, 201):
            ops.error(f"save_generated fail {r.status_code}", message=r.text[:200])
            return
        ops.success("Carousel Notion'a kaydedildi", f"row={row_id[:8]} slides={len(slides)}")
    except Exception as e:
        ops.error("save_generated exception", exception=e)


def fetch_row(row_id: str) -> Optional[dict]:
    """Tek satırı oku — manuel generate için."""
    try:
        r = requests.get(f"{API}/pages/{row_id}", headers=_headers(), timeout=15)
        r.raise_for_status()
        row = r.json()
    except Exception as e:
        ops.error("fetch_row exception", exception=e)
        return None
    props = row.get("properties", {})
    return {
        "row_id": row.get("id", ""),
        "title": _title(props.get("Title", {})),
        "source": (props.get("Source", {}).get("select") or {}).get("name") or "?",
        "score": props.get("Score", {}).get("number") or 0,
        "tweet_text": _rich_text(props.get("Tweet Text", {})),
        "thread": _rich_text(props.get("Thread", {})),
        "linkedin_text": _rich_text(props.get("LinkedIn Text", {})),
        "source_url": props.get("Source URL", {}).get("url") or "",
    }
