# LinkedIn Paylaşım — Notion + Drive → Typefully → LinkedIn Master Pipeline

Notion'daki "Yayınlandı" videoları, Google Drive'daki master kalitedeki dosyalardan
Typefully üzerinden LinkedIn'e otomatik paylaşan günlük pipeline.

## Özellikler

- **Master Kalite:** Drive'daki orijinal master `.mp4` dosyası kullanılır — TikTok kompresyonu yok, watermark yok
- **Sıfır Kayıp:** FFmpeg sadece kayıpsız faststart remux yapar (`-c copy`); >200MB'da otomatik compress
- **Akıllı Caption:** Groq LLM, sayfa script'inden tek cümlelik LinkedIn caption üretir (max 280 char, hashtag yok, CTA yok, **spesifik ürün adı yok** — jenerik kategori + tavsiye dili)
- **Notion Dedup:** Aynı video iki kez paylaşılmaz; logger DB sorgu yapar
- **Günlük 1 Paylaşım:** Cron `0 10 * * *` (UTC) = 13:00 TR
- **Typefully Proxy:** LinkedIn OAuth refresh derdi YOK; 15 dk video upload polling YOK. Typefully kendi LinkedIn entegrasyonu üzerinden paylaşır.

## Akış

1. Notion `Reels & YouTube` DB → `Status = "Yayınlandı"` videoları çek (Paylaşım Tarihi DESC)
2. Logger DB'de zaten paylaşılmamış ilk video
3. `Drive` property'sindeki klasörü Service Account ile aç
4. Klasördeki dosyalardan pattern öncelikli seç: `tiktok` > `insta` (env: `VIDEO_PATTERN_PRIORITY`)
5. Drive'dan indir → kayıpsız faststart remux (gerekirse compress)
6. Notion sayfa body'sinden Groq ile tek cümle caption üret
7. Typefully `/media/upload` (S3 presigned PUT) + `/drafts` (publish_at=now, platforms.linkedin)
8. Logger DB'ye `page_id` ile kayıt at

## Mimari

```
main.py → Pipeline orchestration
├── core/notion_video_selector.py → Notion DB sorgu + Drive URL parse
├── core/drive_downloader.py      → Service Account ile klasör listele + dosya indir
├── core/video_processor.py       → Faststart remux (kayıpsız); >REENCODE_OVER_BYTES ise compress
├── core/content_filter.py        → CaptionGenerator + SuitabilityFilter (Groq)
├── core/typefully_publisher.py   → Typefully /media/upload + /drafts (LinkedIn social set)
└── core/notion_logger.py         → Logger DB (dedup birincil anahtar: page_id)
```

## Environment Variables

| Variable | Açıklama |
|----------|----------|
| `TYPEFULLY_API_KEY` | Typefully hesap API key (X cron'u ile aynı) |
| `TYPEFULLY_LINKEDIN_SOCIAL_SET_ID` | LinkedIn-only Typefully social set ID (Settings → Social Sets'ten kopyala) |
| `GROQ_API_KEY` | Groq API key |
| `GROQ_MODEL` | (opsiyonel) default `llama-3.3-70b-versatile` |
| `NOTION_SOCIAL_TOKEN` | Notion integration token |
| `NOTION_DB_REELS_KAPAK` | Kaynak DB ("Reels & YouTube") |
| `NOTION_LINKEDIN_DB_ID` | Logger DB |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | (Railway) base64 encoded SA JSON; lokal: `_knowledge/credentials/google-service-account.json` |
| `VIDEO_PATTERN_PRIORITY` | (opsiyonel) Virgüllü liste, default `tiktok,insta` |
| `MAX_VIDEO_BYTES` | (opsiyonel) Üzerini skip et, default 500MB |
| `REENCODE_OVER_BYTES` | (opsiyonel) Bunun üzerinde compress yap; default 200MB |

> **Deprecated 2026-05-09 — Typefully migration:** `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`
> artık kullanılmıyor. Typefully kendi LinkedIn auth'unu yönetiyor.

## Çalıştırma

```bash
ENV=development python main.py    # lokal DRY-RUN
RUN_MODE=cron python main.py      # Railway cron
```

## Deploy

Railway servis: `linkedin-video-cron` (auto-deploy KAPALI; `serviceInstanceDeployV2` mutation
ile manuel commit deploy gerekli — bkz. `_knowledge/deploy-registry.md`).
