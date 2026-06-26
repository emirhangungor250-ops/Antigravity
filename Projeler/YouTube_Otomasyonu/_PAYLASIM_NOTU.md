# Paylasim Notu — YT_Otomasyonu

## Mod
A — Dogrudan ver.

## Ne yapildi
- `youtube_credentials.json` ve `youtube_token.json` (OAuth credential + token) KOPYALANMADI.
- `.venv/`, `.DS_Store`, `__pycache__` kopyalanmadi.
- Kisisel veri scrub'lari:
  - `setup_youtube.py` — sabit kodlanmis kisisel mutlak `master.env` yolu kaldirildi; client ID/secret artik proje koku `.env` dosyasindan okunuyor
- `config.py` zaten tamamen env-driven idi, degisiklik gerekmedi (Replicate model surum hash'i public, korundu).
- Yeni `.env.example` uretildi (proje hic yoktu).

## Ogrenci ne yapmali
1. `.env.example` → `.env` kopyalayip doldurun:
   - `OPENAI_API_KEY`, `KIE_API_KEY`, `REPLICATE_API_TOKEN` — AI servis anahtarlari
   - `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` — Google Cloud Console'dan OAuth client
   - `NOTION_SOCIAL_TOKEN`, `NOTION_DB_YOUTUBE_OTOMASYON` — opsiyonel log takibi
2. `python setup_youtube.py` calistirip YouTube kanalinizi baglayin (token uretilir).
3. Uretilen `YOUTUBE_REFRESH_TOKEN`'i `.env`'e ekleyin.
