"""Firecrawl canlı kredi durumu."""
from __future__ import annotations

from typing import Any

import requests

from ._env import get as env_get


def collect() -> dict[str, Any]:
    key = env_get("FIRECRAWL_API_KEY")
    if not key:
        return {"ok": False, "error": "FIRECRAWL_API_KEY yok"}
    try:
        r = requests.get(
            "https://api.firecrawl.dev/v1/team/credit-usage",
            headers={"Authorization": f"Bearer {key}"},
            timeout=15,
        )
        if r.status_code != 200:
            return {"ok": False, "error": f"Firecrawl {r.status_code}"}
        data = (r.json() or {}).get("data") or {}
        plan_credits = data.get("plan_credits", 0)
        remaining = data.get("remaining_credits", 0)
        used = max(plan_credits - remaining, 0)
        pct = round((used / plan_credits * 100), 1) if plan_credits else 0
        # Plan tahmini: 500 = free, 5000 = hobby ($9), 50000 = standard ($83), 500000 = growth ($333)
        if plan_credits <= 500:
            tier, monthly = "Free", 0.0
        elif plan_credits <= 5000:
            tier, monthly = "Hobby", 16.0
        elif plan_credits <= 50000:
            tier, monthly = "Standard", 83.0
        else:
            tier, monthly = "Growth", 333.0
        return {
            "ok": True,
            "name": "Firecrawl",
            "monthly_usd": monthly,
            "monthly_usd_known": True,
            "tier": tier,
            "used": used,
            "limit": plan_credits,
            "remaining": remaining,
            "usage_pct": pct,
            "source": "live",
            "note": f"{tier} plan · {remaining:,}/{plan_credits:,} kredi kaldı ({pct}% kullanıldı)",
            "console_url": "https://www.firecrawl.dev/app/billing",
            "billing_period_end": data.get("billing_period_end"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2, ensure_ascii=False))
