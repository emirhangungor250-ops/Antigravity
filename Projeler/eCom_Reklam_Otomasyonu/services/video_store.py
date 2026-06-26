"""
Video Store — Kalıcı Video Hosting
====================================
Replicate output URL'leri ~1 saatte expire eder. Notion log'larındaki
video linkleri kullanıcının onlarca dakika/saat sonra ziyaretinde 404
olur. Bu modül video'yu Catbox.moe'ya re-host eder; kalıcı URL döner.

Catbox: ücretsiz, API key yok, dosya 200MB limit, kalıcı (manuel silinmediği
sürece). 10-30s reklam videoları tipik 5-20MB.

Fail-graceful: Catbox erişilemezse orijinal Replicate URL geri döner; akış
durdurulmaz.
"""

from __future__ import annotations

import re

import requests

from logger import get_logger

log = get_logger("video_store")

CATBOX_API = "https://catbox.moe/user/api.php"
REQUEST_TIMEOUT = 120  # büyük video upload için

# WHY: Eski "catbox.moe" substring kontrolü Catbox API'nin abuse mesajı
# ("We reject catbox.moe uploads…") ya da hata cümlesi gibi gövdelerde
# de geçer; sonuçta Notion'a kırık URL yazılıyordu. Sadece gerçek
# files.catbox.moe veya catbox.moe path'iyle başlayan kısa URL'i kabul et.
_CATBOX_URL_RE = re.compile(
    r"^https?://(?:files\.)?catbox\.moe/[A-Za-z0-9_\-]+\.[A-Za-z0-9]+\s*$"
)


def rehost_to_catbox(video_url: str) -> str:
    """Replicate (veya başka geçici) video URL'ini Catbox.moe'ya kopyala.

    Args:
        video_url: kaynak http(s) URL

    Returns:
        str: kalıcı Catbox URL, ya da fail durumunda orijinal `video_url`.
        Asla raise etmez — caller akışı kesintisiz devam etsin.
    """
    if not video_url or not video_url.startswith("http"):
        return video_url

    try:
        resp = requests.post(
            CATBOX_API,
            data={"reqtype": "urlupload", "url": video_url},
            timeout=REQUEST_TIMEOUT,
        )
        if not resp.ok:
            log.warning(
                f"Catbox rehost başarısız ({resp.status_code}): "
                f"{resp.text[:200]} — orijinal URL kullanılacak"
            )
            return video_url

        body = (resp.text or "").strip()
        if _CATBOX_URL_RE.match(body):
            log.info(f"Video Catbox'a re-host edildi: {body}")
            return body

        log.warning(
            f"Catbox beklenmedik yanıt: '{body[:200]}' — orijinal URL kullanılacak"
        )
        return video_url

    except requests.exceptions.Timeout:
        log.warning(
            f"Catbox rehost timeout ({REQUEST_TIMEOUT}s) — orijinal URL kullanılacak"
        )
        return video_url
    except Exception:
        log.warning("Catbox rehost genel hatası — orijinal URL kullanılacak", exc_info=True)
        return video_url
