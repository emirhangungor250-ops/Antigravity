"""Reels indir + Supabase Storage'a yükle + public URL al.

HappyScribe transcription oluşturmak için public CDN URL gerekiyor; Instagram CDN
URL'leri kabul edilmiyor (5xx). Bu modül yt-dlp ile reels'ı /tmp'ye indirir, sonra
Supabase Storage `reels-source` bucket'ına yükler.
"""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import httpx
import yt_dlp

from core.config import Config

BUCKET = "reels-source"
APIFY_ACTOR = "apify~instagram-scraper"
APIFY_SYNC_TIMEOUT = 180


@dataclass
class DownloadedReel:
    shortcode: str
    local_path: Path
    public_url: str
    duration_sec: float | None
    title: str | None


def shortcode_from_url(url: str) -> str:
    m = re.search(r"/(reel|p|tv)/([^/?#]+)", url)
    if not m:
        raise ValueError(f"Reels shortcode URL'den çıkarılamadı: {url}")
    return m.group(2)


def download_reel(url: str, dest_dir: Path | None = None, cookies_browser: str = "safari") -> tuple[Path, dict]:
    """Instagram reels indir. Login wall'u aşmak için browser cookies kullanır.

    Production'da Apify scraper'a geçilecek (Sprint 2). Lokal test için
    cookies_browser parametresi default safari — kullanıcının makinesinde
    Instagram'a login olduğu varsayılır.
    """
    dest_dir = dest_dir or Path(tempfile.mkdtemp(prefix="reels_"))
    dest_dir.mkdir(parents=True, exist_ok=True)
    opts = {
        "outtmpl": str(dest_dir / "%(id)s.%(ext)s"),
        "format": "mp4/bestvideo[ext=mp4]+bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "cookiesfrombrowser": (cookies_browser,) if cookies_browser else None,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    file_path = Path(info["requested_downloads"][0]["filepath"])
    return file_path, info


def upload_to_supabase(cfg: Config, local_path: Path, object_name: str) -> str:
    content_type = "video/mp4" if local_path.suffix.lower() == ".mp4" else "application/octet-stream"
    with local_path.open("rb") as f:
        r = httpx.post(
            f"{cfg.supabase_url}/storage/v1/object/{BUCKET}/{object_name}",
            headers={
                "apikey": cfg.supabase_anon_key,
                "Authorization": f"Bearer {cfg.supabase_anon_key}",
                "Content-Type": content_type,
                "x-upsert": "true",
            },
            content=f.read(),
            timeout=120,
        )
    if r.status_code >= 300:
        raise RuntimeError(f"Supabase upload HTTP {r.status_code}: {r.text[:200]}")
    return f"{cfg.supabase_url}/storage/v1/object/public/{BUCKET}/{object_name}"


def apify_fetch_reel_meta(cfg: Config, reels_url: str) -> dict:
    """Apify instagram-scraper ile reel detayını çek. videoUrl + caption + meta."""
    r = httpx.post(
        f"https://api.apify.com/v2/acts/{APIFY_ACTOR}/run-sync-get-dataset-items",
        params={"token": cfg.apify_api_key, "timeout": APIFY_SYNC_TIMEOUT},
        json={
            "directUrls": [reels_url],
            "resultsType": "details",
            "resultsLimit": 1,
            "addParentData": False,
        },
        timeout=APIFY_SYNC_TIMEOUT + 10,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Apify HTTP {r.status_code}: {r.text[:200]}")
    items = r.json()
    if not items:
        raise RuntimeError(f"Apify boş döndü — reel URL geçersiz veya silinmiş: {reels_url}")
    return items[0]


def download_video_from_url(video_url: str, dest_dir: Path | None = None, ext: str = ".mp4") -> Path:
    dest_dir = dest_dir or Path(tempfile.mkdtemp(prefix="reels_"))
    dest_dir.mkdir(parents=True, exist_ok=True)
    local_path = dest_dir / f"download{ext}"
    with httpx.stream("GET", video_url, follow_redirects=True, timeout=120) as r:
        r.raise_for_status()
        with local_path.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    return local_path


def fetch_reel(
    cfg: Config,
    reels_url: str,
    *,
    local_file: Path | None = None,
    downloader: str = "apify",
) -> DownloadedReel:
    """Reels'ı çek, Supabase Storage'a yükle, DownloadedReel döndür.

    downloader:
      - 'apify' (default): Apify Instagram scraper → mp4 indir → Supabase
      - 'ytdlp': yt-dlp + cookies-from-browser (lokal Safari/Chrome login)
      - 'local': local_file parametresiyle verilen lokal mp4 dosyasını yükle
    """
    shortcode = shortcode_from_url(reels_url)
    meta: dict = {}
    title = ""
    duration = None

    if downloader == "local":
        if not local_file or not local_file.exists():
            raise FileNotFoundError(f"local_file bulunamadı: {local_file}")
        local_path = local_file
    elif downloader == "apify":
        meta = apify_fetch_reel_meta(cfg, reels_url)
        video_url = meta.get("videoUrl")
        if not video_url:
            raise RuntimeError(f"Apify item'da videoUrl yok: {list(meta.keys())[:8]}")
        local_path = download_video_from_url(video_url)
        duration = meta.get("videoDuration")
        title = meta.get("caption") or meta.get("alt") or ""
    elif downloader == "ytdlp":
        local_path, info = download_reel(reels_url)
        duration = info.get("duration")
        title = info.get("title") or info.get("description") or ""
    else:
        raise ValueError(f"Bilinmeyen downloader: {downloader}")

    object_name = f"{shortcode}{local_path.suffix}"
    public_url = upload_to_supabase(cfg, local_path, object_name)
    return DownloadedReel(
        shortcode=shortcode,
        local_path=local_path,
        public_url=public_url,
        duration_sec=duration,
        title=title[:200] if title else None,
    )


if __name__ == "__main__":
    import sys
    cfg = Config.from_env()
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.instagram.com/reel/DOX9_KOEi5Z/"
    print(f"⏬ İndiriliyor: {url}")
    r = fetch_reel(cfg, url)
    print(f"   shortcode: {r.shortcode}")
    print(f"   local:     {r.local_path} ({r.local_path.stat().st_size:,} bytes)")
    print(f"   duration:  {r.duration_sec}s")
    print(f"   public:    {r.public_url}")
