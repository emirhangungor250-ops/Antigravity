"""Google Sheet'i servis hesabıyla paylaşmak için tek seferlik yardımcı betik.

Servis hesabı (GOOGLE_SERVICE_ACCOUNT_JSON) ile Sheets okuyabilmek için,
ilgili Sheet'in servis hesabının e-postasıyla paylaşılması gerekir.
Bu betik bunu otomatikleştirir.

Gerekli env değişkenleri:
  SPREADSHEET_ID                 — paylaşılacak Google Sheet ID'si
  SERVICE_ACCOUNT_EMAIL          — servis hesabının e-postası (...iam.gserviceaccount.com)
  GOOGLE_OAUTH_HELPER_PATH       — google_auth yardımcı modülünün bulunduğu klasör (opsiyonel)
"""
import os
import sys

helper_path = os.environ.get("GOOGLE_OAUTH_HELPER_PATH")
if helper_path:
    sys.path.insert(0, helper_path)

from google_auth import get_drive_service

try:
    drive_service = get_drive_service("outreach")

    file_id = os.environ.get("SPREADSHEET_ID", "<GOOGLE_SHEET_ID>")
    user_permission = {
        "type": "user",
        "role": "writer",
        "emailAddress": os.environ.get(
            "SERVICE_ACCOUNT_EMAIL", "<SERVICE_ACCOUNT_EMAIL>"
        ),
    }

    command = drive_service.permissions().create(
        fileId=file_id,
        body=user_permission,
        fields="id",
    )
    res = command.execute()
    print("Permission ID:", res.get("id"))
    print("Sheet shared successfully!")
except Exception as e:
    print("Failed to share:", str(e))
