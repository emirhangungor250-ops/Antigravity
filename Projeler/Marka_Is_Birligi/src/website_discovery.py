#!/usr/bin/env python3
"""Layer 0 — Website Discovery.

Markanın resmi website'ını bulmak için iki aşamalı arama:

  1. Heuristic (ücretsiz): brand_handle ve normalize edilmiş brand_name'in
     yaygın TLD'lerle kombinasyonunu HEAD + GET body kontrolüyle dene.
  2. Apify Google Search Scraper: "<brand_name> official site" araması yap,
     ilk geçerli organik sonucu döndür (sosyal/dizin sayfaları filtrelenir).
     Apify sonucu için brand-name domain guard uygulanır.

Returns:
    dict: {
        "url": "https://...",       # ya da ""
        "source": "heuristic" | "apify_search" | "none",
        "confidence": "high" | "medium" | "low",
        "trace": [str, ...],
        "apify_cost_usd": float,
    }
"""
from __future__ import annotations

import logging
import os
import sys
from urllib.parse import urlparse

import requests

# Proje root'unu path'e ekle ki env_loader import edilebilsin
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from env_loader import get_env  # type: ignore
except ImportError:
    def get_env(key, *_a, **_kw):
        return os.environ.get(key)

logger = logging.getLogger(__name__)

APIFY_TOKEN = (
    get_env("APIFY_API_KEY")
    or get_env("APIFY_API_KEY_1")
    or get_env("APIFY_API_KEY_2")
)
APIFY_ACTOR_ID = "apify~google-search-scraper"

BLOCKED_DOMAINS = {
    "wikipedia.org", "wikidata.org",
    "crunchbase.com", "linkedin.com", "github.com",
    "twitter.com", "x.com", "instagram.com", "facebook.com",
    "tiktok.com", "youtube.com", "youtu.be",
    "medium.com", "substack.com", "reddit.com",
    "producthunt.com", "g2.com", "capterra.com",
    "play.google.com", "apps.apple.com", "appstore.com",
    "bloomberg.com", "forbes.com", "techcrunch.com",
    "amazon.com", "amazon.co.uk",
    "pitchbook.com", "owler.com", "zoominfo.com",
    "trustpilot.com", "glassdoor.com",
    "notion.so", "gitbook.io",
    "discord.com", "discord.gg", "t.me", "telegram.me",
}

HEURISTIC_TLDS = [".ai", ".com", ".io", ".co", ".app"]

HEAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


def _normalize(text: str) -> str:
    if not text:
        return ""
    out = text.lower().strip()
    for suffix in [" ai", " official", "_official", ".official",
                   "_ai", ".ai", "_app", " app", " io", " tr"]:
        if out.endswith(suffix):
            out = out[: -len(suffix)]
    return "".join(ch for ch in out if ch.isalnum())


def _is_alive(url: str, timeout: int = 6) -> bool:
    """URL ayakta + body'li bir HTML sayfa mı? Parking/empty filtrelenir."""
    try:
        r = requests.head(
            url, timeout=timeout,
            allow_redirects=True, headers=HEAD_HEADERS,
        )
        if r.status_code >= 400 and r.status_code not in (403, 405, 501):
            return False
    except requests.exceptions.RequestException:
        return False

    try:
        r = requests.get(
            url, timeout=timeout,
            allow_redirects=True, headers=HEAD_HEADERS,
        )
        if r.status_code >= 400:
            return False
        body = (r.text or "").strip()
        if len(body) < 500:
            return False
        ctype = (r.headers.get("Content-Type") or "").lower()
        if "html" not in ctype and "text" not in ctype:
            return False
        return True
    except requests.exceptions.RequestException:
        return False


def _domain_of(url: str) -> str:
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    netloc = urlparse(url).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def _is_blocked_domain(url: str) -> bool:
    d = _domain_of(url)
    if not d:
        return True
    for blocked in BLOCKED_DOMAINS:
        if d == blocked or d.endswith("." + blocked):
            return True
    return False


def _domain_matches_brand(url: str, brand_name: str, brand_handle: str | None = None) -> bool:
    """Apify Google Search sonucunda yanlış pozitif filtresi.

    Aicatcheu4 → eastwenatcheewa.gov gibi marka adıyla alakasız sonuçları yakalar.
    Kural: domain root, normalize edilmiş brand veya handle ile en az 4-char örtüşmeli.
    Çok kısa marka adlarında (3 char altı) atla, kabul et.
    """
    domain = _domain_of(url)
    if not domain:
        return False
    domain_root = domain.split(".")[0]

    candidates = []
    nb = _normalize(brand_name)
    if nb:
        candidates.append(nb)
    nh = _normalize(brand_handle or "")
    if nh and nh not in candidates:
        candidates.append(nh)

    if not candidates:
        return True  # bilgi yok, gate kapatma

    for cand in candidates:
        if len(cand) < 3:
            return True
        if cand == domain_root:
            return True
        if cand in domain_root or domain_root in cand:
            return True
        for i in range(len(cand) - 3):
            chunk = cand[i:i + 4]
            if chunk in domain_root:
                return True
    return False


def _heuristic_candidates(brand_name: str, brand_handle: str | None) -> list[str]:
    bases: list[str] = []
    if brand_handle:
        bases.append(_normalize(brand_handle))
    if brand_name:
        bases.append(_normalize(brand_name))
    seen = set()
    uniq_bases = []
    for b in bases:
        if b and len(b) >= 3 and b not in seen:
            seen.add(b)
            uniq_bases.append(b)

    candidates: list[str] = []
    for base in uniq_bases:
        for tld in HEURISTIC_TLDS:
            candidates.append(f"https://{base}{tld}")
    return candidates


def _apify_google_search(query: str, timeout: int = 60) -> dict:
    if not APIFY_TOKEN:
        return {"organic": [], "cost_usd": 0.0, "error": "no_apify_token"}

    url = (
        f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}"
        f"/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    )
    payload = {
        "queries": query,
        "resultsPerPage": 5,
        "maxPagesPerQuery": 1,
        "countryCode": "us",
        "languageCode": "en",
        "saveHtml": False,
        "saveHtmlToKeyValueStore": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=timeout)
    except requests.exceptions.Timeout:
        return {"organic": [], "cost_usd": 0.0, "error": "apify_timeout"}
    except requests.exceptions.RequestException as e:
        return {"organic": [], "cost_usd": 0.0, "error": f"apify_network: {e}"}

    if r.status_code == 401:
        return {"organic": [], "cost_usd": 0.0, "error": "apify_auth_failed"}
    if r.status_code == 402:
        return {"organic": [], "cost_usd": 0.0, "error": "apify_quota_exhausted"}
    if r.status_code == 429:
        return {"organic": [], "cost_usd": 0.0, "error": "apify_rate_limit"}
    if r.status_code >= 400:
        return {
            "organic": [],
            "cost_usd": 0.0,
            "error": f"apify_http_{r.status_code}: {r.text[:200]}",
        }

    try:
        data = r.json()
    except ValueError:
        return {"organic": [], "cost_usd": 0.0, "error": "apify_invalid_json"}

    organic: list[dict] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                organic.extend(item.get("organicResults") or [])

    return {"organic": organic, "cost_usd": 0.007, "error": None}


def _pick_first_valid_organic(
    results: list[dict],
    brand_name: str,
    brand_handle: str | None,
) -> tuple[str, str] | None:
    """Organic sonuçlardan ilk geçerli URL'yi döndür (blocked + brand guard)."""
    for item in results:
        url = item.get("url") or item.get("link") or ""
        if not url:
            continue
        if _is_blocked_domain(url):
            continue
        parsed = urlparse(url)
        if not (parsed.scheme and parsed.netloc):
            continue
        root = f"{parsed.scheme}://{parsed.netloc}"
        if not _domain_matches_brand(root, brand_name, brand_handle):
            logger.info(f"Layer0 brand-guard reject: {root} (marka: {brand_name})")
            continue
        return root, item.get("title", "")
    return None


def find_official_website(
    brand_name: str,
    brand_handle: str | None = None,
) -> dict:
    """Markanın resmi sitesini bul.

    Sıra:
        1. Heuristic (HEAD+GET ile TLD denemeleri) → high confidence
        2. Apify Google Search Scraper → medium confidence (brand guard'lı)
        3. None → low confidence
    """
    trace: list[str] = []
    cost = 0.0

    candidates = _heuristic_candidates(brand_name, brand_handle)
    trace.append(f"heuristic candidates: {len(candidates)}")
    for c in candidates:
        if _is_alive(c):
            trace.append(f"heuristic hit: {c}")
            return {
                "url": c,
                "source": "heuristic",
                "confidence": "high",
                "trace": trace,
                "apify_cost_usd": cost,
            }
    trace.append("heuristic exhausted")

    if not APIFY_TOKEN:
        trace.append("apify skipped: no token")
        return {
            "url": "", "source": "none", "confidence": "low",
            "trace": trace, "apify_cost_usd": cost,
        }

    query = f"{brand_name} official site"
    trace.append(f"apify query: {query!r}")
    res = _apify_google_search(query)
    cost += res["cost_usd"]
    if res["error"]:
        trace.append(f"apify error: {res['error']}")
        return {
            "url": "", "source": "none", "confidence": "low",
            "trace": trace, "apify_cost_usd": cost,
        }

    trace.append(f"apify organic count: {len(res['organic'])}")
    picked = _pick_first_valid_organic(res["organic"], brand_name, brand_handle)
    if not picked:
        trace.append("apify: no valid organic (blocked/guard/empty)")
        return {
            "url": "", "source": "none", "confidence": "low",
            "trace": trace, "apify_cost_usd": cost,
        }
    url, title = picked
    if not _is_alive(url):
        trace.append(f"apify pick dead: {url}")
        return {
            "url": "", "source": "none", "confidence": "low",
            "trace": trace, "apify_cost_usd": cost,
        }

    trace.append(f"apify hit: {url} ({title!r})")
    return {
        "url": url,
        "source": "apify_search",
        "confidence": "medium",
        "trace": trace,
        "apify_cost_usd": cost,
    }


if __name__ == "__main__":
    import json
    samples = [
        ("Manus", "manusaiofficial"),
        ("Yandex Turkiye", "yandex__turkiye"),
        ("Aicatcheu4", "aicatcheu4"),
    ]
    for name, handle in samples:
        r = find_official_website(name, handle)
        print(f"\n=== {name} ===")
        print(json.dumps(r, indent=2, ensure_ascii=False))
