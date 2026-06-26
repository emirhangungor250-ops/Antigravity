"""Notion script DB'sinden "hazır" durumdaki kartları + sayfa gövdesini okur.

Caption/özet alanını DEĞİL, sayfa GÖVDESİNİ okur (prompter metni gövdededir).

Şema env'den okunur — kendi Notion DB'nizdeki adlara göre .env'de ayarlayın:
  NOTION_STATUS_PROPERTY  — durum (status/select) property adı (varsayılan "Status")
  NOTION_STATUS_READY     — "çekime hazır" değeri (varsayılan "Çekime Hazır")
"""
from __future__ import annotations

import os

from notion_client import Client

STATUS_PROPERTY = os.getenv("NOTION_STATUS_PROPERTY", "Status")
STATUS_READY = os.getenv("NOTION_STATUS_READY", "Çekime Hazır")


def notion_client() -> Client:
    token = os.environ.get("NOTION_REELS_TOKEN") or os.environ.get("PROMPTER_NOTION_TOKEN")
    if not token:
        raise RuntimeError("Notion token yok (NOTION_REELS_TOKEN / PROMPTER_NOTION_TOKEN).")
    return Client(auth=token)


def fetch_ready_cards(notion: Client, db_id: str) -> list[dict]:
    """Status = hazır değeri olan kartları döndürür: [{'id', 'name'}]."""
    cards: list[dict] = []
    cursor = None
    while True:
        resp = notion.databases.query(
            database_id=db_id,
            filter={"property": STATUS_PROPERTY, "select": {"equals": STATUS_READY}},
            start_cursor=cursor,
            page_size=100,
        )
        for pg in resp["results"]:
            cards.append({"id": pg["id"], "name": _title(pg)})
        if not resp.get("has_more"):
            break
        cursor = resp["next_cursor"]
    return cards


def _title(page: dict) -> str:
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in prop["title"]).strip()
    return ""


def fetch_body_text(notion: Client, page_id: str) -> str:
    """Sayfa gövdesini düz metne çevirir (block -> satır). AI temizleyici işler."""
    lines: list[str] = []
    cursor = None
    while True:
        resp = notion.blocks.children.list(block_id=page_id, start_cursor=cursor, page_size=100)
        for block in resp["results"]:
            lines.append(_block_text(block))
        if not resp.get("has_more"):
            break
        cursor = resp["next_cursor"]
    return "\n".join(lines)


def _rt(rich: list) -> str:
    return "".join(t.get("plain_text", "") for t in rich)


def _block_text(block: dict) -> str:
    btype = block.get("type", "")
    data = block.get(btype, {})
    if btype == "divider":
        return "----"
    if btype == "child_page":
        return ""  # alt-sayfa — script gövdesi değil
    if "rich_text" in data:
        return _rt(data["rich_text"])
    return ""
