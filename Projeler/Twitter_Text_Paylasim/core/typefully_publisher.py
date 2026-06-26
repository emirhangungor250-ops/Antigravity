"""Typefully Draft Publisher (text + image draft).

X (Twitter) için Typefully'ye **draft** olarak post oluşturur — otomatik yayınlamaz.
Hesap sahibi Typefully UI'da inceleyip onaylar.

Akış:
  - Tek tweet:   POST /v2/social-sets/{ss}/drafts  (publish_at YOK → draft)
  - Thread:      Aynı endpoint, posts: [tweet1, tweet2, ...]
  - Görselli:    Önce /media/upload → S3 PUT → polling, sonra draft create
"""

import os
import re
import time
import mimetypes
from pathlib import Path
from typing import Callable

import requests

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "TypefullyPublisher")

BASE = "https://api.typefully.com/v2"


# ---------------------------------------------------------------------------
# Typefully 429 retry helper.
#
# IMPORTANT: This helper is duplicated by hand across 4 services
# (Twitter_Text_Paylasim, Twitter_Video_Paylasim, LinkedIn_Text_Paylasim,
# LinkedIn_Video_Paylasim — when the latter migrates to Typefully).
# Per monorepo shared-util constraint (`_skills/shared/` cannot be
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

# Internal/private linklerin tweet body'sine sızmasını engelleyen son savunma.
# Notion sayfaları + diğer dahili sistem linkleri tweet'e asla gitmemeli.
_FORBIDDEN_URL_PATTERNS = [
    re.compile(r"https?://(?:www\.)?notion\.so/\S+", re.IGNORECASE),
    re.compile(r"https?://(?:[\w-]+\.)?notion\.site/\S+", re.IGNORECASE),
]


def _sanitize_tweet(text: str) -> str:
    """Tweet metnindeki yasaklı internal URL'leri temizler.
    Tespit ederse loglar; tweet'i dropping yerine URL'i strip ediyoruz ki
    içerik tamamen kaybolmasın (skor zaten geçtiği için içerik değerli).
    """
    if not text:
        return text
    cleaned = text
    for pat in _FORBIDDEN_URL_PATTERNS:
        if pat.search(cleaned):
            ops.warning("Internal URL tespit edildi, strip ediliyor", pat.search(cleaned).group(0)[:120])
            cleaned = pat.sub("", cleaned)
    # URL strip sonrası fazladan boşluk/satır temizliği
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


class TypefullyDraftError(Exception):
    pass


class TypefullyDraftPublisher:
    def __init__(self):
        self.api_key = settings.TYPEFULLY_API_KEY
        self.social_set_id = settings.TYPEFULLY_SOCIAL_SET_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _ss_url(self, suffix: str) -> str:
        return f"{BASE}/social-sets/{self.social_set_id}{suffix}"

    def create_single_draft(self, text: str, linkedin_text: str | None = None) -> dict:
        """Tek tweet draft'ı. linkedin_text verilirse LinkedIn varyantı da eklenir."""
        x_posts = [{"text": _sanitize_tweet(text)}]
        li_posts = self._linkedin_posts(linkedin_text)
        return self._create_draft(x_posts, linkedin_posts=li_posts)

    def create_thread_draft(self, tweets: list[str], linkedin_text: str | None = None) -> dict:
        """Thread draft'ı. linkedin_text verilirse aynı draft'ta LinkedIn tek-postu."""
        if not tweets:
            raise TypefullyDraftError("Boş thread")
        x_posts = [{"text": _sanitize_tweet(t)} for t in tweets if t and t.strip()]
        li_posts = self._linkedin_posts(linkedin_text)
        return self._create_draft(x_posts, linkedin_posts=li_posts)

    def create_thread_draft_with_image(self, tweets: list[str], image_path: str,
                                       linkedin_text: str | None = None) -> dict:
        """Thread draft'ı, görsel ilk tweet'e iliştirilir. LinkedIn varyantına da görsel eklenir."""
        if not tweets:
            raise TypefullyDraftError("Boş thread")
        media_id = ""
        if image_path and os.path.exists(image_path):
            media_id = self._upload_image(image_path) or ""
        x_posts = [{"text": _sanitize_tweet(t)} for t in tweets if t and t.strip()]
        if media_id and x_posts:
            x_posts[0]["media_ids"] = [media_id]
        li_posts = self._linkedin_posts(linkedin_text, media_id=media_id)
        return self._create_draft(x_posts, linkedin_posts=li_posts)

    def create_single_draft_with_image(self, text: str, image_path: str,
                                       linkedin_text: str | None = None) -> dict:
        """Görselli tek tweet draft'ı. LinkedIn varyantına da aynı görsel eklenir."""
        media_id = ""
        if image_path and os.path.exists(image_path):
            media_id = self._upload_image(image_path) or ""
            if not media_id:
                ops.warning("Görsel upload başarısız, text-only draft'a dönülüyor")
        x_post = {"text": _sanitize_tweet(text)}
        if media_id:
            x_post["media_ids"] = [media_id]
        li_posts = self._linkedin_posts(linkedin_text, media_id=media_id)
        return self._create_draft([x_post], linkedin_posts=li_posts)

    def create_linkedin_only_draft(self, text: str, image_path: str | None = None) -> dict:
        """X devre dışı, sadece LinkedIn-only draft. LinkedIn_Text_Paylasim için."""
        if not text or not text.strip():
            raise TypefullyDraftError("LinkedIn metni boş")
        media_id = ""
        if image_path and os.path.exists(image_path):
            media_id = self._upload_image(image_path) or ""
            if not media_id:
                ops.warning("LinkedIn görsel upload başarısız, text-only fallback")
        li_posts = self._linkedin_posts(text, media_id=media_id) or []
        return self._create_draft(x_posts=None, linkedin_posts=li_posts)

    @staticmethod
    def _linkedin_posts(text: str | None, media_id: str = "") -> list[dict] | None:
        """LinkedIn için tek-post payload. Boş/None ise None döner (LinkedIn devre dışı)."""
        if not text or not text.strip():
            return None
        post = {"text": _sanitize_tweet(text)}
        if media_id:
            post["media_ids"] = [media_id]
        return [post]

    def _upload_image(self, image_path: str) -> str:
        """JPG/PNG upload → media_id (Twitter_Video_Paylasim publisher patternı)."""
        if settings.IS_DRY_RUN:
            ops.info("[DRY-RUN] Görsel upload atlandı")
            return "dry-run-media"

        ext = Path(image_path).suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png"):
            ops.error(f"Desteklenmeyen görsel uzantısı: {ext}")
            return ""
        safe_stem = "".join(c if ((c.isascii() and c.isalnum()) or c in "_.()-") else "_"
                            for c in Path(image_path).stem)[:200]
        file_name = f"{safe_stem}{ext}"
        try:
            r = typefully_call_with_retry(
                lambda: requests.post(self._ss_url("/media/upload"), headers=self.headers,
                                      json={"file_name": file_name}, timeout=20),
                log=ops,
            )
            if r.status_code != 201:
                ops.error(f"media/upload {r.status_code}: {r.text[:300]}")
                return ""
            data = r.json()
            media_id = data["media_id"]
            upload_url = data["upload_url"]
        except Exception as e:
            ops.error("media/upload exception", exception=e)
            return ""

        try:
            with open(image_path, "rb") as f:
                put = requests.put(upload_url, data=f, timeout=120)
            if put.status_code not in (200, 204):
                ops.error(f"S3 PUT {put.status_code}: {put.text[:300]}")
                return ""
        except Exception as e:
            ops.error("S3 PUT exception", exception=e)
            return ""

        # Polling
        poll = self._ss_url(f"/media/{media_id}")
        deadline = time.time() + 120
        while time.time() < deadline:
            try:
                pr = requests.get(poll, headers=self.headers, timeout=15)
                pr.raise_for_status()
                pd = pr.json()
                status = pd.get("status", "")
                if status == "ready":
                    return media_id
                if status == "failed":
                    ops.error(f"media processing failed: {pd.get('error_reason','?')}")
                    return ""
            except Exception as e:
                ops.warning(f"media polling: {e}")
            time.sleep(3)
        ops.error("media ready olmadı (120s)")
        return ""

    def _create_draft(self, x_posts: list[dict] | None, linkedin_posts: list[dict] | None = None) -> dict:
        platforms: dict = {}
        if x_posts:
            platforms["x"] = {"enabled": True, "posts": x_posts}
        if linkedin_posts:
            platforms["linkedin"] = {"enabled": True, "posts": linkedin_posts, "settings": {}}
        if not platforms:
            raise TypefullyDraftError("İçerik yok: hem X hem LinkedIn boş")

        if settings.IS_DRY_RUN:
            keys = ",".join(platforms.keys())
            ops.info("[DRY-RUN] Draft create atlandı", f"platforms={keys}")
            return {"draft_id": "dry-run", "share_url": "https://typefully.com/dry-run"}

        payload = {
            "platforms": platforms,
            # publish_at GİRİLMİYOR → Typefully draft olarak tutuyor
        }
        try:
            r = typefully_call_with_retry(
                lambda: requests.post(
                    self._ss_url("/drafts"),
                    headers=self.headers,
                    json=payload,
                    timeout=30,
                ),
                log=ops,
            )
            if r.status_code == 429:
                raise TypefullyDraftError(f"Rate limit; reset={r.headers.get('x-ratelimit-user-reset','?')}")
            if r.status_code not in (200, 201):
                raise TypefullyDraftError(f"draft create {r.status_code}: {r.text[:500]}")
            data = r.json()
            draft_id = data.get("id")
            share_url = data.get("share_url") or data.get("private_url") or f"typefully://draft/{draft_id}"
            ops.info("Draft oluşturuldu",
                     f"id={draft_id}, platforms={list(platforms.keys())}, url={share_url}")
            return {"draft_id": draft_id, "share_url": share_url}
        except TypefullyDraftError:
            raise
        except Exception as e:
            ops.error("draft create exception", exception=e)
            raise TypefullyDraftError(str(e))
