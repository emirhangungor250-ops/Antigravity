"""Sheet Tetikli Mail Yanıtlayıcı — konfigürasyon.

Tüm Sheet'e özgü bağlamalar (sheet id, sekme adı, sütun haritası) env var'larından
okunur. Kendi Google Sheet'inin yapısına göre .env dosyasını düzenle.
"""
import os

# ── Google Sheet ──
SHEET_ID = os.environ.get("SHEET_ID", "<GOOGLE_SHEET_ID>")
TAB_NAME = os.environ.get("TAB_NAME", "Sheet1")

# ── Sütun haritası (1-indexed Sheet sütun harfleri) ──
# Header satırı 1, veri satırları 2'den başlar.
# Kendi Sheet'inin sütun düzenine göre .env'de override et.
#   TRIGGER_COL   → işaretlendiğinde mail tetikleyen checkbox sütunu
#   STATUS_COL    → bu otomasyonun "gönderildi" durumunu yazdığı sütun
#   EMAIL_COL     → alıcının e-posta adresi
#   NAME_COL / SURNAME_COL / BRAND_COL / ROLE_COL / NEED_COL / NOTES_COL
#     → mail kişiselleştirmesi için bağlam sütunları (opsiyonel)
COL = {
    "role": os.environ.get("ROLE_COL", "A"),
    "brand": os.environ.get("BRAND_COL", "B"),
    "employees": os.environ.get("EMPLOYEES_COL", "C"),
    "phone": os.environ.get("PHONE_COL", "D"),
    "email": os.environ.get("EMAIL_COL", "E"),
    "need": os.environ.get("NEED_COL", "F"),
    "name": os.environ.get("NAME_COL", "G"),
    "surname": os.environ.get("SURNAME_COL", "H"),
    "notes": os.environ.get("NOTES_COL", "J"),
    "trigger": os.environ.get("TRIGGER_COL", "K"),   # checkbox — işaretlenince mail tetiklenir
    "status": os.environ.get("STATUS_COL", "M"),     # bu otomasyonun yazdığı durum sütunu
}

# Veri çekilecek sütun aralığının son harfi (A'dan buraya kadar okunur)
LAST_COL = os.environ.get("LAST_COL", "M")

STATUS_HEADER = os.environ.get("STATUS_HEADER", "Mail Durumu")

# ── OpenAI ──
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

# ── Google hesap profilleri (google_auth.py) ──
GMAIL_ACCOUNT = os.environ.get("GMAIL_ACCOUNT", "gmail")
SHEETS_ACCOUNT = os.environ.get("SHEETS_ACCOUNT", "sheets")

# ── Davranış ──
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
POLL_ONCE = os.environ.get("POLL_ONCE", "1") == "1"  # cron modunda True
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))

# ── Gönderici kimliği ──
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "sender@example.com")
SENDER_NAME = os.environ.get("SENDER_NAME", "Ekip")
