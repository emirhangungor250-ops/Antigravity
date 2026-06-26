# Paylaşım Notu — IG_Carousel_Cron

**Mod:** A (doğrudan ver)

## Ne yapıldı
- **Temizlenen sırlar:** Koda gömülü sır bulunmadı (tüm anahtarlar zaten env üzerinden okunuyor).
- **Scrub edilen kişisel veriler:**
  - `core/mail_sender.py` — hardcoded kişisel RECIPIENT/SENDER e-posta adresi → env var (`APPROVAL_RECIPIENT_EMAIL`, `APPROVAL_SENDER_EMAIL`)
  - `core/style.py` — `BRAND_MARK_TEXT` içindeki kişisel marka handle'ı → env var (`BRAND_MARK_TEXT`), default `@yourbrand`
  - `style/carousel_style_guide.md` — kişisel marka handle referansı → `@yourbrand`
  - `ops_logger.py` — hardcoded Notion Ops Log DB ID default kaldırıldı (artık boş, env'den okunur)
- **Kopyalanmayanlar:** `outputs/` (üretilmiş slide görselleri + smoke logları), `.DS_Store`.

## Öğrenci ne yapmalı
1. `.env.example` dosyasını `.env` olarak kopyala ve doldur:
   - `NOTION_SOCIAL_TOKEN`, `NOTION_X_DB_ID` — Notion entegrasyonu + draft DB
   - `KIE_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY` (veya `OPENAI_API_KEY`)
   - `IMGBB_API_KEY` — görsel CDN
   - `APPROVAL_BASE_URL`, `APPROVAL_SECRET` — Twitter_Onay_Api ile aynı secret
2. Marka mark'ını ayarla: `.env` içine `BRAND_MARK_TEXT=@kendimarkan`.
3. Onay maili adreslerini ayarla: `APPROVAL_RECIPIENT_EMAIL`, `APPROVAL_SENDER_EMAIL`.
4. `requirements.txt` ile bağımlılıkları kur, `python main.py` ile çalıştır.
