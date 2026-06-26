"""Kie AI bakiye / kullanım.

Kie API'sinin tam usage endpoint'i resmi belgelenmemiş; en güvenilir veri
hesap bakiyesi (`/api/v1/chat/credit`) üzerinden gelir. Bakiye düşüşü
manuel takip ile yapılır. Bu collector mevcut bakiyeyi gösterir,
"monthly_usd" alanı bilinmez ise 0 döner.
"""
from __future__ import annotations

from typing import Any

import requests

from ._env import get as env_get


def collect() -> dict[str, Any]:
    key = env_get("KIE_API_KEY")
    if not key:
        return {"ok": False, "error": "KIE_API_KEY yok"}

    base = env_get("KIE_BASE_URL") or "https://api.kie.ai"
    try:
        r = requests.get(
            f"{base.rstrip('/')}/api/v1/chat/credit",
            headers={"Authorization": f"Bearer {key}"},
            timeout=15,
        )
        if r.status_code != 200:
            return {"ok": False, "error": f"Kie {r.status_code}", "name": "Kie AI"}
        data = r.json().get("data") or {}
        balance = data.get("balance") or data.get("credits") or 0
        return {
            "ok": True,
            "name": "Kie AI",
            "monthly_usd": 0.0,
            "monthly_usd_known": False,  # Bakiye gösterir, kullanım değil
            "note": f"bakiye: {balance}",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "name": "Kie AI"}


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2))
