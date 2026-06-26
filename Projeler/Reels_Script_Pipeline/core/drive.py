"""Google Drive + Docs entegrasyonu.

Her reels için parent klasör altında yeni alt-klasör + içine "Brief — <title>" Doc'u açar.
Doc'a editör için asset havuzu yazılır (gerçek YouTube URL'leri + duration check'ten geçmiş).
Anyone-with-link reader izniyle paylaşır. Klasör URL'i Notion "Drive" property'sine yazılır.
"""

from __future__ import annotations

import io
import os
import re
import sys
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from core.config import Config

_OAUTH_DIR = Path(__file__).resolve().parents[3] / "_knowledge" / "credentials" / "oauth"
if str(_OAUTH_DIR) not in sys.path:
    sys.path.insert(0, str(_OAUTH_DIR))

from google_auth import _get_credentials  # type: ignore

DRIVE_ACCOUNT = os.getenv("REELS_DRIVE_OAUTH_ACCOUNT", "outreach")


def _creds():
    """Pipeline <KULLANICI_ADI>'ın kişisel OAuth token'ını (drive.file scope) kullanır.
    Servis hesabı kişisel Drive'a yazamadığı için bu yol seçildi."""
    return _get_credentials(DRIVE_ACCOUNT)


def _drive():
    return build("drive", "v3", credentials=_creds(), cache_discovery=False)


def _slug(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^\w\s\-çğıöşüÇĞİÖŞÜ]", "", text or "", flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:max_len] or "brief"


def create_brief_folder(
    cfg: Config,
    *,
    title: str,
    assets: dict,
    source_reels_url: str,
    script_text: str | None = None,
    source_channel: str | None = None,
) -> dict[str, str]:
    """Parent altında yeni klasör + brief Doc oluştur, ikisini de anyone-with-link reader yap.

    Döndürür: {"folder_id", "folder_url", "doc_id", "doc_url"}
    """
    parent_id = cfg.google_drive_reels_parent_folder_id
    folder_name = _slug(title)

    drive = _drive()
    folder = drive.files().create(
        body={
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        },
        fields="id,webViewLink",
        supportsAllDrives=True,
    ).execute()
    folder_id = folder["id"]

    doc_html = _build_brief_html(
        title=title,
        assets=assets,
        source_reels_url=source_reels_url,
    )
    media = MediaIoBaseUpload(
        io.BytesIO(doc_html.encode("utf-8")),
        mimetype="text/html",
        resumable=False,
    )
    doc = drive.files().create(
        body={
            "name": f"Brief — {folder_name}",
            "mimeType": "application/vnd.google-apps.document",
            "parents": [folder_id],
        },
        media_body=media,
        fields="id,webViewLink",
        supportsAllDrives=True,
    ).execute()
    doc_id = doc["id"]

    _share_anyone_reader(drive, folder_id)
    _share_anyone_reader(drive, doc_id)

    return {
        "folder_id": folder_id,
        "folder_url": f"https://drive.google.com/drive/folders/{folder_id}",
        "doc_id": doc_id,
        "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
    }


def _share_anyone_reader(drive, file_id: str) -> None:
    drive.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
        supportsAllDrives=True,
    ).execute()


def _esc(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _build_brief_html(*, title: str, assets: dict, source_reels_url: str) -> str:
    """Brief Doc'unun HTML içeriği. Drive otomatik Google Doc'a çevirir.
    <h1> başlığı görünür/büyük yapar. Maddeler arası boş paragrafla ayrılır."""
    parts: list[str] = ["<html><body>"]
    parts.append(f"<h1>{_esc(title)}</h1>")
    parts.append(
        f'<p><mark>Kaynak reels: <a href="{_esc(source_reels_url)}">{_esc(source_reels_url)}</a></mark></p>'
    )
    parts.append("<p>&nbsp;</p>")
    items = assets.get("assets", [])
    for i, a in enumerate(items):
        desc = _esc(a.get("aciklama", ""))
        url = a.get("url") or ""
        if url:
            parts.append(
                f'<p>• {desc}<br><a href="{_esc(url)}">{_esc(url)}</a></p>'
            )
        else:
            parts.append(f"<p>• {desc}</p>")
        if i < len(items) - 1:
            parts.append("<p>&nbsp;</p>")
    parts.append("</body></html>")
    return "".join(parts)
