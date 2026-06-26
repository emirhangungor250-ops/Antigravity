"""Notion X Posts logger — yeni DB için.

DB schema:
  Title (title), Source (select), Score (number), Status (select),
  Tweet Text (rich_text), Thread (rich_text), Source URL (url),
  Skip Reason (rich_text), Typefully Draft URL (url), Date (date)

Race condition mitigation:
  Twitter ve LinkedIn cron'ları aynı NOTION_X_DB_ID'ye yazıyor. Aynı dakikada
  ikisi birden çalışırsa (Pzt/Per UTC 05:00 + 07:10 penceresi) klasik
  check-then-create race'i duplicate satır üretebiliyordu. Soft idempotency:
  her satırın Title'ı `[<source_slug>:<sha1(key)[:12]>] ...` deterministik
  prefix ile başlar; _create_page() önce bu prefix'i arar (varsa skip),
  sonra create eder, sonra tekrar arar (>1 ise yenisini archive eder).
  Bu mantık LinkedIn_Text_Paylasim/core/notion_logger.py ile birebir aynı —
  Railway monorepo rootDirectory yüzünden shared util mümkün değil; iki
  dosyayı manuel hizalı tutuyoruz.
"""

import hashlib
import re
from datetime import datetime, timezone, timedelta

import requests

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "NotionLogger")

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def make_dedup_prefix(source: str, key: str) -> str:
    """Deterministik title prefix: `[<source_slug>:<sha1(key)[:12]>] `.

    source: Notion'daki Source select adı (örn. "GitHub", "AI Use Case",
            "LinkedIn Haber").
    key:    İçeriği tekilleştiren string (URL, title, weekly bucket vs.).
            Boş key gönderilirse prefix üretilmez (None döner).
    """
    if not source or not key:
        return ""
    src_slug = re.sub(r"[^a-z0-9]+", "_", source.lower()).strip("_")[:20] or "src"
    digest = hashlib.sha1(key.encode("utf-8", errors="ignore")).hexdigest()[:12]
    return f"[{src_slug}:{digest}] "


class NotionLogger:
    def __init__(self):
        self.token = settings.NOTION_TOKEN
        self.db_id = settings.NOTION_X_DB_ID
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def _enabled(self) -> bool:
        if not self.db_id:
            ops.warning("NOTION_X_DB_ID set değil, log atlanıyor")
            return False
        return True

    def is_already_processed(self, source_url: str) -> bool:
        """Aynı kaynak son N gün içinde işlendiyse True."""
        if not self._enabled() or not source_url:
            return False
        cutoff = (datetime.now(timezone.utc) - timedelta(days=settings.DEDUP_DAYS)).date().isoformat()
        payload = {
            "filter": {
                "and": [
                    {"property": "Source URL", "url": {"equals": source_url}},
                    {"property": "Date", "date": {"on_or_after": cutoff}},
                ]
            },
            "page_size": 1,
        }
        try:
            r = requests.post(f"{API}/databases/{self.db_id}/query",
                              headers=self.headers, json=payload, timeout=15)
            r.raise_for_status()
            return len(r.json().get("results", [])) > 0
        except Exception as e:
            ops.warning(f"Dedup query hatası: {e}")
            return False

    def is_already_processed_by_title(self, source: str, title: str) -> bool:
        """Aynı title aynı source'tan son 30 günde işlenmiş mi?"""
        if not self._enabled() or not title:
            return False
        cutoff = (datetime.now(timezone.utc) - timedelta(days=settings.DEDUP_DAYS)).date().isoformat()
        payload = {
            "filter": {"and": [
                {"property": "Source", "select": {"equals": source}},
                {"property": "Title", "title": {"equals": title}},
                {"property": "Date", "date": {"on_or_after": cutoff}},
            ]},
            "page_size": 1,
        }
        try:
            r = requests.post(f"{API}/databases/{self.db_id}/query",
                              headers=self.headers, json=payload, timeout=15)
            r.raise_for_status()
            return len(r.json().get("results", [])) > 0
        except Exception:
            return False

    def get_last_youtube_video_id(self) -> str:
        """En son işlenen YouTube videosunun ID'sini döner (Source URL'den parse)."""
        if not self._enabled():
            return ""
        payload = {
            "filter": {"property": "Source", "select": {"equals": "YouTube"}},
            "sorts": [{"property": "Date", "direction": "descending"}],
            "page_size": 1,
        }
        try:
            r = requests.post(f"{API}/databases/{self.db_id}/query",
                              headers=self.headers, json=payload, timeout=15)
            r.raise_for_status()
            results = r.json().get("results", [])
            if not results:
                return ""
            url_prop = results[0]["properties"].get("Source URL", {})
            url = url_prop.get("url", "") or ""
            # YouTube URL: https://www.youtube.com/watch?v=VIDEOID
            if "watch?v=" in url:
                return url.split("watch?v=")[-1].split("&")[0]
            return ""
        except Exception as e:
            ops.warning(f"Last YT video query hatası: {e}")
            return ""

    def log_skipped(self, source: str, source_url: str, score: int,
                    skip_reason: str, title: str = ""):
        """Eşik altı içeriği logla."""
        base_title = (title or skip_reason or f"{source} skipped")[:200]
        # Dedup key öncelik: source_url varsa onu kullan, yoksa base_title.
        dedup_key = source_url or base_title
        prefix = make_dedup_prefix(source, dedup_key)
        full_title = (prefix + base_title)[:200]
        self._create_page({
            "Title": {"title": [{"text": {"content": full_title}}]},
            "Source": {"select": {"name": source}},
            "Score": {"number": score},
            "Status": {"select": {"name": "Atlandı"}},
            "Source URL": {"url": source_url or None},
            "Skip Reason": {"rich_text": [{"text": {"content": skip_reason[:1990]}}]},
            "Date": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        }, dedup_prefix=prefix)

    def log_draft(self, source: str, source_url: str, score: int,
                  tweet_text: str = "", thread_tweets: list = None,
                  draft_url: str = "", title: str = "", image_url: str = "",
                  draft_id: str = "", linkedin_text: str = ""):
        """Draft olarak Typefully'ye gönderilmiş içeriği logla.

        linkedin_text: aynı draft'taki LinkedIn varyant metni (varsa).
        """
        base_title = (title or tweet_text[:60] or linkedin_text[:60] or f"{source} draft")[:200]
        thread_str = "\n\n---\n\n".join(thread_tweets) if thread_tweets else ""
        # Dedup key öncelik: source_url > tweet_text > linkedin_text > title
        dedup_key = source_url or (tweet_text[:200] if tweet_text else "") \
                              or (linkedin_text[:200] if linkedin_text else "") \
                              or base_title
        prefix = make_dedup_prefix(source, dedup_key)
        full_title = (prefix + base_title)[:200]
        props = {
            "Title": {"title": [{"text": {"content": full_title}}]},
            "Source": {"select": {"name": source}},
            "Score": {"number": score},
            "Status": {"select": {"name": "Draft"}},
            "Tweet Text": {"rich_text": [{"text": {"content": tweet_text[:1990]}}]},
            "Thread": {"rich_text": [{"text": {"content": thread_str[:1990]}}]},
            "LinkedIn Text": {"rich_text": [{"text": {"content": (linkedin_text or "")[:1990]}}]},
            "Source URL": {"url": source_url or None},
            "Typefully Draft URL": {"url": draft_url or None},
            "Typefully Draft ID": {"rich_text": [{"text": {"content": str(draft_id)[:200]}}]} if draft_id else {"rich_text": []},
            "Date": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        }
        if image_url:
            props["Image URL"] = {"url": image_url}
        self._create_page(props, dedup_prefix=prefix)

    def fetch_recent_titles_by_source(self, source: str, days: int = 30, limit: int = 30) -> list[str]:
        """Son N gün içinde source'tan üretilmiş Title'ları döner (use case dedup için)."""
        if not self._enabled():
            return []
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
        payload = {
            "filter": {"and": [
                {"property": "Source", "select": {"equals": source}},
                {"property": "Date", "date": {"on_or_after": cutoff}},
            ]},
            "sorts": [{"property": "Date", "direction": "descending"}],
            "page_size": limit,
        }
        try:
            r = requests.post(f"{API}/databases/{self.db_id}/query",
                              headers=self.headers, json=payload, timeout=15)
            r.raise_for_status()
            results = r.json().get("results", [])
            titles = []
            for row in results:
                title_arr = row["properties"].get("Title", {}).get("title", [])
                title = "".join(t.get("plain_text", "") for t in title_arr)
                if title:
                    titles.append(title)
            return titles
        except Exception as e:
            ops.warning(f"recent_titles query hatası: {e}")
            return []

    def log_failed(self, source: str, source_url: str, error: str, title: str = ""):
        base_title = (title or f"{source} failed")[:200]
        # Failed satırlarda da prefix kullanıyoruz — aynı hatanın iki cron'dan
        # iki kez loglanmasını engellemek için.
        dedup_key = source_url or base_title
        prefix = make_dedup_prefix(source, dedup_key) if dedup_key else ""
        full_title = (prefix + base_title)[:200]
        self._create_page({
            "Title": {"title": [{"text": {"content": full_title}}]},
            "Source": {"select": {"name": source}},
            "Status": {"select": {"name": "Failed"}},
            "Source URL": {"url": source_url or None},
            "Skip Reason": {"rich_text": [{"text": {"content": error[:1990]}}]},
            "Date": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        }, dedup_prefix=prefix or None)

    # ------------------------------------------------------------------
    # Race condition helpers
    # ------------------------------------------------------------------

    def _query_pages_by_prefix(self, prefix: str, page_size: int = 5) -> list:
        """Title `starts_with` prefix olan satırları döner (en eski → en yeni)."""
        if not prefix or not self._enabled():
            return []
        payload = {
            "filter": {"property": "Title", "title": {"starts_with": prefix}},
            "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
            "page_size": page_size,
        }
        try:
            r = requests.post(f"{API}/databases/{self.db_id}/query",
                              headers=self.headers, json=payload, timeout=15)
            r.raise_for_status()
            return r.json().get("results", []) or []
        except Exception as e:
            ops.warning(f"Prefix query hatası: {e}")
            return []

    def _archive_page(self, page_id: str) -> bool:
        try:
            r = requests.patch(f"{API}/pages/{page_id}",
                               headers=self.headers,
                               json={"archived": True}, timeout=15)
            return r.status_code in (200, 201)
        except Exception as e:
            ops.warning(f"Archive hatası ({page_id}): {e}")
            return False

    def _create_page(self, properties: dict, dedup_prefix: str | None = None):
        if not self._enabled():
            return

        # 1) Pre-create check: prefix zaten varsa create etme.
        if dedup_prefix:
            existing = self._query_pages_by_prefix(dedup_prefix, page_size=1)
            if existing:
                winner_id = existing[0].get("id", "")
                ops.info("Duplicate detected (race winner exists), skipping create",
                         f"prefix={dedup_prefix!r} winner={winner_id}")
                return

        payload = {
            "parent": {"database_id": self.db_id},
            "properties": properties,
        }
        try:
            r = requests.post(f"{API}/pages", headers=self.headers,
                              json=payload, timeout=20)
            if r.status_code not in (200, 201):
                ops.error(f"Notion log başarısız ({r.status_code}): {r.text[:300]}")
                return
            ops.info("Notion'a loglandı")
        except Exception as e:
            ops.error("Notion log exception", exception=e)
            return

        # 2) Post-create race detection: aynı prefix'ten >1 varsa loser'ı archive et.
        if dedup_prefix:
            try:
                rows = self._query_pages_by_prefix(dedup_prefix, page_size=5)
                if len(rows) > 1:
                    # En eskiyi (created_time ascending → ilk) bırak, kalanı archive et.
                    keeper = rows[0].get("id", "")
                    losers = [row for row in rows[1:] if row.get("id")]
                    ops.warning(
                        f"Race detected: prefix={dedup_prefix!r} keeper={keeper} "
                        f"archiving {len(losers)} loser(s)"
                    )
                    for row in losers:
                        self._archive_page(row["id"])
            except Exception as e:
                ops.warning(f"Race detection sonrası hata: {e}")
