# YouTube Açıklama Otomasyonu

YouTube videolarınıza otomatik olarak (1) chapter'lı açıklama yazar, (2) iş birliği yapılan markanın affiliate linkini ekler, (3) Notion'daki video satırının Drive klasörüne Google Docs olarak bırakır.

## Akış

1. Cron her 15 dakikada bir yapılandırılmış Notion DB'sini tarar.
2. `Durum = "Yayınlandı"` + `URL` (YouTube linki) dolu + `Drive` (klasör) dolu olan satırları alır.
3. Drive klasöründe `Aciklama_Taslagi*.docx` zaten varsa atlar (idempotency).
4. YouTube transcript'ini `youtube-transcript-api` ile çeker.
5. Claude Opus 4.7 ile (style corpus + brief + transcript girdi olarak) yapılandırılmış açıklama üretir: ana metin + chapter'lar + marka anahtarı.
6. `data/brand_affiliates.json` map'inden marka adına karşılık gelen affiliate linki çeker.
7. Drive klasörüne yeni Google Docs olarak yazar (HTML upload, Drive auto-convert).
8. Telegram'a "Hazır: {Docs link}" bildirimi yollar.

## Stack

- Python 3.11
- `anthropic` (Claude Opus 4.7, structured output)
- `notion-client`
- `youtube-transcript-api`
- `apify-client` (sadece style corpus üretimi için)
- `google-api-python-client` (Drive, HTML upload yolu)

## Çalışma Şekli

**Bir kerelik kurulum:**

```bash
python scripts/build_style_corpus.py
```

Bu komut `data/style_corpus.json` (kanal video açıklamaları) + `data/brand_affiliates.json` (marka → affiliate link map) üretir. Ayda bir manuel yenilenebilir. Alternatif olarak bu iki dosyayı elle de doldurabilirsiniz.

**Production:**

Railway cron `*/15 * * * *`. `main.py` çalışır, yeni "Yayınlandı" videoları için Docs üretir.

## Environment Setup

`.env.example` dosyasını `.env` olarak kopyalayın ve değerleri doldurun.

## Deploy

Railway'e push edilir. `rootDirectory` proje klasörü olmalı.

## Reusable Kaynaklar

- `core/google_auth.py` — Google Drive OAuth (outreach hesabı, drive.file scope)
- `core/transcript_service.py` — YouTube transcript çekimi
- `scripts/build_style_corpus.py` — Apify Store actor `streamers/youtube-scraper`
