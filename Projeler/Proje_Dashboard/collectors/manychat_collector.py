"""ManyChat sağlık bilgisi.

ManyChat'in resmi billing endpoint'i yok; `GET /fb/page/getInfo` page
bilgisi + subscriber sayısı döndürür. `monthly_usd` bu collector'da
0 kalır (manuel tahmin override edilmez); subscriber count `note`
alanına yazılır.
"""
from __future__ import annotations

from typing import Any

import requests

from ._env import get as env_get


def collect() -> dict[str, Any]:
    key = env_get("MANYCHAT_API_TOKEN")
    if not key:
        return {"ok": False, "error": "MANYCHAT_API_TOKEN yok"}

    try:
        r = requests.get(
            "https://api.manychat.com/fb/page/getInfo",
            headers={"Authorization": f"Bearer {key}"},
            timeout=15,
        )
        if r.status_code != 200:
            return {
                "ok": False,
                "error": f"ManyChat {r.status_code}",
                "name": "ManyChat",
            }
        body = r.json() or {}
    except Exception as e:
        return {"ok": False, "error": str(e), "name": "ManyChat"}

    data = body.get("data") or {}
    page_name = data.get("name") or data.get("title") or "page"
    note = f"page: {page_name}"
    if "username" in data:
        note = f"page: {data['username']}"
    return {
        "ok": True,
        "name": "ManyChat",
        "monthly_usd": 0.0,
        "monthly_usd_known": False,
        "note": note,
        "tier": data.get("pricing_plan") or "?",
        "console_url": "https://manychat.com/account/billing",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2))
