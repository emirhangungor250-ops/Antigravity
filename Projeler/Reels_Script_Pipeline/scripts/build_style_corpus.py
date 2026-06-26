"""Style corpus indeksleme.

"İçerik DB" Notion DB'sinden "Yayınlandı" status'undaki kartları çek,
sayfa body'lerini düz metne çevir, Voyage voyage-3 ile embed et, Supabase
style_corpus_embeddings tablosuna upsert.

Kullanım:
    python -m scripts.build_style_corpus           # tüm Yayınlandı kartları
    python -m scripts.build_style_corpus --limit 5 # ilk 5 kart (test)
    python -m scripts.build_style_corpus --dry-run # embed/upsert yapma, sadece say
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass

import httpx

from core.config import Config

NOTION_VERSION = "2022-06-28"
VOYAGE_BATCH_SIZE = 8
MAX_BODY_CHARS = 12000


@dataclass
class CorpusEntry:
    notion_page_id: str
    title: str
    script_text: str
    drive_url: str | None
    caption: str | None


def fetch_published_pages(cfg: Config, limit: int | None) -> list[dict]:
    pages: list[dict] = []
    cursor: str | None = None
    while True:
        body: dict = {
            "filter": {"property": "Status", "select": {"equals": "Yayınlandı"}},
            "page_size": 100,
        }
        if cursor:
            body["start_cursor"] = cursor
        r = httpx.post(
            f"https://api.notion.com/v1/databases/{cfg.notion_style_corpus_db_id}/query",
            headers={
                "Authorization": f"Bearer {cfg.notion_token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            json=body,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        pages.extend(data.get("results", []))
        if limit and len(pages) >= limit:
            return pages[:limit]
        if not data.get("has_more"):
            return pages
        cursor = data.get("next_cursor")


def extract_property_text(prop: dict | None) -> str:
    if not prop:
        return ""
    t = prop.get("type")
    if t == "title":
        return "".join(x.get("plain_text", "") for x in prop.get("title", []))
    if t == "rich_text":
        return "".join(x.get("plain_text", "") for x in prop.get("rich_text", []))
    if t == "url":
        return prop.get("url") or ""
    return ""


def fetch_page_body(cfg: Config, page_id: str) -> str:
    parts: list[str] = []
    cursor: str | None = None
    while True:
        url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"
        r = httpx.get(
            url,
            headers={
                "Authorization": f"Bearer {cfg.notion_token}",
                "Notion-Version": NOTION_VERSION,
            },
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        for block in data.get("results", []):
            parts.append(block_to_text(block))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return "\n".join(p for p in parts if p).strip()


def block_to_text(block: dict) -> str:
    t = block.get("type")
    if not t:
        return ""
    inner = block.get(t, {})
    rich = inner.get("rich_text", [])
    text = "".join(x.get("plain_text", "") for x in rich)
    if t == "heading_1":
        return f"\n# {text}" if text else ""
    if t == "heading_2":
        return f"\n## {text}" if text else ""
    if t == "heading_3":
        return f"\n### {text}" if text else ""
    if t == "bulleted_list_item":
        return f"- {text}" if text else ""
    if t == "numbered_list_item":
        return f"1. {text}" if text else ""
    if t == "to_do":
        mark = "[x]" if inner.get("checked") else "[ ]"
        return f"{mark} {text}" if text else ""
    if t == "quote":
        return f"> {text}" if text else ""
    if t == "code":
        return f"```\n{text}\n```" if text else ""
    if t == "callout":
        return text
    return text


def page_to_entry(cfg: Config, page: dict) -> CorpusEntry | None:
    props = page.get("properties", {})
    title = extract_property_text(props.get("Name")).strip()
    drive = extract_property_text(props.get("Drive")).strip() or None
    caption = extract_property_text(props.get("Caption")).strip() or None
    body = fetch_page_body(cfg, page["id"])
    composite_parts: list[str] = []
    if title:
        composite_parts.append(f"BAŞLIK: {title}")
    if caption:
        composite_parts.append(f"CAPTION: {caption}")
    if body:
        composite_parts.append(f"SCRIPT:\n{body}")
    script_text = "\n\n".join(composite_parts).strip()
    if len(script_text) < 40:
        return None
    if len(script_text) > MAX_BODY_CHARS:
        script_text = script_text[:MAX_BODY_CHARS]
    return CorpusEntry(
        notion_page_id=page["id"],
        title=title or "(başlıksız)",
        script_text=script_text,
        drive_url=drive,
        caption=caption,
    )


def embed_batch(cfg: Config, texts: list[str]) -> list[list[float]]:
    r = httpx.post(
        "https://api.voyageai.com/v1/embeddings",
        headers={
            "Authorization": f"Bearer {cfg.voyage_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "input": texts,
            "model": cfg.embedding_model,
            "input_type": "document",
        },
        timeout=60,
    )
    r.raise_for_status()
    return [d["embedding"] for d in r.json()["data"]]


def upsert_entries(cfg: Config, rows: list[dict]) -> int:
    if not rows:
        return 0
    r = httpx.post(
        f"{cfg.supabase_url}/rest/v1/style_corpus_embeddings?on_conflict=notion_page_id",
        headers={
            "apikey": cfg.supabase_anon_key,
            "Authorization": f"Bearer {cfg.supabase_anon_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation",
        },
        json=rows,
        timeout=60,
    )
    if r.status_code >= 300:
        print(f"  ❌ Supabase upsert HTTP {r.status_code}: {r.text[:200]}")
        r.raise_for_status()
    return len(r.json())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cfg = Config.from_env()
    print(f"📚 Style corpus indeksleme — limit={args.limit or 'all'} dry={args.dry_run}")
    print(f"   Notion DB: {cfg.notion_style_corpus_db_id}")
    print(f"   Embedding: {cfg.embedding_model} (1024d)")
    print()

    pages = fetch_published_pages(cfg, args.limit)
    print(f"📥 Yayınlandı status'unda {len(pages)} kart bulundu")
    if not pages:
        return 0

    entries: list[CorpusEntry] = []
    for i, page in enumerate(pages, 1):
        title = extract_property_text(page.get("properties", {}).get("Name"))[:60]
        try:
            entry = page_to_entry(cfg, page)
        except httpx.HTTPError as e:
            print(f"  [{i:>3}/{len(pages)}] ⚠️  body fetch error: {title} — {e}")
            continue
        if entry is None:
            print(f"  [{i:>3}/{len(pages)}] ⏭️  içerik çok kısa, atlandı: {title}")
            continue
        entries.append(entry)
        print(f"  [{i:>3}/{len(pages)}] ✅ {title} ({len(entry.script_text)} char)")

    print(f"\n🧮 {len(entries)} kart embed'lenecek")
    if args.dry_run:
        return 0

    indexed = 0
    for start in range(0, len(entries), VOYAGE_BATCH_SIZE):
        batch = entries[start : start + VOYAGE_BATCH_SIZE]
        vectors = embed_batch(cfg, [e.script_text for e in batch])
        rows = [
            {
                "notion_page_id": e.notion_page_id,
                "title": e.title,
                "script_text": e.script_text,
                "topic_tags": [],
                "drive_url": e.drive_url,
                "embedding": v,
            }
            for e, v in zip(batch, vectors)
        ]
        n = upsert_entries(cfg, rows)
        indexed += n
        print(f"  📦 batch {start//VOYAGE_BATCH_SIZE + 1}: {n} kart yazıldı")
        time.sleep(0.3)

    print(f"\n✅ Style corpus güncellendi: {indexed} satır")
    return 0


if __name__ == "__main__":
    sys.exit(main())
