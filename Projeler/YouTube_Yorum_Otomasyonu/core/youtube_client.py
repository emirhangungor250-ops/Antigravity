# -*- coding: utf-8 -*-
"""YouTube Data API v3 — okuma (Faz 1, API key) + yazma (Faz 2, OAuth force-ssl).

Faz 1 okuma OAuth gerektirmez: yorumlar herkese açık veri, API key yeterli.
Yazma (comments.insert) Faz 2'de OAuth ile yt_write.py üzerinden yapılır.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field

import requests

import config

OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"

API = "https://www.googleapis.com/youtube/v3"


@dataclass
class Reply:
    author: str
    author_channel: str
    text: str
    published_at: str


@dataclass
class CommentThread:
    comment_id: str
    video_id: str
    author: str
    author_channel: str
    text: str
    like_count: int
    published_at: str
    total_replies: int
    replies: list[Reply] = field(default_factory=list)
    video_title: str = ""

    @property
    def channel_replied(self) -> bool:
        """Kanal sahibi bu thread'e cevap vermiş mi?"""
        return any(r.author_channel == config.CHANNEL_ID for r in self.replies)

    @property
    def channel_reply_text(self) -> str:
        """Kanalın bu thread'e verdiği İLK cevabın metni (corpus için)."""
        for r in self.replies:
            if r.author_channel == config.CHANNEL_ID:
                return r.text
        return ""

    @property
    def is_by_channel(self) -> bool:
        """Üst yorum bizzat kanal tarafından mı yazılmış (kendi yorumumuz)?"""
        return self.author_channel == config.CHANNEL_ID


def _get(path: str, params: dict, *, retries: int = 2) -> dict:
    params = {**params, "key": config.YOUTUBE_API_KEY}
    last = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(f"{API}/{path}", params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                last = RuntimeError(f"YouTube {r.status_code}: {r.text[:160]}")
            else:
                raise RuntimeError(f"YouTube {r.status_code}: {r.text[:200]}")
        except (requests.Timeout, requests.ConnectionError) as e:
            last = e
        if attempt < retries:
            time.sleep(1.5 * (attempt + 1))
    raise last or RuntimeError("YouTube GET başarısız")


def _parse_reply(item: dict) -> Reply:
    s = item.get("snippet", {})
    return Reply(
        author=s.get("authorDisplayName", ""),
        author_channel=(s.get("authorChannelId") or {}).get("value", ""),
        text=s.get("textOriginal", "") or "",
        published_at=s.get("publishedAt", ""),
    )


def fetch_all_replies(parent_id: str) -> list[Reply]:
    """Bir üst yorumun TÜM cevaplarını çek (inline 5'i aşan thread'ler için)."""
    out: list[Reply] = []
    page = None
    while True:
        params = {"part": "snippet", "parentId": parent_id, "maxResults": 100, "textFormat": "plainText"}
        if page:
            params["pageToken"] = page
        data = _get("comments", params)
        for it in data.get("items", []):
            out.append(_parse_reply(it))
        page = data.get("nextPageToken")
        if not page:
            break
    return out


def fetch_comment_threads(max_threads: int | None = None) -> list[CommentThread]:
    """Kanal geneli son yorum thread'lerini çek (zaman sıralı, yeniden eskiye)."""
    max_threads = max_threads or config.MAX_THREADS_PER_RUN
    threads: list[CommentThread] = []
    page = None
    while len(threads) < max_threads:
        params = {
            "part": "snippet,replies",
            "allThreadsRelatedToChannelId": config.CHANNEL_ID,
            "order": "time",
            "maxResults": 100,
            "textFormat": "plainText",
        }
        if page:
            params["pageToken"] = page
        data = _get("commentThreads", params)
        for it in data.get("items", []):
            sn = it.get("snippet", {})
            tlc = sn.get("topLevelComment", {})
            tlcs = tlc.get("snippet", {})
            total = sn.get("totalReplyCount", 0) or 0
            replies = [_parse_reply(r) for r in (it.get("replies", {}) or {}).get("comments", [])]
            t = CommentThread(
                comment_id=tlc.get("id", ""),
                video_id=tlcs.get("videoId", ""),
                author=tlcs.get("authorDisplayName", ""),
                author_channel=(tlcs.get("authorChannelId") or {}).get("value", ""),
                text=tlcs.get("textOriginal", "") or "",
                like_count=tlcs.get("likeCount", 0) or 0,
                published_at=tlcs.get("publishedAt", ""),
                total_replies=total,
            )
            # inline cevaplar 5 ile sınırlı; daha fazlası varsa tamamını çek
            # (kanal cevabını kaçırmamak + corpus için doğru eşleştirme)
            if total > len(replies):
                try:
                    t.replies = fetch_all_replies(t.comment_id)
                except Exception:
                    t.replies = replies
            else:
                t.replies = replies
            threads.append(t)
        page = data.get("nextPageToken")
        if not page:
            break
    return threads


def resolve_video_titles(video_ids: list[str]) -> dict[str, str]:
    """videoId -> başlık (50'şer batch). E-postada video adını göstermek için."""
    titles: dict[str, str] = {}
    uniq = [v for v in dict.fromkeys(video_ids) if v]
    for i in range(0, len(uniq), 50):
        batch = uniq[i:i + 50]
        data = _get("videos", {"part": "snippet", "id": ",".join(batch)})
        for it in data.get("items", []):
            titles[it["id"]] = it.get("snippet", {}).get("title", "")
    return titles


def is_recent(published_at: str, days: int) -> bool:
    """published_at (ISO) son `days` gün içinde mi?"""
    if not published_at:
        return False
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    age = datetime.now(timezone.utc) - dt
    return age.total_seconds() <= days * 86400


# ── Faz 2: yorum YAZMA (youtube.force-ssl OAuth) ─────────────────────
def _forcessl_token_raw() -> str:
    """force-ssl token JSON'unu getir: önce Railway env, sonra lokal dosya."""
    raw = os.environ.get(config.YT_TOKEN_ENV, "")
    if raw:
        return raw
    if os.path.exists(config.YT_TOKEN_PATH):
        with open(config.YT_TOKEN_PATH, encoding="utf-8") as f:
            return f.read()
    return ""


def _forcessl_access_token() -> str:
    """refresh_token'dan taze access token (manuel refresh — ekstra Google kütüphanesi yok)."""
    raw = _forcessl_token_raw()
    if not raw:
        raise RuntimeError(
            f"force-ssl token yok ({config.YT_TOKEN_ENV} / {config.YT_TOKEN_PATH}). "
            "Faz 2 yazma için önce setup_youtube_forcessl.py çalıştırılmalı.")
    tok = json.loads(raw)
    r = requests.post(OAUTH_TOKEN_URL, data={
        "client_id": tok.get("client_id") or config.YOUTUBE_CLIENT_ID,
        "client_secret": tok.get("client_secret") or config.YOUTUBE_CLIENT_SECRET,
        "refresh_token": tok["refresh_token"],
        "grant_type": "refresh_token",
    }, timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(f"OAuth refresh HTTP {r.status_code}: {r.text[:160]}")
    return r.json()["access_token"]


def post_reply(parent_comment_id: str, text: str) -> str:
    """Üst yoruma cevap YAYINLA (Faz 2). Döner: yeni cevabın YouTube id'si.
    DİKKAT: geri alınamaz + halka açık. Yalnızca kanal sahibinin onayından sonra çağrılmalı."""
    if not (parent_comment_id and text.strip()):
        raise ValueError("post_reply: parent_comment_id ve text zorunlu")
    token = _forcessl_access_token()
    r = requests.post(
        f"{API}/comments?part=snippet",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps({"snippet": {"parentId": parent_comment_id, "textOriginal": text}}),
        timeout=30,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"YouTube reply HTTP {r.status_code}: {r.text[:200]}")
    return r.json().get("id", "")
