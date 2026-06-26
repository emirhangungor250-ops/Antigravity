# Paylaşım Notu — Teleprompter_Senkron

**Mod:** B (knowledge/içerik öğrenci koyar)

## Ne yapıldı

- **Temizlenen sırlar:** Kodda gömülü gerçek API anahtarı yoktu. `.env.example`'daki gerçekçi görünen sahte değerler (`ntn_xxx`, `sk-xxx`, `sk-ant-xxx`) açık `<...>` placeholder formatına çevrildi.
- **Hardcoded ID'ler env'e taşındı (sızıntı kapatıldı):**
  - Notion script DB ID'si (`27b9...d532a2`) koddan ve `.env.example`'dan kaldırıldı → `PROMPTER_NOTION_DB_ID=<NOTION_DB_ID>`, kod placeholder default ile okur.
  - Google Drive klasör ID'si (`1YBAl...PG_`) kaldırıldı → `PROMPTER_DRIVE_FOLDER_ID=<GOOGLE_DRIVE_FOLDER_ID>`.
- **Scrub edilen kişisel veriler:**
  - Sahibin adı, e-posta adresi ve domain'i tüm dosyalardan (sync.py, core/*.py, README, RUNBOOK, .env.example) kaldırıldı.
  - Sahibin Notion DB adı jenerik "script DB" olarak değiştirildi.
  - "Nano Teleprompter" tek bir yerde "teleprompter uygulaması (ör. Nano Teleprompter)" olarak yumuşatıldı; davranış deseni korundu.
  - Sahibe özel mutlak yollar (`_knowledge/credentials/oauth/...`, monorepo `master.env` yolu, `parents[3]`/`parents[2]` ile monorepo köküne çıkan referanslar) kaldırıldı; tüm yollar artık proje köküne göre dinamik (`Path(__file__)...parents[1]`).
  - Sahibe özel önekli env adları → jenerik `GOOGLE_DRIVE_TOKEN_JSON` ve tek `OPENAI_API_KEY`.
  - Sahibe özel hesap güvenlik kapısı (hardcoded bir domain kontrolü) → opsiyonel `EXPECTED_DRIVE_DOMAIN` env'i; varsayılan boş (kapı kapalı). Güvenlik deseni korundu, kişisel domain çıkarıldı.
  - GitHub Actions workflow dosyası (sahibin secret'larına bağlı) pakete alınmadı; yerine README'ye placeholder secret adlı jenerik `.github/workflows/sync.yml` örneği konuldu.
- **Model seçimi jenerikleştirildi:** Sahibe özel `gpt-5.4` + `claude-sonnet-4-6` model ID'leri env-driven ucuz varsayılanlara çekildi (`OPENAI_MODEL` / `ANTHROPIC_MODEL`; default `gpt-4o-mini` / `claude-3-5-haiku-latest`). Script → prompter dönüşüm deseni (AI temizleme + OpenAI→Claude fallback) aynen korundu.
- **Eksik bağımlılık eklendi:** `reauth_drive_full.py`'ın kullandığı `google-auth-oauthlib==1.2.1` requirements'a eklendi (kaynakta eksikti).
- **OAuth yeniden üretim akışı jenerikleştirildi:** `reauth_drive_full.py` artık sahibin paylaşılan gmail token'ından değil, standart Google Cloud Console "Desktop app" OAuth client (`client_secret.json`) dosyasından okur; token'ı proje köküne yazar.
- `.gitignore`'a `client_secret.json`, `drive-full-token.json`, `*token*.json` eklendi (öğrenci yanlışlıkla commit etmesin).

## Öğrenci ne yapmalı

1. `.env.example`'ı `.env` olarak kopyala ve doldur:
   - `NOTION_REELS_TOKEN` — Notion integration token (https://www.notion.so/my-integrations); DB'ni bu integration ile paylaş.
   - `PROMPTER_NOTION_DB_ID` — kendi script DB'nin ID'si.
   - `PROMPTER_DRIVE_FOLDER_ID` — teleprompter uygulamasının Drive'da açtığı klasörün ID'si.
   - `OPENAI_API_KEY` ve/veya `ANTHROPIC_API_KEY`.
   - (Opsiyonel) `NOTION_STATUS_PROPERTY` / `NOTION_STATUS_READY` — Notion DB şeman farklıysa kendi durum property adın ve "hazır" değerin.
   - (Opsiyonel) `EXPECTED_DRIVE_DOMAIN` — yanlış Google hesabına yazmayı önleyen güvenlik kapısı.
2. Google Drive OAuth token'ı üret: Google Cloud Console'da Drive API'yi aç, Desktop app OAuth client ID indir → proje köküne `client_secret.json` koy → `python core/reauth_drive_full.py` çalıştır. Üretilen `drive-full-token.json` içeriğini sunucuda `GOOGLE_DRIVE_TOKEN_JSON` secret'ı olarak ver.
3. **Kendi içeriğine göre değiştirilecek dosya — `core/cleaner.py`:** İçindeki `SYSTEM` prompt'u "neyi koru / neyi çıkar" kurallarını senin script formatına göre tanımlar. Kendi script'lerinde kullandığın etiketler, platform kapanışları, çekimle ilgisi olmayan bölümler (DM/dağıtım/revizyon panelleri) varsa bu prompt'taki KORU/ÇIKAR listelerini kendine göre uyarla. Mantık aynı kalır; sadece örnek bölüm adları senin formatına göre değişir.
4. Cron'u kur: GitHub Actions için README'deki `.github/workflows/sync.yml` örneğini ekle ve secret'ları doldur; ya da `railway.json` ile kendi Railway hesabına deploy et.
