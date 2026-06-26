"""Apify canlı bu ay USD kullanımı.

`/v2/users/me/usage/monthly` her usage tipinin gerçek $ değerini verir.
Toplam = tüm tiplerin amountAfterVolumeDiscountUsd toplamı.
"""
from __future__ import annotations

from typing import Any

import requests

from ._env import get as env_get


def _user_monthly(key: str) -> dict[str, Any]:
    r = requests.get(
        "https://api.apify.com/v2/users/me/usage/monthly",
        headers={"Authorization": f"Bearer {key}"},
        timeout=20,
    )
    if r.status_code != 200:
        return {"ok": False, "error": f"{r.status_code}"}
    data = (r.json() or {}).get("data") or {}
    cycle = data.get("usageCycle") or {}
    service_usage = data.get("monthlyServiceUsage") or {}
    total_usd = 0.0
    for tip, val in service_usage.items():
        total_usd += float(val.get("amountAfterVolumeDiscountUsd") or 0)
    return {
        "ok": True,
        "monthly_usd": round(total_usd, 4),
        "cycle_start": cycle.get("startAt"),
        "cycle_end": cycle.get("endAt"),
    }


def _user_plan(key: str) -> str:
    try:
        r = requests.get(
            "https://api.apify.com/v2/users/me",
            headers={"Authorization": f"Bearer {key}"},
            timeout=15,
        )
        if r.status_code != 200:
            return "?"
        return (((r.json() or {}).get("data") or {}).get("plan") or {}).get("id") or "?"
    except Exception:
        return "?"


def collect() -> dict[str, Any]:
    keys = [env_get("APIFY_API_KEY_1"), env_get("APIFY_API_KEY_2")]
    keys = [k for k in keys if k]
    if not keys:
        return {"ok": False, "error": "APIFY_API_KEY yok"}

    total = 0.0
    accounts = []
    for k in keys:
        plan = _user_plan(k)
        usage = _user_monthly(k)
        if usage.get("ok"):
            total += usage["monthly_usd"]
            accounts.append({"plan": plan, "monthly_usd": usage["monthly_usd"]})

    if not accounts:
        return {"ok": False, "error": "Apify usage çekilemedi"}

    note = ", ".join(f"{a['plan']} ${a['monthly_usd']:.3f}" for a in accounts)
    return {
        "ok": True,
        "name": "Apify",
        "monthly_usd": round(total, 2),
        "monthly_usd_known": True,
        "tier": "+".join(a["plan"] for a in accounts),
        "source": "live",
        "note": f"{len(accounts)} hesap toplamı · {note}",
        "console_url": "https://console.apify.com/billing",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2, ensure_ascii=False))
