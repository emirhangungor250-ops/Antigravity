"""Google Drive üzerinden Docs üretimi.

Strateji: Docs API'sı ÇAĞIRMIYORUZ — HTML metnini Drive API'ye `application/vnd.google-apps.document`
mime type'ı ile yükleyince Drive bunu otomatik olarak Google Docs'a çevirir. Bu yol:
  - Mevcut drive.file scope'u yeterli (Docs scope reauth gerektirmez)
  - Tek API çağrısı yeterli (create + content tek seferde)
  - Docs API yerine HTML upload + Drive auto-convert kullanılır; pattern temiz kalır
"""

import io
import re
from googleapiclient.http import MediaIoBaseUpload

from core.google_auth import get_drive_service


def extract_folder_id(folder_url: str) -> str | None:
    if not folder_url:
        return None
    if "folders/" in folder_url:
        return folder_url.split("folders/")[1].split("?")[0].split("/")[0]
    if "id=" in folder_url:
        return folder_url.split("id=")[1].split("&")[0]
    return None


def find_existing_draft(folder_id: str, name_contains: str = "Aciklama_Taslagi") -> str | None:
    """Klasörde 'Aciklama_Taslagi' içeren bir Docs varsa link döndür (idempotency)."""
    service = get_drive_service()
    query = (
        f"'{folder_id}' in parents "
        f"and name contains '{name_contains}' "
        f"and mimeType = 'application/vnd.google-apps.document' "
        f"and trashed = false"
    )
    res = service.files().list(q=query, fields="files(id, name, webViewLink)", pageSize=5).execute()
    files = res.get("files", [])
    if files:
        return files[0].get("webViewLink") or f"https://docs.google.com/document/d/{files[0]['id']}"
    return None


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def _linkify(text: str) -> str:
    """Düz metindeki URL'leri <a> tag'ine çevir (escape sonrası)."""
    pattern = re.compile(r"(https?://[^\s<]+)")
    return pattern.sub(r'<a href="\1">\1</a>', text)


def build_html(title: str, description_text: str) -> str:
    """Açıklama metnini Google Docs'a uygun basit HTML'e çevir."""
    safe_title = _escape_html(title)
    paragraphs = []
    for raw_line in description_text.split("\n"):
        line = raw_line.rstrip()
        if not line:
            paragraphs.append("<p>&nbsp;</p>")
            continue
        escaped = _escape_html(line)
        linked = _linkify(escaped)
        paragraphs.append(f"<p>{linked}</p>")
    body = "\n".join(paragraphs)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{safe_title}</title></head>
<body><h1>{safe_title}</h1>
{body}
</body></html>"""


def create_doc_in_folder(folder_id: str, doc_name: str, html_content: str) -> dict:
    """HTML'i Drive'a yükle, Drive otomatik Google Doc'a çevirsin.

    Returns: {"id": str, "webViewLink": str, "name": str}
    """
    service = get_drive_service()
    media = MediaIoBaseUpload(
        io.BytesIO(html_content.encode("utf-8")),
        mimetype="text/html",
        resumable=False,
    )
    file_metadata = {
        "name": doc_name,
        "mimeType": "application/vnd.google-apps.document",
        "parents": [folder_id],
    }
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, webViewLink",
    ).execute()
    return file
