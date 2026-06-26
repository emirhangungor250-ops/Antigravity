# -*- coding: utf-8 -*-
"""Öğrenme corpus'u — kanal sahibinin gerçek (yorum -> cevap) çiftleri.

Faz 1: kanalda zaten cevaplanmış thread'lerden çift toplar, yorum metnini Voyage ile
  embed'leyip yt_reply_corpus'a yazar (pasif birikim).
Faz 2: yeni yoruma en benzer geçmiş çiftleri çeker (match_reply_corpus RPC) -> few-shot.

Benzerlik YORUM metni üzerinden: benzer yoruma kanal sahibi nasıl cevap verdiyse onu örnek al.
"""
from __future__ import annotations

import time

import requests

import config

REST = f"{config.SUPABASE_URL}/rest/v1"
VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_BATCH = 8


def _sb_headers(extra: dict | None = None) -> dict:
    h = {
        "apikey": config.SUPABASE_KEY,
        "Authorization": f"Bearer {config.SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def _voyage_embed(texts: list[str], input_type: str) -> list[list[float]]:
    r = requests.post(
        VOYAGE_URL,
        headers={"Authorization": f"Bearer {config.VOYAGE_API_KEY}", "Content-Type": "application/json"},
        json={"input": texts, "model": config.EMBEDDING_MODEL, "input_type": input_type},
        timeout=60,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Voyage HTTP {r.status_code}: {r.text[:200]}")
    return [d["embedding"] for d in r.json()["data"]]


def existing_corpus_ids(comment_ids: list[str]) -> set[str]:
    """Corpus'ta zaten olan comment_id'ler (tekrar embed'lemeyi önle)."""
    out: set[str] = set()
    ids = [c for c in comment_ids if c]
    for i in range(0, len(ids), 200):
        batch = ids[i:i + 200]
        in_list = ",".join(f'"{c}"' for c in batch)
        r = requests.get(
            f"{REST}/yt_reply_corpus",
            headers=_sb_headers(),
            params={"select": "comment_id", "comment_id": f"in.({in_list})"},
            timeout=30,
        )
        if r.status_code >= 300:
            raise RuntimeError(f"Supabase corpus select HTTP {r.status_code}: {r.text[:200]}")
        out.update(row["comment_id"] for row in r.json() if row.get("comment_id"))
    return out


def _upsert(rows: list[dict]) -> int:
    if not rows:
        return 0
    r = requests.post(
        f"{REST}/yt_reply_corpus?on_conflict=comment_id",
        headers=_sb_headers({"Prefer": "resolution=merge-duplicates,return=representation"}),
        json=rows,
        timeout=60,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Supabase corpus upsert HTTP {r.status_code}: {r.text[:200]}")
    return len(r.json())


def seed_pairs(pairs: list[dict]) -> int:
    """pairs: [{comment_id, comment_text, reply_text, video_id, video_title, lang, source}].
    Yorum metnini embed'leyip corpus'a yazar. Zaten var olanlar çağrı öncesi elenmeli."""
    written = 0
    for start in range(0, len(pairs), VOYAGE_BATCH):
        batch = pairs[start:start + VOYAGE_BATCH]
        vectors = _voyage_embed([p["comment_text"][:4000] for p in batch], "document")
        rows = []
        for p, v in zip(batch, vectors):
            rows.append({
                "comment_id": p.get("comment_id"),
                "comment_text": p["comment_text"],
                "reply_text": p["reply_text"],
                "video_id": p.get("video_id"),
                "video_title": p.get("video_title"),
                "lang": p.get("lang"),
                "source": p.get("source", "native"),
                "ai_draft": p.get("ai_draft"),
                "embedding": v,
            })
        written += _upsert(rows)
        time.sleep(0.3)
    return written


def retrieve_similar(comment_text: str, k: int = 5, lang: str | None = None) -> list[dict]:
    """Faz 2: yeni yoruma en benzer geçmiş (yorum->cevap) çiftleri (cosine)."""
    vec = _voyage_embed([comment_text[:4000]], "query")[0]
    body = {"query_embedding": vec, "match_count": k}
    if lang:
        body["filter_lang"] = lang
    r = requests.post(
        f"{REST}/rpc/match_reply_corpus",
        headers=_sb_headers(),
        json=body,
        timeout=30,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Supabase RPC HTTP {r.status_code}: {r.text[:200]}")
    return r.json()
