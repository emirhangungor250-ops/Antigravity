"""Teleprompter klasörüyle çalışma — "bir kez bırak" modeli.

ÖNEMLİ — teleprompter uygulamasının (ör. Nano Teleprompter) klasör davranışı:
  - Uygulama klasörü İKİ YÖNLÜ senkronlar ve sahiplenir.
  - Bıraktığımız .txt dosyalarını **Google Docs'a çevirir** (.txt uzantısı düşer).
  - Drive'dan sildiğimiz dosyayı **geri getirir** (uygulamadaki kopyayı tekrar yazar).
Sonuç: klasörü biz yönetemeyiz. Tek güvenli iş = yeni script'i bir kez BIRAKMAK.
Eşleme dosya ADINA göre yapılır (Doc da olsa), böyle mükerrer önlenir.
"""
from __future__ import annotations

import io

from googleapiclient.http import MediaIoBaseUpload

PLAIN = "text/plain"
FOLDER_MIME = "application/vnd.google-apps.folder"


def list_files(service, folder_id: str) -> list[dict]:
    """Klasördeki TÜM dosyalar (Docs dahil; alt klasör hariç): [{'id','name','mime'}]."""
    out: list[dict] = []
    cursor = None
    while True:
        resp = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id,name,mimeType)",
            pageToken=cursor,
            pageSize=100,
        ).execute()
        for f in resp.get("files", []):
            if f.get("mimeType") != FOLDER_MIME:
                out.append({"id": f["id"], "name": f["name"], "mime": f.get("mimeType", "")})
        cursor = resp.get("nextPageToken")
        if not cursor:
            break
    return out


def _media(content: str) -> MediaIoBaseUpload:
    return MediaIoBaseUpload(io.BytesIO(content.encode("utf-8")), mimetype=PLAIN, resumable=False)


def create_file(service, folder_id: str, name: str, content: str) -> str:
    """Yeni .txt bırak. Nano bunu içe alıp Google Doc'a çevirecek."""
    f = service.files().create(
        body={"name": name, "mimeType": PLAIN, "parents": [folder_id]},
        media_body=_media(content),
        fields="id",
    ).execute()
    return f["id"]


def trash_file(service, file_id: str) -> None:
    service.files().update(fileId=file_id, body={"trashed": True}).execute()
