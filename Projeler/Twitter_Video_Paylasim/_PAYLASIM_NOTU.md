# Paylasim Notu — Twitter_Video_Paylasim

## Mod
A — Dogrudan ver.

## Ne yapildi
- Tam credential dump iceren kaynak `.env` dosyasi KOPYALANMADI (sadece `.env.example` uretildi).
- `__pycache__`, `.pyc` dosyalari temizlendi.
- Kisisel veri scrub'lari:
  - `config.py` — `X_HANDLE` default'u kişisel handle'dan `<X_HANDLE>` placeholder'ina cevrildi
  - `core/typefully_publisher.py` — dry-run URL'sindeki kisisel handle → `<X_HANDLE>`
  - `core/content_filter.py` — LLM prompt'larindaki "<KULLANICI_ADI>" + kisisel nis tanimi jeneriklestirildi
  - `core/notion_video_selector.py` — kisisel Notion DB adi jeneriklestirildi
  - `README.md` — kisisel DB adlari, handle default'u, ic deploy-registry referansi temizlendi
- Yeni `.env.example` uretildi (proje hic yoktu).

## Ogrenci ne yapmali
`.env.example` dosyasini `.env` olarak kopyalayip su degiskenleri doldurun:
- `TYPEFULLY_API_KEY`, `TYPEFULLY_SOCIAL_SET_ID` — Typefully hesap bilgileri
- `X_HANDLE` — kendi X (Twitter) kullanici adiniz
- `GROQ_API_KEY` — Groq API anahtari
- `NOTION_SOCIAL_TOKEN`, `NOTION_DB_REELS_KAPAK`, `NOTION_TWITTER_DB_ID` — Notion entegrasyonu
- `GOOGLE_SERVICE_ACCOUNT_JSON` — Google Drive erisimi icin base64 service account JSON
