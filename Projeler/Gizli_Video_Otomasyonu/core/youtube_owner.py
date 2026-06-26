"""Kanal sahibi olarak YouTube erişimi.

force-ssl token ile: gizli (unlisted) videoları listele, altyazı (transkript) indir.
yt-dlp ile videoyu indir (kapak motoru videoyu YouTube'dan çekemediği için).
Hepsi sahip yetkisiyle; Apify/paralı servis YOK.
"""
import json
import os
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import FORCESSL_TOKEN_ENV, FORCESSL_TOKEN_FILE


def _creds() -> Credentials:
    raw = os.getenv(FORCESSL_TOKEN_ENV)
    d = json.loads(raw) if raw else json.loads(FORCESSL_TOKEN_FILE.read_text(encoding="utf-8"))
    c = Credentials(
        token=d.get("token"), refresh_token=d.get("refresh_token"),
        token_uri=d.get("token_uri"), client_id=d.get("client_id"),
        client_secret=d.get("client_secret"), scopes=d.get("scopes"),
    )
    c.refresh(Request())
    return c


def service():
    return build("youtube", "v3", credentials=_creds(), cache_discovery=False)


def list_unlisted(limit: int = 25) -> list[dict]:
    """Kanaldaki gizli videoları döner: [{id, title, published, duration_sec}]."""
    yt = service()
    ch = yt.channels().list(part="contentDetails", mine=True).execute()
    uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    pl = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=limit).execute()
    ids = [i["contentDetails"]["videoId"] for i in pl["items"]]
    out = []
    for i in range(0, len(ids), 50):
        det = yt.videos().list(part="snippet,status,contentDetails", id=",".join(ids[i:i + 50])).execute()
        for v in det["items"]:
            if v["status"]["privacyStatus"] == "unlisted":
                out.append({
                    "id": v["id"],
                    "title": v["snippet"]["title"],
                    "published": v["snippet"].get("publishedAt", ""),
                    "duration_sec": _iso_dur(v["contentDetails"].get("duration", "")),
                })
    return out


def _iso_dur(iso: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def _srt_to_seconds(ts: str) -> float:
    # "00:01:02,500"
    hh, mm, rest = ts.split(":")
    ss, ms = rest.split(",")
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000.0


def fetch_transcript(video_id: str) -> dict:
    """Sahip yetkisiyle altyazıyı indirir, üst üste binen ASR parçalarını birleştirir,
    ~15 sn'de bir [mm:ss] etiketi ekler. {text, has_captions} döner."""
    yt = service()
    caps = yt.captions().list(part="snippet", videoId=video_id).execute().get("items", [])
    if not caps:
        return {"text": "", "has_captions": False}
    # ASR olmayanı (insan altyazısı) tercih et, yoksa ASR
    pick = sorted(caps, key=lambda i: 0 if i["snippet"].get("trackKind") != "asr" else 1)[0]
    raw = yt.captions().download(id=pick["id"], tfmt="srt").execute()
    srt = raw.decode("utf-8", "ignore") if isinstance(raw, (bytes, bytearray)) else str(raw)
    return {"text": _stitch_srt(srt), "has_captions": True}


def _stitch_srt(srt: str) -> str:
    """YouTube ASR srt'sinde her cue bir sonrakiyle örtüşür (kelimeler yuvarlanır).
    Örtüşmeyi temizleyip [mm:ss] etiketli düz metin üretir."""
    blocks = re.split(r"\n\s*\n", srt.strip())
    cues = []
    for b in blocks:
        lines = [x for x in b.splitlines() if x.strip()]
        if len(lines) < 2 or "-->" not in lines[1]:
            continue
        start = _srt_to_seconds(lines[1].split("-->")[0].strip())
        words = " ".join(lines[2:]).split()
        if words:
            cues.append((start, words))

    running: list[str] = []
    out_parts: list[str] = []
    last_tag = -999.0
    for start, words in cues:
        # running kuyruğu ile cue başının örtüşmesini bul
        max_k = min(len(running), len(words))
        k = 0
        for kk in range(max_k, 0, -1):
            if [w.lower() for w in running[-kk:]] == [w.lower() for w in words[:kk]]:
                k = kk
                break
        new_words = words[k:]
        if not new_words:
            continue
        if start - last_tag >= 15:
            out_parts.append(f"[{int(start // 60):02d}:{int(start % 60):02d}]")
            last_tag = start
        out_parts.append(" ".join(new_words))
        running.extend(new_words)
    return " ".join(out_parts).strip()


def download_video(video_id: str, dest_dir, max_height: int = 720) -> str:
    """yt-dlp ile videoyu indirir (kare çıkarımı için ~720p yeterli). Dosya yolunu döner."""
    import yt_dlp

    os.makedirs(dest_dir, exist_ok=True)
    out_tmpl = os.path.join(str(dest_dir), f"{video_id}.%(ext)s")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "format": f"best[height<={max_height}][ext=mp4]/best[ext=mp4]/best",
        "outtmpl": out_tmpl,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"https://youtu.be/{video_id}", download=True)
        return y.prepare_filename(info)
