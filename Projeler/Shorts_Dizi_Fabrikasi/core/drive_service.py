"""Google Drive yukleme: seri klasoru + resumable bolum upload."""
import logging
import os
from typing import Optional, Tuple

from googleapiclient.http import MediaFileUpload

from core.config import settings
from core.google_auth import get_drive_service

logger = logging.getLogger("DriveService")

ROOT_FOLDER_NAME = os.environ.get("DRIVE_ROOT_FOLDER_NAME", "Shorts Dizi Fabrikasi")
FOLDER_MIMETYPE = "application/vnd.google-apps.folder"


def _folder_url(folder_id: str) -> str:
    return f"https://drive.google.com/drive/folders/{folder_id}"


def _extract_folder_id(folder_url: str) -> Optional[str]:
    folder_id = None
    if "folders/" in folder_url:
        folder_id = folder_url.split("folders/")[1].split("?")[0]
    elif "id=" in folder_url:
        folder_id = folder_url.split("id=")[1].split("&")[0]
    return folder_id


def get_or_create_subfolder(service, parent_id: Optional[str], folder_name: str) -> str:
    """Klasoru bul-ya-da-olustur, Drive ID don. parent_id=None → Drive koku."""
    parent_clause = f"'{parent_id}' in parents and " if parent_id else "'root' in parents and "
    query = (
        f"{parent_clause}name = '{folder_name}' "
        f"and mimeType = '{FOLDER_MIMETYPE}' and trashed = false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    logger.info(f"Drive'da yeni klasor olusturuluyor: {folder_name}")
    metadata = {"name": folder_name, "mimeType": FOLDER_MIMETYPE}
    if parent_id:
        metadata["parents"] = [parent_id]
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder.get("id")


def ensure_series_folder(series_title: str) -> Tuple[Optional[str], Optional[str]]:
    """<kok>/<series_title> klasorunu garanti et → (folder_id, folder_url).

    Kok: DRIVE_FOLDER_URL doluysa o; bossa ROOT_FOLDER_NAME env'i (varsayilan 'Shorts Dizi Fabrikasi').
    DRY_RUN'da (None, None).
    """
    if settings.IS_DRY_RUN:
        logger.info(f"[DRY-RUN] Drive klasoru atlandi: {series_title}")
        return None, None

    service = get_drive_service("outreach")

    root_id = None
    if settings.DRIVE_FOLDER_URL:
        root_id = _extract_folder_id(settings.DRIVE_FOLDER_URL)
        if not root_id:
            raise ValueError(f"DRIVE_FOLDER_URL cozumlenemedi: {settings.DRIVE_FOLDER_URL}")
    else:
        root_id = get_or_create_subfolder(service, None, ROOT_FOLDER_NAME)

    series_id = get_or_create_subfolder(service, root_id, series_title)
    return series_id, _folder_url(series_id)


def upload_file_to_folder(
    file_path: str,
    folder_id: str,
    file_name: str,
    mimetype: str = "video/mp4",
) -> Optional[str]:
    """Dosyayi klasore yukle → fileId. Ayni isim varsa yukleme, mevcut id don (resume)."""
    if settings.IS_DRY_RUN:
        logger.info(f"[DRY-RUN] Drive upload atlandi: {file_name}")
        return None

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Yuklenecek dosya yok: {file_path}")

    service = get_drive_service("outreach")

    safe_name = file_name.replace("'", "\\'")
    query = f"'{folder_id}' in parents and name = '{safe_name}' and trashed = false"
    existing = service.files().list(q=query, fields="files(id, name)").execute().get("files", [])
    if existing:
        logger.info(f"Drive'da zaten var, yukleme atlandi: {file_name}")
        return existing[0]["id"]

    logger.info(f"Drive'a yukleniyor: {file_name}")
    metadata = {"name": file_name, "parents": [folder_id]}
    media = MediaFileUpload(file_path, mimetype=mimetype, resumable=True)
    file = service.files().create(body=metadata, media_body=media, fields="id").execute()
    file_id = file.get("id")
    logger.info(f"Drive upload tamam: {file_name} (id={file_id})")
    return file_id
