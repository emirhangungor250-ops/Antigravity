"""Bir kerelik: kendi YouTube kanalınızın son ~100 videosunun açıklamasını
Apify ile çek, iki çıktı üret:

  1. data/style_corpus.json  → son 30 video {title, description, url}  (few-shot için)
  2. data/brand_affiliates.json → marka_anahtari → en sık görülen affiliate link map

Apify actor: streamers/youtube-scraper
Çalıştırma:
    cd Projeler/YT_Aciklama_Otomasyonu
    python scripts/build_style_corpus.py
"""

import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent.parent / "_knowledge" / "credentials" / "master.env")

APIFY_TOKEN = os.getenv("APIFY_API_KEY_1") or os.getenv("APIFY_API_KEY_2")
CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "")
ACTOR_ID = "streamers~youtube-scraper"

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
STYLE_PATH = DATA_DIR / "style_corpus.json"
AFFILIATE_PATH = DATA_DIR / "brand_affiliates.json"

CHANNEL_URL = f"https://www.youtube.com/channel/{CHANNEL_ID}/videos"

# Affiliate / ref pattern'leri
AFFILIATE_QS_RE = re.compile(r"[?&](?:ref|via|aff|affiliate|partner|coupon|promo)=", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s\)\]\}<>\"']+")
# Kendi promo kodunuz/handle'ınız sıkça affiliate işaretidir.
# AFFILIATE_HINT_KEYWORD env değişkeni ile kendi kodunuzu verin (örn. promo kodunuz).
_AFFILIATE_HINT = os.getenv("AFFILIATE_HINT_KEYWORD", "").strip()
AFFILIATE_HINT_RE = re.compile(re.escape(_AFFILIATE_HINT), re.IGNORECASE) if _AFFILIATE_HINT else None


def run_apify(payload: dict, timeout: int = 600) -> list[dict]:
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}", "Content-Type": "application/json"}
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs"
    print(f"[apify] start: {ACTOR_ID}")
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    run_id = r.json()["data"]["id"]
    print(f"[apify] run_id={run_id} polling...")

    start = time.time()
    while True:
        if time.time() - start > timeout:
            print("[apify] timeout")
            return []
        rr = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}", headers=headers, timeout=30)
        rr.raise_for_status()
        data = rr.json()["data"]
        status = data["status"]
        if status == "SUCCEEDED":
            ds_id = data["defaultDatasetId"]
            ds = requests.get(
                f"https://api.apify.com/v2/datasets/{ds_id}/items",
                headers=headers,
                timeout=120,
            )
            ds.raise_for_status()
            items = ds.json()
            print(f"[apify] succeeded, items={len(items)}")
            return items
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            print(f"[apify] failed: {status}")
            return []
        time.sleep(8)


def extract_brand_from_url(url: str) -> str | None:
    """https://ornek-marka.com/?ref=KOD → 'ornek-marka'."""
    m = re.match(r"https?://(?:www\.)?([^/?#]+)", url)
    if not m:
        return None
    host = m.group(1)
    # Subdomain'leri at, ana domain'in birinci segmentini al
    parts = host.split(".")
    if len(parts) >= 2:
        # short.aff.dom.com → 'dom' yerine; topview.ai → 'topview'
        # heuristik: TLD'siz son segment
        return parts[-2].lower()
    return host.lower()


def parse_videos(items: list[dict]) -> list[dict]:
    """Apify item → {title, url, description, viewCount, date}."""
    out = []
    for it in items:
        title = it.get("title") or it.get("videoTitle") or ""
        url = it.get("url") or it.get("videoUrl") or ""
        desc = it.get("text") or it.get("description") or ""
        view_count = it.get("viewCount") or it.get("views") or 0
        date = it.get("date") or it.get("publishedAt") or ""
        if not title or not desc:
            continue
        out.append({
            "title": title,
            "url": url,
            "description": desc,
            "view_count": view_count,
            "date": date,
        })
    return out


def build_style_corpus(videos: list[dict], n: int = 30) -> list[dict]:
    """En çok izlenen N video açıklamasını few-shot kütüphanesi yap.

    En çok izlenenler genelde "iyi yazılmış" örneklerdir.
    """
    def _vc(v):
        try:
            return int(v.get("view_count") or 0)
        except Exception:
            return 0
    sorted_videos = sorted(videos, key=_vc, reverse=True)
    return [
        {"title": v["title"], "url": v["url"], "description": v["description"]}
        for v in sorted_videos[:n]
    ]


def build_affiliate_map(videos: list[dict]) -> dict[str, str]:
    """Marka → en sık görünen affiliate link.

    Strateji:
      - Tüm açıklamalardaki URL'leri çıkar
      - Sadece affiliate-pattern'i veya AFFILIATE_HINT_KEYWORD içerenleri al
      - Marka adı = host'un ana segmenti
      - Marka başına en sık görüleni seç
    """
    brand_links: dict[str, Counter] = defaultdict(Counter)
    for v in videos:
        for url in URL_RE.findall(v["description"]):
            hint_match = AFFILIATE_HINT_RE.search(url) if AFFILIATE_HINT_RE else False
            if not (AFFILIATE_QS_RE.search(url) or hint_match):
                continue
            brand = extract_brand_from_url(url)
            if not brand:
                continue
            # youtube, instagram, tiktok gibi sosyal medyaları filtrele
            if brand in {"youtube", "youtu", "instagram", "tiktok", "twitter", "x", "facebook", "linkedin", "amazon"}:
                continue
            brand_links[brand][url] += 1

    return {brand: cnt.most_common(1)[0][0] for brand, cnt in brand_links.items()}


def main():
    if not APIFY_TOKEN:
        print("APIFY_API_KEY_1 eksik. .env veya master.env'i kontrol et.")
        sys.exit(1)

    payload = {
        "startUrls": [{"url": CHANNEL_URL}],
        "maxResults": 100,
        "maxResultsShorts": 0,
        "maxResultStreams": 0,
    }
    items = run_apify(payload)
    if not items:
        print("Apify boş döndü. Actor input formatı değişmiş olabilir.")
        sys.exit(2)

    videos = parse_videos(items)
    print(f"[parse] {len(videos)} kullanılabilir video (title+description dolu)")

    corpus = build_style_corpus(videos, n=30)
    with open(STYLE_PATH, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)
    print(f"[write] {STYLE_PATH}  → {len(corpus)} örnek")

    aff = build_affiliate_map(videos)
    with open(AFFILIATE_PATH, "w", encoding="utf-8") as f:
        json.dump(aff, f, ensure_ascii=False, indent=2)
    print(f"[write] {AFFILIATE_PATH}  → {len(aff)} marka")
    for brand, link in aff.items():
        print(f"  - {brand}: {link}")


if __name__ == "__main__":
    main()
