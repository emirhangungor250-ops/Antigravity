"""Konuşma hafızası — Supabase (PostgREST) üzerinden.

Son N mesajı (varsayılan 15) user_id ile bir Supabase tablosunda tutar. Service role
anahtarı RLS'i bypass eder. Tablo adı env'den ayarlanabilir (CHAT_MEMORY_TABLE).

Hafıza bir İYİLEŞTİRMEdir: Supabase erişilemezse bot yine cevap verir (boş geçmişle).
"""

from __future__ import annotations

import logging
import os

import requests

from config import CONFIG

log = logging.getLogger("hotel-chat.memory")
_VERIFY_SSL = os.getenv("HOTELRUNNER_VERIFY_SSL", "1") != "0"
_TIMEOUT = 10
_TABLE = os.getenv("CHAT_MEMORY_TABLE", "chat_memory")


def _ready() -> bool:
    return bool(CONFIG.supabase_url and CONFIG.supabase_service_key)


def _headers() -> dict:
    k = CONFIG.supabase_service_key
    return {"apikey": k, "Authorization": f"Bearer {k}", "Content-Type": "application/json"}


def load(user_id: str, limit: int | None = None) -> list[dict]:
    """Son N mesajı kronolojik (eski→yeni) sırada döndürür: [{role, content}, ...]."""
    if not _ready():
        return []
    n = limit or CONFIG.history_window
    url = f"{CONFIG.supabase_url}/rest/v1/{_TABLE}"
    params = {
        "user_id": f"eq.{user_id}",
        "select": "role,content",
        "order": "created_at.desc",
        "limit": str(n),
    }
    try:
        r = requests.get(url, headers=_headers(), params=params, timeout=_TIMEOUT, verify=_VERIFY_SSL)
        r.raise_for_status()
        rows = r.json()
        return [{"role": x["role"], "content": x["content"]} for x in reversed(rows)]
    except Exception as e:
        log.warning("memory load failed (%s): %s", user_id, e)
        return []


def save(user_id: str, platform: str, role: str, content: str) -> None:
    """Tek mesaj ekler. Sessizce başarısız olabilir (hafıza kritik değil)."""
    if not _ready() or not content:
        return
    url = f"{CONFIG.supabase_url}/rest/v1/{_TABLE}"
    body = {"user_id": user_id, "platform": platform, "role": role, "content": content}
    try:
        h = {**_headers(), "Prefer": "return=minimal"}
        requests.post(url, headers=h, json=body, timeout=_TIMEOUT, verify=_VERIFY_SSL)
    except Exception as e:
        log.warning("memory save failed (%s): %s", user_id, e)
