"""ElevenLabs canlı abonelik + kullanım.

`/v1/user` endpoint'i tier + bu dönem kullanılan karakter sayısını verir.
Tier'a göre tahmini USD üretilir (free $0, starter $5, creator $22, ...).
"""
from __future__ import annotations

from typing import Any

import requests

from ._env import get as env_get

TIER_PRICING = {
    "free": 0.0,
    "starter": 5.0,
    "creator": 22.0,
    "pro": 99.0,
    "scale": 330.0,
    "business": 1320.0,
}


def collect() -> dict[str, Any]:
    key = env_get("ELEVENLABS_API_KEY")
    if not key:
        return {"ok": False, "error": "ELEVENLABS_API_KEY yok"}
    try:
        r = requests.get(
            "https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": key},
            timeout=15,
        )
        if r.status_code != 200:
            return {"ok": False, "error": f"ElevenLabs {r.status_code}"}
        data = r.json()
        sub = data.get("subscription") or {}
        tier = (sub.get("tier") or "free").lower()
        used = sub.get("character_count", 0)
        limit = sub.get("character_limit", 0)
        overage = float((sub.get("current_overage") or {}).get("amount") or 0)
        monthly = TIER_PRICING.get(tier, 0.0) + overage
        usage_pct = round((used / limit * 100), 1) if limit else 0
        return {
            "ok": True,
            "name": "ElevenLabs",
            "monthly_usd": round(monthly, 2),
            "monthly_usd_known": True,
            "tier": tier,
            "used": used,
            "limit": limit,
            "usage_pct": usage_pct,
            "source": "live",
            "note": f"{tier.title()} plan · {used:,}/{limit:,} karakter ({usage_pct}%)",
            "console_url": "https://elevenlabs.io/app/subscription",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2, ensure_ascii=False))
