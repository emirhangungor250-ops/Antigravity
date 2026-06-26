# Paylaşım Notu — Lead_Notifier_Bot

**Mod:** A (doğrudan ver)

## Ne yapıldı
- **Temizlenen sırlar:**
  - Gerçek Railway API token, project/env/service ID'leri ve gerçek Telegram bot token'ı içeren operasyonel yardımcı betikler **tamamen çıkarıldı**: `deploy_railway.py`, `delete_vars.py`, `get_railway_logs.py`, `get_service_info.py`. Bunlar botun çalışması için gerekli değil, sahibe özel tek seferlik deploy araçlarıydı.
  - `credentials.json` ve `.seen_lead_ids.json` kopyalanmadı.
- **Scrub edilen kişisel veriler:**
  - `config.py` — hardcoded Google Sheet ID + kişisel bildirim/gönderici e-posta defaultları → placeholder (`<GOOGLE_SHEET_ID>`, `<NOTIFY_EMAIL>`, `<SENDER_EMAIL>`)
  - `main.py` — docstring'deki kişi adı → "ilgili kişiye"
  - `share_sheet.py` — hardcoded mutlak yol, Sheet ID ve servis hesabı e-postası → env var (`SPREADSHEET_ID`, `SERVICE_ACCOUNT_EMAIL`, `GOOGLE_OAUTH_HELPER_PATH`); betik baştan env-driven yazıldı
  - `README.md` — Sheet tab adı, e-posta defaultları, kişisel GitHub repo URL'i, kişi adı jenerikleştirildi; dosya yapısı güncellendi
- **Yeni:** `.env.example` üretildi (proje önceden yoktu, kod 11 env var okuyor).

## Öğrenci ne yapmalı
1. `.env.example` → `.env` kopyala ve doldur:
   - `SPREADSHEET_ID`, `SHEET_TAB` — izlenecek Google Sheet
   - `TELEGRAM_BOT_TOKEN` (@BotFather), `TELEGRAM_CHAT_ID`
   - `NOTIFY_EMAIL`, `SENDER_EMAIL`
   - `GOOGLE_SERVICE_ACCOUNT_JSON` — kendi servis hesabı JSON'u
   - `GOOGLE_OUTREACH_TOKEN_JSON` — e-posta gönderimi için Gmail OAuth token
2. Sheet'i servis hesabıyla paylaş: `SERVICE_ACCOUNT_EMAIL` ortam değişkenini set edip `python share_sheet.py` çalıştır (veya Sheet'i manuel paylaş).
3. `pip install -r requirements.txt` → `python main.py` (test için `python main.py --once`).
