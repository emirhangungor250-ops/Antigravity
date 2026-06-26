"""YouTube transcript çekimi — Apify üzerinden.

YouTube datacenter/lokal IP'leri sıklıkla blokluyor; bu yüzden
youtube-transcript-api yerine Apify actor `pintostudio/youtube-transcript-scraper`
kullanıyoruz. Maliyet: $10/1000 video — ihmal edilebilir.

Output (her segment): {"start": float, "text": str, "duration": float}
"""

import os
import re
import time
import requests

ACTOR_ID = "pintostudio~youtube-transcript-scraper"
APIFY_BASE = "https://api.apify.com/v2"
POLL_INTERVAL_SEC = 5
RUN_TIMEOUT_SEC = 180

_VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})")


def extract_video_id(url: str) -> str | None:
    if not url:
        return None
    m = _VIDEO_ID_RE.search(url)
    return m.group(1) if m else None


def _apify_token() -> str | None:
    return os.getenv("APIFY_API_KEY_1") or os.getenv("APIFY_API_KEY_2")


def _run_actor(video_url: str) -> list[dict]:
    token = _apify_token()
    if not token:
        print("[transcript] APIFY_API_KEY_1 yok.")
        return []

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    start = requests.post(
        f"{APIFY_BASE}/acts/{ACTOR_ID}/runs",
        headers=headers,
        json={"videoUrl": video_url},
        timeout=30,
    )
    if start.status_code >= 400:
        print(f"[transcript] actor start hata {start.status_code}: {start.text[:200]}")
        return []
    run_id = start.json()["data"]["id"]

    deadline = time.time() + RUN_TIMEOUT_SEC
    dataset_id = None
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_SEC)
        rr = requests.get(f"{APIFY_BASE}/actor-runs/{run_id}", headers=headers, timeout=20)
        if rr.status_code >= 400:
            continue
        data = rr.json()["data"]
        status = data["status"]
        if status == "SUCCEEDED":
            dataset_id = data["defaultDatasetId"]
            break
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            print(f"[transcript] actor {status}: {video_url}")
            return []
    if not dataset_id:
        print(f"[transcript] actor timeout: {video_url}")
        return []

    ds = requests.get(f"{APIFY_BASE}/datasets/{dataset_id}/items", headers=headers, timeout=60)
    if ds.status_code >= 400:
        return []
    return ds.json()


def fetch_transcript(video_id_or_url: str) -> list[dict]:
    """[{start: float, text: str, duration: float}, ...] döner. Boşsa [].

    Argüman video_id veya tam URL olabilir; içeride normalize edilir.
    """
    if video_id_or_url.startswith("http"):
        url = video_id_or_url
    else:
        url = f"https://www.youtube.com/watch?v={video_id_or_url}"

    items = _run_actor(url)
    if not items:
        return []

    # Apify actor genelde top-level liste döndürür ama bazen
    # {"data": [...]} sarmalaması yapabilir — iki ihtimali de işle
    if isinstance(items, dict):
        items = items.get("data") or items.get("transcript") or []
    if items and isinstance(items, list) and isinstance(items[0], dict) and "data" in items[0] and isinstance(items[0]["data"], list):
        items = items[0]["data"]

    segments: list[dict] = []
    for it in items:
        text = (it.get("text") or "").strip()
        if not text:
            continue
        try:
            start = float(it.get("start", 0))
        except (TypeError, ValueError):
            start = 0.0
        try:
            duration = float(it.get("dur") or it.get("duration") or 0)
        except (TypeError, ValueError):
            duration = 0.0
        segments.append({"start": start, "text": text, "duration": duration})

    return segments


def format_for_prompt(segments: list[dict], step: int = 15) -> str:
    """Her ~step saniyede bir [mm:ss] tag'i ile birleştirilmiş transcript.

    Claude'un chapter üretiminde saniye sınırlarını doğru tahmin etmesi için
    transcript'i timestamp tag'leri ile dolduruyoruz.
    """
    if not segments:
        return ""
    lines: list[str] = []
    next_mark = 0
    for seg in segments:
        if seg["start"] >= next_mark:
            mm = int(seg["start"]) // 60
            ss = int(seg["start"]) % 60
            lines.append(f"\n[{mm:02d}:{ss:02d}]")
            next_mark = seg["start"] + step
        lines.append(seg["text"])
    return " ".join(lines).strip()


def total_duration_seconds(segments: list[dict]) -> int:
    if not segments:
        return 0
    last = segments[-1]
    return int(last["start"] + last["duration"])


def fetch_youtube_duration(video_id: str) -> int:
    """YouTube Data API ile videonun süresini saniye olarak çek (transcript yoksa fallback).

    Returns 0 if API key missing or any error.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return 0
    try:
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "contentDetails", "id": video_id, "key": api_key},
            timeout=15,
        )
        items = r.json().get("items", [])
        if not items:
            return 0
        iso = items[0].get("contentDetails", {}).get("duration", "PT0S")
        # ISO 8601 PT#H#M#S
        m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
        if not m:
            return 0
        h, mn, s = (int(x) if x else 0 for x in m.groups())
        return h * 3600 + mn * 60 + s
    except Exception as e:
        print(f"[transcript] YT API duration hatası ({video_id}): {e}")
        return 0
