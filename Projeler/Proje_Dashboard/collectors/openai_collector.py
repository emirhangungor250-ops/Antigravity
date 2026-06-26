"""OpenAI bu ayki harcamasını çeker.

OpenAI'ın `/v1/organization/costs` endpoint'i admin key ister.
Yoksa `/v1/dashboard/billing/usage` endpoint'i (legacy) denenir.
Hiçbiri çalışmazsa graceful 'veri yok' döner.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from ._env import get as env_get


def _start_of_month() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _try_admin_costs(key: str) -> float | None:
    """Admin API kullanırsa daha doğru sonuç verir."""
    start_ts = int(_start_of_month().timestamp())
    try:
        r = requests.get(
            "https://api.openai.com/v1/organization/costs",
            headers={"Authorization": f"Bearer {key}"},
            params={"start_time": start_ts, "limit": 30},
            timeout=20,
        )
        if r.status_code != 200:
            return None
        data = r.json().get("data") or []
        total = 0.0
        for bucket in data:
            for item in bucket.get("results") or []:
                amt = (item.get("amount") or {}).get("value")
                if amt:
                    total += float(amt)
        return round(total, 2)
    except Exception:
        return None


def collect() -> dict[str, Any]:
    # Önce admin key, yoksa normal key dene
    key = env_get("OPENAI_ADMIN_API_KEY") or env_get("OPENAI_API_KEY")
    if not key:
        return {"ok": False, "error": "OPENAI_API_KEY yok", "name": "OpenAI"}

    total = _try_admin_costs(key)
    if total is None:
        return {
            "ok": False,
            "error": "Admin key gerek (api.usage.read scope)",
            "name": "OpenAI",
        }
    return {
        "ok": True,
        "name": "OpenAI",
        "monthly_usd": total,
        "monthly_usd_known": True,
        "source": "live",
        "tier": "PAYG",
        "note": f"bu ayki gerçek kullanım ${total}",
        "console_url": "https://platform.openai.com/usage",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2))
