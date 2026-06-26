# Paylasim Notu — Web_Site_Satis_Otomasyonu

## Mod
A — Dogrudan ver.

## Ne yapildi
- `venv/`, `.DS_Store`, `output.json` (uretilmis cikti) kopyalanmadi.
- Kisisel veri scrub'lari:
  - `research_apify.py` — sabit kodlanmis kisisel mutlak `master.env` yolu kaldirildi; token artik ortam degiskeninden okunuyor
  - `src/config.py` — sabit `master.env` yolu kaldirildi, yerine proje koku `.env` okuma; sabit kodlanmis Notion kokpit sayfa ID'si `NOTION_COCKPIT_PAGE_ID` env degiskenine tasindi
  - `src/lead_generator.py` — log mesajindaki `master.env` referansi jeneriklestirildi
  - `IMPLEMENTATION_PLAN_v2.md` — kisisel Notion sayfa URL'si kaldirildi
- `.env.example` guncellendi: `NOTION_COCKPIT_PAGE_ID` eklendi, placeholder'lar netlestirildi.

## Ogrenci ne yapmali
`.env.example` → `.env` kopyalayip doldurun:
- `APIFY_API_KEY_1`, `APIFY_API_KEY_2` — Apify token'lari (fail-over icin 2 tane)
- `NOTION_API_TOKEN` — Notion integration token
- `NOTION_COCKPIT_PAGE_ID` — kendi Notion workspace'inizde olusturacaginiz kokpit sayfasinin ID'si
- `NOTION_LEAD_DB_ID` — ilk calistirmada otomatik olusur, sonra buraya yazilir
- `SUPABASE_URL`, `SUPABASE_ANON_KEY` — opsiyonel (loglama; bos birakilirsa devre disi)
