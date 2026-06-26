"""Style corpus retrieval — Voyage embed + Supabase pgvector cosine similarity."""

from __future__ import annotations

import httpx

from core.config import Config


def embed_query(cfg: Config, text: str) -> list[float]:
    r = httpx.post(
        "https://api.voyageai.com/v1/embeddings",
        headers={
            "Authorization": f"Bearer {cfg.voyage_api_key}",
            "Content-Type": "application/json",
        },
        json={"input": [text], "model": cfg.embedding_model, "input_type": "query"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]


def top_k_similar(cfg: Config, query_text: str, k: int = 5) -> list[dict]:
    """Style corpus'tan benzer scriptleri çek (cosine similarity)."""
    vector = embed_query(cfg, query_text)
    vector_literal = "[" + ",".join(str(x) for x in vector) + "]"
    # Supabase'in REST PostgREST'inde pgvector operator desteği için RPC tercih ederim
    # ama Sprint 1 için basit SQL üzerinden gidelim — execute_sql via PostgREST yok,
    # bunun yerine bir SQL RPC fonksiyonu oluşturmamız gerekir. Kısa yol:
    # PostgREST query string ile vector ordering yapılamıyor. RPC fonksiyonu yazalım.
    r = httpx.post(
        f"{cfg.supabase_url}/rest/v1/rpc/match_style_corpus",
        headers={
            "apikey": cfg.supabase_anon_key,
            "Authorization": f"Bearer {cfg.supabase_anon_key}",
            "Content-Type": "application/json",
        },
        json={"query_embedding": vector_literal, "match_count": k},
        timeout=30,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Supabase RPC HTTP {r.status_code}: {r.text[:200]}")
    return r.json()
