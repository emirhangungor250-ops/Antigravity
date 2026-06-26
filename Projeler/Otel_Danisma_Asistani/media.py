"""Medya sınıflandırma — bir ManyChat mesajı düz metin mi, ses mi, görsel mi?

Marker'a güvenmek yerine URL'in GERÇEK Content-Type'ına HEAD/GET probe ile bakar. Probe
başarısız olursa uzantı/host sezgiselleriyle (heuristic) düşer.

Güvenlik: allow_redirects=False — açık yönlendirme zinciri/SSRF yüzeyini daraltır;
fiziksel dosya İNDİRMEZ (HEAD veya Range: bytes=0-0 ile yalnızca header alınır). URL değilse
veya hiç sinyal yoksa GÜVENLİ varsayılan "text" (ham URL ajana metin gibi geçer, asla indirilmez).
"""

from __future__ import annotations

import logging
import re

import requests

from config import CONFIG

log = logging.getLogger("hotel-chat.media")

# Lokal SSL-kesme ortamı bayrağı (diğer modüllerle aynı).
import os
_VERIFY_SSL = os.getenv("HOTELRUNNER_VERIFY_SSL", "1") != "0"

# Ses ipucu veren host/uzantı desenleri (IG/FB/ManyChat CDN'leri). Content-Type
# alınamazsa son çare olarak kullanılır. Görsel uzantısı varsa ses sayılMAZ.
_AUDIO_HOST_PATTERNS = (
    "lookaside.fbsbx.com",
    "lookaside.instagram.com",
    "scontent.cdninstagram.com",
    "manybot",
    "fbsbx",
    "fbcdn.net",
    ".mp4", ".m4a", ".ogg", ".opus", ".wav",
)
_IMAGE_EXT_RE = re.compile(r"\.(jpg|jpeg|png|webp|gif|heic)(\?|$)", re.I)
_URL_RE = re.compile(r"^https?://", re.I)
# Bazı CDN'ler User-Agent'sız isteği 403'ler (Wikimedia, bazı Meta uçları).
_UA = "Mozilla/5.0 (compatible; HotelChatBot/2.0)"
# Probe için fallback GET'e geçilecek HTTP durumları (HEAD reddi).
_FALLBACK_STATUSES = {403, 405, 501}


def _is_url(text: str) -> bool:
    return bool(text) and isinstance(text, str) and bool(_URL_RE.match(text.strip()))


def _is_image_url(text: str) -> bool:
    if not _is_url(text):
        return False
    return _IMAGE_EXT_RE.search(text.strip()) is not None


def _is_audio_url(text: str) -> bool:
    if not _is_url(text):
        return False
    lower = text.strip().lower()
    has_pattern = any(p in lower for p in _AUDIO_HOST_PATTERNS)
    # Görsel uzantısı varsa ses değildir (foto da fbcdn'den gelebilir).
    return has_pattern and not _is_image_url(text)


def _probe_content_type(url: str) -> str | None:
    """HEAD (gerekirse Range:bytes=0-0 GET) ile Content-Type başlığını çek.

    allow_redirects=False: yönlendirme zincirini takip etmeyiz (SSRF/açık-redirect yüzeyi).
    3xx gelirse Content-Type'a güvenmeyiz (hedef değil ara yanıt) → None (sezgisele düşülür).
    Dönüş: 'audio/mp4' gibi normalize Content-Type, veya başarısızsa None.
    """
    timeout = CONFIG.media_probe_timeout
    _hdr = {"User-Agent": _UA}  # bazı CDN'ler UA'sız isteği 403'ler
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=False,
                             headers=_hdr, verify=_VERIFY_SSL)
    except Exception as e:
        log.warning("[media] HEAD probe hata: %s", e)
        resp = None

    # HEAD başarısız ya da reddedildiyse (403/405/501) Range GET dene.
    if resp is None or resp.status_code in _FALLBACK_STATUSES:
        try:
            resp = requests.get(url, timeout=timeout, allow_redirects=False,
                                headers={**_hdr, "Range": "bytes=0-0"}, stream=True, verify=_VERIFY_SSL)
            resp.close()  # gövdeyi indirme; sadece header lazım
        except Exception as e:
            log.warning("[media] GET probe hata: %s", e)
            return None

    # Yönlendirme = belirsiz; Content-Type'a güvenme, sezgisele düş.
    if 300 <= resp.status_code < 400:
        log.info("[media] probe redirect (%s) — sezgisele düşülüyor", resp.status_code)
        return None

    ct_raw = resp.headers.get("content-type", "") or ""
    ct = ct_raw.split(";")[0].strip().lower()
    return ct or None


def classify_media_url(text: str) -> str:
    """Bir mesajı sınıflar: "audio" | "image" | "text".

    1) URL değilse → "text" (düz mesaj, aynen geçer)
    2) Content-Type probe: audio/* → "audio", image/* → "image", video/* → "image"*
       (* video'yu da görsel pipeline'ına yollarız: vision tek karede içeriği betimler;
        ayrı video çözümü yok, görsel betimleme en yakın güvenli davranış)
    3) Probe belirsiz/başarısız → sezgisel (uzantı/host)
    4) Hiç sinyal yoksa → GÜVENLİ varsayılan "text" (ham URL'i indirmeyiz)
    """
    if not _is_url(text):
        return "text"
    trimmed = text.strip()

    ct = _probe_content_type(trimmed)
    if ct:
        if ct.startswith("audio/"):
            return "audio"
        if ct.startswith("image/"):
            return "image"
        if ct.startswith("video/"):
            return "image"  # video → vision betimleme (ayrı video pipeline yok)
        # text/html, application/octet-stream vb. → sezgisele düş (CDN bazen yanlış tip verir)

    # Sezgisel fallback.
    if _is_image_url(trimmed):
        return "image"
    if _is_audio_url(trimmed):
        return "audio"
    return "text"
