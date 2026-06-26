"""Lokal geliştirmede master.env'i ortama yükler.

Railway'de env değişkenleri panelden gelir; orada master.env yoktur, bu yüzden
yalnızca dosya varsa ve değişken zaten set değilse doldurur (Railway env kazanır).
"""
import os
from pathlib import Path

from config import REPO_ROOT

MASTER_ENV = REPO_ROOT / "_knowledge" / "credentials" / "master.env"


def load_local_env() -> None:
    if not MASTER_ENV.exists():
        return
    for line in MASTER_ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = val.strip().strip('"').strip("'")
