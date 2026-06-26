"""Supabase pipeline_runs state CRUD."""

from __future__ import annotations

import httpx

from core.config import Config


def _hdr(cfg: Config) -> dict:
    return {
        "apikey": cfg.supabase_anon_key,
        "Authorization": f"Bearer {cfg.supabase_anon_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def create_run(cfg: Config, *, reels_url: str, source: str = "manuel",
               source_channel: str | None = None) -> dict:
    r = httpx.post(
        f"{cfg.supabase_url}/rest/v1/pipeline_runs",
        headers=_hdr(cfg),
        json={"reels_url": reels_url, "source": source, "source_channel": source_channel,
              "stage": "created"},
        timeout=15,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"create_run HTTP {r.status_code}: {r.text[:200]}")
    return r.json()[0]


def update_run(cfg: Config, run_id: str, **fields) -> None:
    if not fields:
        return
    fields["updated_at"] = "now()"
    r = httpx.patch(
        f"{cfg.supabase_url}/rest/v1/pipeline_runs?id=eq.{run_id}",
        headers=_hdr(cfg),
        json=fields,
        timeout=15,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"update_run HTTP {r.status_code}: {r.text[:200]}")
