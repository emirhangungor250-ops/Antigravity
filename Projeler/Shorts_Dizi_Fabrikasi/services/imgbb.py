"""ImgBB upload: referans goruntulerini public URL'e cevirir."""
import base64
import logging
import os
from typing import Optional

import requests

from core.config import settings

logger = logging.getLogger("ImgBB")

API_URL = "https://api.imgbb.com/1/upload"


def upload_image(path: str, name: Optional[str] = None) -> str:
    """Gorseli ImgBB'ye yukle → public URL. Hata durumunda RuntimeError."""
    if settings.IS_DRY_RUN:
        logger.info(f"[DRY-RUN] ImgBB upload atlandi: {path}")
        return "file://" + os.path.abspath(path)

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    payload = {"key": settings.IMGBB_API_KEY, "image": encoded}
    if name:
        payload["name"] = name

    r = requests.post(API_URL, data=payload, timeout=45)
    if r.status_code != 200:
        raise RuntimeError(f"ImgBB upload fail {r.status_code}: {r.text[:300]}")
    url = r.json().get("data", {}).get("url", "")
    if not url:
        raise RuntimeError(f"ImgBB yaniti URL icermiyor: {r.text[:300]}")
    logger.info(f"ImgBB upload OK: {url[:80]}")
    return url
