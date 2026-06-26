"""Typefully üzerinden LinkedIn video paylaşımı.

Akış:
  1) POST /media/upload → media_id + presigned S3 URL
  2) PUT video binary'sini upload_url'e
  3) Polling: GET /media/{id} → status='ready'
  4) POST /drafts (publish_at='now', platforms.linkedin) → Typefully LinkedIn paylaşımını tetikler
  5) Polling: GET /drafts/{id} → status='published' → LinkedIn URL

Typefully tek hesap üzerinden birden fazla social set tutar; X için ayrı, LinkedIn
için ayrı social_set_id kullanılır. API anahtarı (`TYPEFULLY_API_KEY`) hesap
düzeyinde tek; social_set_id LinkedIn için ayrı env var (`TYPEFULLY_LINKEDIN_SOCIAL_SET_ID`).

Bu pattern Twitter_Video_Paylasim'den birebir kopyalandı; sadece social_set kaynağı ve
publish payload'undaki platform anahtarı (`linkedin`) farklı.
"""

import os
import time
from pathlib import Path
from typing import Callable

import requests

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("LinkedIn_Video_Paylasim", "TypefullyPublisher")

BASE = "https://api.typefully.com/v2"


# ---------------------------------------------------------------------------
# Typefully 429 retry helper.
#
# IMPORTANT: This helper is duplicated by hand across 4 services
# (Twitter_Text_Paylasim, Twitter_Video_Paylasim, LinkedIn_Text_Paylasim,
# LinkedIn_Video_Paylasim).
# Per Antigravity shared-util constraint (`_skills/shared/` cannot be
# imported across Railway services because each service has its own
# rootDirectory), there is no central module. If you change behavior
# here, MIRROR THE EDIT into the other 3 typefully_publisher.py files.
# ---------------------------------------------------------------------------
def typefully_call_with_retry(
    fn: Callable[[], requests.Response],
    *,
    max_attempts: int = 3,
    log=None,
) -> requests.Response:
    """Wrap a Typefully HTTP call so 429s are retried with Retry-After-aware sleep.

    fn must be a zero-arg callable returning the requests.Response (no raise on
    non-2xx). On 429 we read Retry-After (seconds) or x-ratelimit-user-reset,
    sleep min 5s / max 120s, retry up to max_attempts. Other statuses are
    returned as-is for the caller to inspect.
    """
    resp: requests.Response | None = None
    for attempt in range(1, max_attempts + 1):
        resp = fn()
        if resp.status_code != 429 or attempt == max_attempts:
            return resp
        retry_after_raw = (
            resp.headers.get("Retry-After")
            or resp.headers.get("x-ratelimit-user-reset", "")
        )
        try:
            sleep_s = min(int(float(retry_after_raw)), 120)
        except (TypeError, ValueError):
            sleep_s = 30
        sleep_s = max(sleep_s, 5)
        if log is not None:
            try:
                log.warning(
                    "Typefully 429 — sleeping",
                    f"{sleep_s}s (attempt {attempt}/{max_attempts})",
                )
            except Exception:
                pass
        time.sleep(sleep_s)
    return resp  # type: ignore[return-value]


class TypefullyError(Exception):
    """Typefully veya S3 upload hatası — pipeline'ı durdurur, sonraki cron'a bırakır."""
    pass


class TypefullyRateLimited(TypefullyError):
    """Raised when Typefully API returns 429."""
    pass


class TypefullyPublisher:
    def __init__(self):
        self.api_key = settings.TYPEFULLY_API_KEY
        self.social_set_id = settings.TYPEFULLY_LINKEDIN_SOCIAL_SET_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _ss_url(self, suffix: str) -> str:
        return f"{BASE}/social-sets/{self.social_set_id}{suffix}"

    def upload_video(self, video_path: str) -> str:
        """Returns media_id (UUID) when ready, empty string on failure."""
        if not video_path or not os.path.exists(video_path):
            ops.error(f"Video bulunamadı: {video_path}")
            return ""

        if settings.IS_DRY_RUN:
            ops.info(f"[DRY-RUN] Typefully media upload atlandı: {video_path}")
            return "dry-run-media-id"

        # Typefully filename pattern: ^[a-zA-Z0-9_.()\-]+\.(jpg|...|mp4|mov|pdf)$
        ext = Path(video_path).suffix.lower()
        if ext not in (".mp4", ".mov"):
            ops.error(f"Desteklenmeyen video uzantısı: {ext}")
            return ""
        # Sanitize file_name to satisfy Typefully regex
        safe_stem = "".join(c if ((c.isascii() and c.isalnum()) or c in "_.()-") else "_" for c in Path(video_path).stem)[:200]
        file_name = f"{safe_stem}{ext}"

        try:
            r = typefully_call_with_retry(
                lambda: requests.post(
                    self._ss_url("/media/upload"),
                    headers=self.headers,
                    json={"file_name": file_name},
                    timeout=20,
                ),
                log=ops,
            )
            if r.status_code == 429:
                reset = r.headers.get("x-ratelimit-user-reset", "?")
                raise TypefullyRateLimited(f"media/upload rate limit; reset={reset}")
            if r.status_code != 201:
                raise TypefullyError(f"media/upload {r.status_code}: {r.text[:300]}")
            data = r.json()
            media_id = data["media_id"]
            upload_url = data["upload_url"]
        except TypefullyError:
            raise
        except Exception as e:
            raise TypefullyError(f"media/upload exception: {e}") from e

        # PUT raw bytes to S3 presigned URL.
        # Content-Type GÖNDERME — Typefully presigned URL'i Content-Type olmadan imzalıyor;
        # header eklersek SignatureDoesNotMatch alırız.
        try:
            with open(video_path, "rb") as f:
                put = requests.put(upload_url, data=f, timeout=600)
            if put.status_code not in (200, 204):
                raise TypefullyError(f"S3 PUT {put.status_code}: {put.text[:400]}")
            ops.info(f"S3 upload tamam ({Path(video_path).stat().st_size/1024/1024:.1f}MB) media_id={media_id[:8]}…")
        except TypefullyError:
            raise
        except Exception as e:
            raise TypefullyError(f"S3 PUT exception: {e}") from e

        if not self._wait_media_ready(media_id, label="media"):
            raise TypefullyError(f"media {media_id[:8]}… ready olmadı")
        return media_id

    def _wait_media_ready(self, media_id: str, label: str = "media", max_wait: int = 300) -> bool:
        url = self._ss_url(f"/media/{media_id}")
        deadline = time.time() + max_wait
        last_status = ""
        while time.time() < deadline:
            try:
                r = requests.get(url, headers=self.headers, timeout=15)
                r.raise_for_status()
                data = r.json()
                status = data.get("status", "")
                if status != last_status:
                    ops.info(f"{label} status: {status}")
                    last_status = status
                if status == "ready":
                    return True
                if status == "failed":
                    ops.error(f"{label} processing failed: {data.get('error_reason','?')}")
                    return False
            except Exception as e:
                ops.warning(f"{label} polling hatası: {e}")
            time.sleep(5)
        ops.error(f"{label} hazır olmadı ({max_wait}s timeout)")
        return False

    def post_to_linkedin(self, text: str, media_id: str) -> str:
        """Post'u Typefully → LinkedIn kuyruğuna 'şimdi yayınla' olarak gönder.
        Returns LinkedIn permalink URL on success, empty string on failure.
        """
        if settings.IS_DRY_RUN:
            ops.info(f"[DRY-RUN] Typefully draft → 'now' publish: '{text[:80]}…' media={media_id}")
            return "https://www.linkedin.com/feed/update/dry-run/"

        payload = {
            "platforms": {
                "linkedin": {
                    "enabled": True,
                    "posts": [{"text": text, "media_ids": [media_id] if media_id else []}],
                }
            },
            "publish_at": "now",
        }
        try:
            r = typefully_call_with_retry(
                lambda: requests.post(self._ss_url("/drafts"), headers=self.headers, json=payload, timeout=30),
                log=ops,
            )
            if r.status_code == 429:
                reset = r.headers.get("x-ratelimit-user-reset", "?")
                raise TypefullyRateLimited(f"draft create rate limit; reset={reset}")
            if r.status_code not in (200, 201):
                raise TypefullyError(f"draft create {r.status_code}: {r.text[:500]}")
            data = r.json()
            draft_id = data.get("id")
            ops.info(f"Draft oluşturuldu (id={draft_id}); 'now' publish bekleniyor")
        except TypefullyError:
            raise
        except Exception as e:
            raise TypefullyError(f"draft create exception: {e}") from e

        # Poll draft until published or error
        return self._wait_draft_published(draft_id) or ""

    def _wait_draft_published(self, draft_id, max_wait: int = 180) -> str:
        url = self._ss_url(f"/drafts/{draft_id}")
        deadline = time.time() + max_wait
        last_status = ""
        while time.time() < deadline:
            try:
                r = requests.get(url, headers=self.headers, timeout=15)
                r.raise_for_status()
                data = r.json()
                status = (data.get("status") or "").lower()
                if not status:
                    if data.get("published_at"):
                        status = "published"
                    elif data.get("scheduled_date"):
                        status = "scheduled"
                if status != last_status:
                    ops.info(f"draft {draft_id} status: {status or 'unknown'}")
                    last_status = status
                if status == "published":
                    # Try LinkedIn-specific URL fields first; fall back to share URLs.
                    li_url = (
                        data.get("linkedin_published_url")
                        or data.get("linkedin_url")
                    )
                    if li_url:
                        return li_url
                    return data.get("share_url") or data.get("private_url") or f"typefully://draft/{draft_id}"
                if status in ("error", "failed"):
                    ops.error(f"Draft publish başarısız: {data}")
                    return ""
            except Exception as e:
                ops.warning(f"draft polling hatası: {e}")
            time.sleep(5)
        ops.warning(f"Draft yayınlanma timeout ({max_wait}s) — Typefully arka planda devam edebilir")
        return f"typefully://draft/{draft_id}"
