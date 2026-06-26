"""Kapak köprüsü.

Kapak motoru (bu paketteki Otonom_Kapak_Uretici) videoyu YouTube'dan çekemez ve drive.file izni
insan-yüklediği dosyaları okuyamaz. Çözüm: videoyu YouTube'dan indir, Drive klasörüne
app-sahipli yükle (artık motor okuyabilir), sonra motoru YouTube modunda tetikle.
"""
import json
import os
import re

from config import KAPAK_DIR, OUTREACH_TOKEN_ENV, OUTREACH_TOKEN_FILE
from core import youtube_owner


def _drive_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    raw = os.getenv(OUTREACH_TOKEN_ENV)
    d = json.loads(raw) if raw else json.loads(OUTREACH_TOKEN_FILE.read_text(encoding="utf-8"))
    c = Credentials(token=d.get("token"), refresh_token=d.get("refresh_token"),
                    token_uri=d.get("token_uri"), client_id=d.get("client_id"),
                    client_secret=d.get("client_secret"), scopes=d.get("scopes"))
    c.refresh(Request())
    return build("drive", "v3", credentials=c, cache_discovery=False)


def _folder_id(url: str):
    m = re.search(r"folders/([A-Za-z0-9_-]+)", url or "") or re.search(r"[?&]id=([A-Za-z0-9_-]+)", url or "")
    return m.group(1) if m else None


def ensure_video_in_drive(video_id: str, title: str, drive_folder_url: str, work_dir) -> dict:
    """Videoyu indirip Drive klasörüne app-sahipli yükler (motorun okuyabilmesi için).
    Aynı video zaten app tarafından yüklenmişse tekrar yüklemez."""
    folder = _folder_id(drive_folder_url)
    if not folder:
        raise ValueError("Drive klasör id çözülemedi: " + str(drive_folder_url))
    svc = _drive_service()
    # zaten app-yüklemiş mi? (drive.file sadece app dosyalarını görür)
    existing = svc.files().list(
        q=f"'{folder}' in parents and trashed=false and name contains '[{video_id}]'",
        fields="files(id,name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute().get("files", [])
    if existing:
        return {"drive_file_id": existing[0]["id"], "reused": True}

    path = youtube_owner.download_video(video_id, work_dir)
    from googleapiclient.http import MediaFileUpload
    safe = re.sub(r"[^\w ]", "", title)[:60].strip() or video_id
    meta = {"name": f"{safe} [{video_id}].mp4", "parents": [folder]}
    media = MediaFileUpload(path, mimetype="video/mp4", resumable=True)
    f = svc.files().create(body=meta, media_body=media, fields="id,name", supportsAllDrives=True).execute()
    return {"drive_file_id": f["id"], "reused": False, "local_path": path}


def already_done(drive_folder_url: str) -> bool:
    """Kalıcı dedup = Drive'ın kendisi (Railway efemera disk). Klasörde hem açıklama
    dökümanı hem yatay (16:9) kapak varsa bu video zaten işlenmiş demektir."""
    fid = _folder_id(drive_folder_url)
    if not fid:
        return False
    svc = _drive_service()
    items = svc.files().list(
        q=f"'{fid}' in parents and trashed=false", fields="files(id,name,mimeType)",
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute().get("files", [])
    has_desc = any("Aciklama_Taslagi" in f["name"] for f in items)
    thumb = next((f for f in items if f["mimeType"].endswith("folder") and f["name"] == "THUMBNAIL"), None)
    has_cover = False
    if thumb:
        imgs = svc.files().list(
            q=f"'{thumb['id']}' in parents and trashed=false",
            fields="files(imageMediaMetadata(width,height))", supportsAllDrives=True).execute().get("files", [])
        has_cover = any((i.get("imageMediaMetadata", {}).get("width", 0) or 0)
                        > (i.get("imageMediaMetadata", {}).get("height", 1) or 1) for i in imgs)
    return has_desc and has_cover


def trigger_cover_engine() -> dict:
    """Kapak motorunu YouTube modunda çalıştırır. Drive dedup sayesinde sadece kapağı
    olmayan videoları işler (idempotent)."""
    import subprocess
    import sys
    proc = subprocess.run([sys.executable, "main.py", "--type", "youtube"],
                          cwd=str(KAPAK_DIR), capture_output=True, text=True, timeout=1800)
    return {"ok": proc.returncode == 0, "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
