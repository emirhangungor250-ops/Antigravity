"""Anthropic bu ayki kullanım.

Anthropic'in usage endpoint'i şu an public tam dökülmemiş — admin
key (sk-ant-admin-...) gerektirir. Yoksa 'veri yok' döner.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from ._env import get as env_get


def collect() -> dict[str, Any]:
    key = env_get("ANTHROPIC_ADMIN_API_KEY") or env_get("ANTHROPIC_API_KEY")
    if not key:
        return {"ok": False, "error": "ANTHROPIC_API_KEY yok"}

    if not key.startswith("sk-ant-admin"):
        return {
            "ok": False,
            "error": "Anthropic usage API admin-key ister (sk-ant-admin-...)",
            "name": "Anthropic",
        }

    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    try:
        r = requests.get(
            "https://api.anthropic.com/v1/organizations/usage_report/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
            params={
                "starting_at": start.isoformat().replace("+00:00", "Z"),
                "limit": 30,
            },
            timeout=20,
        )
        if r.status_code != 200:
            return {
                "ok": False,
                "error": f"Anthropic API {r.status_code}",
                "name": "Anthropic",
            }
        data = r.json().get("data") or []
        total = 0.0
        for bucket in data:
            for item in bucket.get("results") or []:
                cost = item.get("cost_usd") or item.get("amount", {}).get("value")
                if cost:
                    total += float(cost)
        return {
            "ok": True,
            "name": "Anthropic API",
            "monthly_usd": round(total, 2),
            "monthly_usd_known": True,
            "source": "live",
            "tier": "PAYG",
            "note": f"bu ayki gerçek kullanım ${round(total,2)}",
            "console_url": "https://console.anthropic.com/settings/usage",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "name": "Anthropic"}


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2))
