# Paylaşım Notu — Sheet Tetikli Mail Yanıtlayıcı

**Mod:** C (şablona çevrildi)

## Orijinal amaç → yeni jenerik çerçeve

Orijinal proje, belirli bir kişiye ait bir lead Sheet'inde bir checkbox
işaretlenince, belirli bir ekip üyesinin adına ve belirli bir topluluğun
bağlamıyla mail atan bir bottu. Yeni çerçeve: **herhangi bir Google Sheet'te
işaretlenen satıra otomatik kişiselleştirilmiş mail atan jenerik bot.** Çekirdek
desen (sheet polling + trigger checkbox + LLM mail + idempotent durum sütunu)
aynen korundu.

## Yapılan temizlik

### Kişisel veri scrub
- Kişiye özel ekip üyesi adı, sahibin adı ve marka adı referansları tüm kod ve
  prompt'lardan çıkarıldı
- Kişiye özel gönderici e-posta adresi → `SENDER_EMAIL` env var'ı, jenerik placeholder
- Kişiye özel gönderici imzası → `SENDER_NAME` env var'ı
- LLM SYSTEM_PROMPT'u kişiye/topluluğa özel bağlamdan tamamen arındırıldı,
  jenerik "ekip adına mail yazan asistan" haline getirildi; mailin amacı artık
  `MAIL_PURPOSE` env var'ı ile özelleştiriliyor

### Sırlar
- Koda gömülü sır bulunmadı (sırlar `.env` / token JSON'larında, kopyalanmadı)

### Owner-specific schema bindings → env/config
- `ECE_SHEET_ID` (gerçek Google Sheet id'si hardcoded fallback'iyle) → `SHEET_ID`
  env var'ı, `<GOOGLE_SHEET_ID>` placeholder
- `ECE_TAB_NAME` (kişiye özel sekme adı) → `TAB_NAME` env var'ı, `Sheet1` default
- Sahibe özel sabit sütun haritası (A-M, Türkçe form alan adları) → her sütun
  ayrı env var'ından okunuyor (`TRIGGER_COL`, `STATUS_COL`, `EMAIL_COL` vb.)
- Sahibin merkezi `_knowledge/credentials/oauth/google_auth.py` modülüne bağımlılık
  → projeye özel, self-contained `google_auth.py` yazıldı (env-driven OAuth)
- Hardcoded hesap profilleri (`"ece"`, `"outreach"`) → `gmail` / `sheets` jenerik
  profilleri, `GMAIL_ACCOUNT` / `SHEETS_ACCOUNT` env var'larıyla override edilebilir

## Öğrenci ne yapmalı

1. `.env.example` → `.env` kopyala, doldur:
   - `GMAIL_TOKEN_JSON` + `SHEETS_TOKEN_JSON` — Google OAuth token'ları
     (kendi OAuth akışınla üret; aynı hesabı kullanacaksan ikisine de aynı token)
   - `SHEET_ID` + `TAB_NAME` — kendi Google Sheet'in
   - `TRIGGER_COL` / `STATUS_COL` / `EMAIL_COL` ve diğer sütun harfleri — kendi
     Sheet'inin sütun düzenine göre ayarla
   - `MAIL_PURPOSE` — bot'un attığı mailin amacını tek cümleyle yaz
   - `SENDER_EMAIL` / `SENDER_NAME` — gönderici kimliği
   - `OPENAI_API_KEY` — mail kişiselleştirmesi için (opsiyonel; boşsa şablon kullanılır)
2. **Mail içeriği:** `mail_writer.py` içindeki `SYSTEM_PROMPT` ve `_template_fallback`'i
   kendi senaryona göre düzenle (ton, amaç, fallback metin).
3. Google Sheet'inde `TRIGGER_COL` bir checkbox sütunu, `STATUS_COL` boş bir
   metin sütunu olsun.
4. Railway'de Cron Job olarak deploy et (`*/5 * * * *` gibi).
