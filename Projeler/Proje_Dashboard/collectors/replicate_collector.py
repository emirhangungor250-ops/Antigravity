"""Replicate canlı kullanım.

`GET https://api.replicate.com/v1/account` hesap bilgisi döner. Resmi
billing endpoint'i public değil; o yüzden `monthly_usd` boş kalırsa
manuel tahmin (subscriptions.yaml) override edilmez.
"""
from __future__ import annotations

from typing import Any

import requests

from ._env import get as env_get


def collect() -> dict[str, Any]:
    key = env_get("REPLICATE_API_TOKEN")
    if not key:
        return {"ok": False, "error": "REPLICATE_API_TOKEN yok"}

    try:
        r = requests.get(
            "https://api.replicate.com/v1/account",
            headers={"Authorization": f"Bearer {key}"},
            timeout=15,
        )
        if r.status_code != 200:
            return {
                "ok": False,
                "error": f"Replicate {r.status_code}",
                "name": "Replicate",
            }
        data = r.json() or {}
    except Exception as e:
        return {"ok": False, "error": str(e), "name": "Replicate"}

    username = data.get("username") or data.get("name") or "hesap"
    account_type = data.get("type") or "user"
    note_parts = [f"hesap: {username}", f"tip: {account_type}"]
    return {
        "ok": True,
        "name": "Replicate",
        "monthly_usd": 0.0,
        "monthly_usd_known": False,
        "note": " · ".join(note_parts),
        "tier": account_type,
        "console_url": "https://replicate.com/account/billing",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2))
