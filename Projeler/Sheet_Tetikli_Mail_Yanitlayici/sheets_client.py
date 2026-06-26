"""Sheet okuma + durum sütununa yazma."""
from __future__ import annotations
import os
import sys
from typing import List, Dict, Any

# Self-contained google_auth modülünü import et
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_auth import get_sheets_service  # noqa: E402

from config import SHEET_ID, TAB_NAME, COL, LAST_COL, STATUS_HEADER, SHEETS_ACCOUNT


def _svc():
    return get_sheets_service(SHEETS_ACCOUNT)


def ensure_status_header() -> None:
    """Durum sütununun header hücresi boşsa header yaz. Mevcut başlık varsa dokunma."""
    svc = _svc()
    rng = f"'{TAB_NAME}'!{COL['status']}1"
    res = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=rng).execute()
    current = (res.get("values") or [[""]])[0][0] if res.get("values") else ""
    if not current:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=rng,
            valueInputOption="RAW",
            body={"values": [[STATUS_HEADER]]},
        ).execute()


def fetch_pending_rows() -> List[Dict[str, Any]]:
    """Trigger sütunu TRUE, durum sütunu boş olan satırları döndür.

    Her satır dict: row_index (1-based) + bağlam alanları.
    """
    svc = _svc()
    rng = f"'{TAB_NAME}'!A1:{LAST_COL}"
    res = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=rng,
        valueRenderOption="UNFORMATTED_VALUE",  # checkbox -> bool
    ).execute()
    values = res.get("values", [])
    if not values:
        return []

    pending = []
    for idx, row in enumerate(values[1:], start=2):  # 2. satırdan başla
        def cell(letter: str) -> str:
            i = ord(letter.upper()) - ord("A")
            return row[i] if 0 <= i < len(row) else ""

        trigger = cell(COL["trigger"])
        status = cell(COL["status"])
        # checkbox UNFORMATTED -> True/False (bool) veya "TRUE"/"FALSE" string
        is_triggered = (trigger is True) or (str(trigger).strip().upper() == "TRUE")
        if not is_triggered:
            continue
        if str(status).strip():  # zaten gönderilmiş
            continue

        pending.append({
            "row_index": idx,
            "role": str(cell(COL["role"])).strip(),
            "brand": str(cell(COL["brand"])).strip(),
            "employees": str(cell(COL["employees"])).strip(),
            "phone": str(cell(COL["phone"])).strip(),
            "email": str(cell(COL["email"])).strip(),
            "need": str(cell(COL["need"])).strip(),
            "name": str(cell(COL["name"])).strip(),
            "surname": str(cell(COL["surname"])).strip(),
            "notes": str(cell(COL["notes"])).strip(),
        })
    return pending


def mark_status(row_index: int, status_text: str) -> None:
    """Durum sütununun ilgili satır hücresine durum yaz."""
    svc = _svc()
    rng = f"'{TAB_NAME}'!{COL['status']}{row_index}"
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=rng,
        valueInputOption="RAW",
        body={"values": [[status_text]]},
    ).execute()
