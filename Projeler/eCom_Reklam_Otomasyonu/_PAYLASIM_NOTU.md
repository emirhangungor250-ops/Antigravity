# Paylasim Notu — eCom_Reklam_Otomasyonu

## Mod
A — Dogrudan ver.

## Ne yapildi
- Gercek `.env`, `.venv*`, `__pycache__`, `.pytest_cache`, tum `*.log` dosyalari, `e2e_result_*.json`, uretilmis log/JSON dosyalari (`deps.txt`, `deployment_logs.json`, `notion_logs.json`, `recent_logs.txt`, `latest_logs.txt`), `.deploy_trigger`, `REDEPLOY`, derlenmis `bin/railway` ikilisi KOPYALANMADI.
- Sir + kisisel veri scrub'lari:
  - `config.py` — `UPLOAD_POST_PROFILE` default'u → `<UPLOAD_POST_PROFILE>`; sabit kodlanmis Notion chat DB ID'si env'e tasindi
  - `services/elevenlabs_service.py` — kisisel ses clone girisi (`"Dolunay"` voice ID) kaldirildi, yorum sablonu birakildi
  - `services/upload_post_service.py` — `DEFAULT_PROFILE` placeholder'a
  - `core/scenario_engine.py`, `core/production_pipeline.py`, `utils/text_normalizer.py`, `utils/error_messages.py` — kod yorumlari ve string'lerdeki "Dolunay" referanslari jeneriklestirildi
  - `test_message.py`, `test_lock_init.py`, `services/test_upload_post_service.py` — test verisindeki kisisel chat ID ve profil adi placeholder'a
  - Operasyonel scriptler (`fetch_*.py`, `railway_*.py`, `check_*.py`, `sync_eleven_key.py`, `test_groq.py`, `test_elevenlabs.py`) — sabit kodlanmis kisisel mutlak `master.env` yollari `.env`'e cevrildi
  - `README.md` — kisisel Telegram chat ID + Notion DB ID + `master.env` referanslari temizlendi
  - `.env.example` — tum placeholder'lar standart `<...>` formatina cevrildi
- `assets/demo/` icindeki 3 referans urun gorseli (demo girdi sablonu) korundu.

## Ogrenci ne yapmali
`.env.example` → `.env` kopyalayip doldurun:
- `TELEGRAM_ECOM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID` — Telegram bot + kendi chat ID'niz
- `OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `IMGBB_API_KEY`, `KIE_API_KEY`, `ELEVENLABS_API_KEY`, `REPLICATE_API_TOKEN`, `FIRECRAWL_API_KEY` — servis anahtarlari
- `NOTION_SOCIAL_TOKEN`, `NOTION_DB_ECOM_REKLAM`, `NOTION_CHAT_DB_ID` — Notion entegrasyonu
- `UPLOAD_POST_API_KEY`, `UPLOAD_POST_PROFILE` — Upload-Post hesabi ve profil adiniz
İsterseniz `services/elevenlabs_service.py` icindeki yorum sablonuna kendi kisisel ses clone'unuzu ekleyebilirsiniz.
