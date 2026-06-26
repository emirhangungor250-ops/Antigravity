"""
HMAC-imzalı, expiry'li tek-tıkla buton URL'leri için token üreteci.

Token formatı: <base64url(payload)>.<base64url(hmac_sha256(payload))>
payload = "<action>|<target_id>|<exp_unix_int>"

action ∈ {"mute", "snooze"}
target_id = Notion page id (thread tracker DB'sinde)
"""

import os
import hmac
import time
import base64
import hashlib
from typing import Optional, Tuple

DEFAULT_TTL_SECONDS = 14 * 24 * 3600  # 14 gün — digest mailler 7 gün içinde okunmazsa zaten anlamsız


def _secret() -> bytes:
    s = os.environ.get("BUTTON_HMAC_SECRET")
    if not s:
        raise RuntimeError("BUTTON_HMAC_SECRET env var set edilmemiş")
    return s.encode("utf-8")


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64d(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def make_token(action: str, target_id: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
    exp = int(time.time()) + ttl_seconds
    payload = f"{action}|{target_id}|{exp}".encode("utf-8")
    sig = hmac.new(_secret(), payload, hashlib.sha256).digest()
    return f"{_b64e(payload)}.{_b64e(sig)}"


def verify_token(token: str) -> Optional[Tuple[str, str]]:
    """Token geçerliyse (action, target_id) döner. Aksi halde None."""
    if not token or "." not in token:
        return None
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        payload = _b64d(payload_b64)
        sig = _b64d(sig_b64)
    except Exception:
        return None

    expected = hmac.new(_secret(), payload, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        return None

    try:
        action, target_id, exp_str = payload.decode("utf-8").split("|", 2)
        exp = int(exp_str)
    except Exception:
        return None

    if time.time() > exp:
        return None

    if action not in ("mute", "snooze"):
        return None

    return action, target_id
