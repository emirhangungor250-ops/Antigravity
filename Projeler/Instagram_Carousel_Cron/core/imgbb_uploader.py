"""ImgBB uploader — final slide PNG'lerini kalıcı CDN URL'lerine çevirir.

Reels-Kapak/agents/reels_agent.py:upload_to_imgbb pattern'ından adapt.
"""

import base64

import requests

from config import settings
from ops_logger import get_ops_logger

ops = get_ops_logger("IG_Carousel_Cron", "ImgBB")

API_URL = "https://api.imgbb.com/1/upload"


def upload(image_path: str, name: str = "") -> str:
    """Slide PNG → ImgBB → URL. Boş string döner fail durumunda."""
    if settings.IS_DRY_RUN:
        ops.info("[DRY-RUN] ImgBB upload atlandı")
        return f"file://{image_path}"

    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        ops.error("ImgBB read exception", exception=e)
        return ""

    payload = {"key": settings.IMGBB_API_KEY, "image": encoded}
    if name:
        payload["name"] = name

    try:
        r = requests.post(API_URL, data=payload, timeout=45)
        if r.status_code != 200:
            ops.error(f"ImgBB upload fail {r.status_code}", message=r.text[:300])
            return ""
        url = r.json().get("data", {}).get("url", "")
        if url:
            ops.info(f"ImgBB upload OK: {url[:80]}…")
        return url
    except Exception as e:
        ops.error("ImgBB upload exception", exception=e)
        return ""
