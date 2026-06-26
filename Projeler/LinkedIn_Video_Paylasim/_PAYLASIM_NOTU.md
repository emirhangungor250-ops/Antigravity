# Paylaşım Notu — LinkedIn_Video_Paylasim

**Mod:** A (doğrudan ver)

## Ne yapıldı
- **Temizlenen sırlar:** Koda gömülü gerçek anahtar bulunmadı (config env-driven).
  - `ops_logger.py` — hardcoded Notion Ops Log DB ID defaultu kaldırıldı.
  - `.railway/project.json` (hardcoded Railway proje/servis ID'leri) kopyalanmadı.
- **Scrub edilen kişisel veriler:**
  - `core/content_filter.py` — LLM prompt'larındaki kişiye özel içerik üretici profili → env var `CREATOR_PROFILE` (jenerik default)
  - `core/notion_video_selector.py` + `README.md` — kişiye özel Notion DB adı → "Reels & YouTube"
- **Yeni:** `.env.example` üretildi (proje önceden yoktu).

## Öğrenci ne yapmalı
1. `.env.example` → `.env` kopyala ve doldur:
   - `TYPEFULLY_API_KEY`, `TYPEFULLY_LINKEDIN_SOCIAL_SET_ID`
   - `GROQ_API_KEY` — uygunluk filtresi + caption üretimi
   - `NOTION_SOCIAL_TOKEN`, `NOTION_DB_REELS_KAPAK`, `NOTION_LINKEDIN_DB_ID`
   - `GOOGLE_SERVICE_ACCOUNT_JSON` — Drive'dan video indirme
2. **`CREATOR_PROFILE`** — kendi içerik nişini ve hedef kitleni yaz. LLM caption üretimi ve uygunluk filtresi bu profile göre çalışır. Örnek değer `.env.example`'da.
3. `ffmpeg` kurulu olmalı (video re-encode için). `pip install -r requirements.txt` → `python main.py`.
