# -*- coding: utf-8 -*-
"""Supabase PostgREST katmanı — yt_comments (durum + idempotency).

repo standardı: ekstra istemci yok, requests + service_role key.
Corpus işlemleri corpus.py'de (embedding gerektirdiği için ayrı).
"""
from __future__ import annotations

from datetime import datetime, timezone

import requests

import config

REST = f"{config.SUPABASE_URL}/rest/v1"


def _headers(extra: dict | None = None) -> dict:
    h = {
        "apikey": config.SUPABASE_KEY,
        "Authorization": f"Bearer {config.SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def known_comment_ids(ids: list[str]) -> set[str]:
    """Verilen id'lerden yt_comments'te ZATEN olanları döndür (tekrar raporlamayı önler)."""
    out: set[str] = set()
    for i in range(0, len(ids), 200):
        batch = ids[i:i + 200]
        in_list = ",".join(f'"{c}"' for c in batch)
        r = requests.get(
            f"{REST}/yt_comments",
            headers=_headers(),
            params={"select": "comment_id", "comment_id": f"in.({in_list})"},
            timeout=30,
        )
        if r.status_code >= 300:
            raise RuntimeError(f"Supabase select HTTP {r.status_code}: {r.text[:200]}")
        out.update(row["comment_id"] for row in r.json())
    return out


def upsert_comments(rows: list[dict]) -> int:
    """yt_comments'e yaz (comment_id çakışırsa güncelle)."""
    if not rows:
        return 0
    r = requests.post(
        f"{REST}/yt_comments?on_conflict=comment_id",
        headers=_headers({"Prefer": "resolution=merge-duplicates,return=representation"}),
        json=rows,
        timeout=60,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Supabase upsert HTTP {r.status_code}: {r.text[:200]}")
    return len(r.json())


def update_comment(comment_id: str, fields: dict) -> None:
    """Tek yorumun durumunu güncelle (Faz 2: auto_replied/drafted/approved/skipped)."""
    # PostgREST'e SQL fonksiyonu değil ISO timestamp gönder (string "now()" timestamptz'e yazılmaz).
    fields = {**fields, "updated_at": datetime.now(timezone.utc).isoformat()}
    r = requests.patch(
        f"{REST}/yt_comments",
        headers=_headers({"Prefer": "return=minimal"}),
        params={"comment_id": f"eq.{comment_id}"},
        json=fields,
        timeout=30,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Supabase update HTTP {r.status_code}: {r.text[:200]}")


def corpus_count() -> int:
    """Corpus'taki gerçek cevap sayısı (Faz 2 hazırlık sinyali için)."""
    r = requests.get(
        f"{REST}/yt_reply_corpus",
        headers=_headers({"Prefer": "count=exact"}),
        params={"select": "id", "limit": "1"},
        timeout=30,
    )
    if r.status_code >= 300:
        return 0
    # Content-Range: 0-0/123  -> toplam 123
    cr = r.headers.get("content-range", "")
    if "/" in cr:
        try:
            return int(cr.split("/")[-1])
        except ValueError:
            return 0
    return 0


def get_comment(comment_id: str) -> dict | None:
    """Tek yorumu getir (Faz 2 onay sayfası: taslak + metin + video). Yoksa None."""
    r = requests.get(
        f"{REST}/yt_comments",
        headers=_headers(),
        params={"comment_id": f"eq.{comment_id}", "limit": "1"},
        timeout=30,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Supabase get_comment HTTP {r.status_code}: {r.text[:200]}")
    rows = r.json()
    return rows[0] if rows else None
