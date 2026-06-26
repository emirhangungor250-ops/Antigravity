"""Sabit aylık abonelikleri YAML'dan oku."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CONFIG = Path(__file__).resolve().parents[1] / "config" / "subscriptions.yaml"


def collect() -> dict[str, Any]:
    if not CONFIG.exists():
        return {"ok": False, "error": "subscriptions.yaml yok"}
    data = yaml.safe_load(CONFIG.read_text()) or {}
    fixed = data.get("fixed") or []
    ai = data.get("ai_usage_estimates") or []
    fixed_total = round(sum(float(x.get("monthly_usd") or 0) for x in fixed), 2)
    ai_total = round(sum(float(x.get("monthly_usd") or 0) for x in ai), 2)
    return {
        "ok": True,
        "fixed": fixed,
        "ai_usage": ai,
        "fixed_total_usd": fixed_total,
        "ai_total_usd": ai_total,
        "grand_total_usd": round(fixed_total + ai_total, 2),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2, default=str))
