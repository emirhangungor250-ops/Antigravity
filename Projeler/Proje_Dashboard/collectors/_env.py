"""master.env'den ortak okuma yardımcısı."""
from __future__ import annotations

import os
from pathlib import Path

MASTER_ENV = Path(__file__).resolve().parents[3] / "_knowledge" / "credentials" / "master.env"

_cache: dict[str, str] | None = None


def _load() -> dict[str, str]:
    global _cache
    if _cache is not None:
        return _cache
    out: dict[str, str] = {}
    if MASTER_ENV.exists():
        for line in MASTER_ENV.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    _cache = out
    return out


def get(name: str) -> str | None:
    val = os.getenv(name)
    if val:
        return val.strip()
    return _load().get(name)
