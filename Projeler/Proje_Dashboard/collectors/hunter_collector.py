"""Hunter.io canlı plan + kredi durumu."""
from __future__ import annotations

from typing import Any

import requests

from ._env import get as env_get

PLAN_PRICING = {
    "Free": 0.0,
    "Starter": 49.0,
    "Growth": 149.0,
    "Pro": 299.0,
    "Business": 499.0,
}


def collect() -> dict[str, Any]:
    key = env_get("HUNTER_API_KEY")
    if not key:
        return {"ok": False, "error": "HUNTER_API_KEY yok"}
    try:
        r = requests.get(f"https://api.hunter.io/v2/account?api_key={key}", timeout=15)
        if r.status_code != 200:
            return {"ok": False, "error": f"Hunter {r.status_code}"}
        data = (r.json() or {}).get("data") or {}
        plan = data.get("plan_name", "Free")
        reqs = data.get("requests", {})
        credits = reqs.get("credits", {})
        used = credits.get("used", 0)
        avail = credits.get("available", 0)
        searches = reqs.get("searches", {})
        pct = round((used / avail * 100), 1) if avail else 0
        monthly = PLAN_PRICING.get(plan, 0.0)
        return {
            "ok": True,
            "name": "Hunter.io",
            "monthly_usd": monthly,
            "monthly_usd_known": True,
            "tier": plan,
            "used": used,
            "limit": avail,
            "usage_pct": pct,
            "source": "live",
            "note": f"{plan} plan · {searches.get('used', 0)}/{searches.get('available', 0)} arama · {pct}% kredi",
            "console_url": "https://hunter.io/dashboard",
            "reset_date": data.get("reset_date"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2, ensure_ascii=False))
