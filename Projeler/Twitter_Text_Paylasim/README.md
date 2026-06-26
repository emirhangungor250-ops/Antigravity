# Twitter_Text_Paylasim

X (Twitter) ve LinkedIn için günlük metin/thread içeriği üreten dual-motor cron. Her sabah 07:10 UTC'de çalışır; weekday'a göre ilgili kaynaktan içerik çeker, kalite skorunu ölçer, eşik geçenleri Typefully'ye draft olarak atar (X thread + LinkedIn uzun-form aynı draft'ta) ve onay maili gönderir.

## Stack
Python 3, Anthropic Claude (Opus 4.7) writer + OpenAI fallback, Perplexity (haber), GitHub API (repo discovery), YouTube RSS, Kie AI (görsel), Typefully API (publishing proxy), Notion API (logging).

## Çalışma Şekli
Cron servis (Railway, `cronSchedule: 10 7 * * *`). Tek `main.py` weekday'ı bakar:
- **Salı:** GitHub trending repo discovery → tweet + LinkedIn varyant
- **Cuma:** Perplexity AI haber özeti → thread + LinkedIn
- **Her gün:** YouTube watcher (kanalda yeni video varsa thread + standalone'lar)

Eşik (`QUALITY_THRESHOLD`) altındakiler atlanır, üstündekiler:
1. Typefully'de draft oluşturulur (X thread + LinkedIn aynı draft'ta).
2. Notion `X DB`'ye Status=Pending olarak loglanır.
3. Sabah özet maili gönderilir; her draft için imzalı onay linki (Twitter_Onay_Api'ye gider).
4. Kullanıcı butona basınca Typefully draft 11/13/15:30 (TR) slot'larından birine schedule edilir.

LinkedIn projesi (`LinkedIn_Text_Paylasim`) artık ayrı API çağrısı yapmıyor — içeriği bu projenin draft'ına ekleniyor.

## Environment Setup
Ortam değişkenleri için `.env.example`'a bak. Doldurman gerekenler:
- `TYPEFULLY_API_KEY` — Typefully Pro API key
- `TYPEFULLY_SOCIAL_SET_ID` — X+LinkedIn social set ID
- `ANTHROPIC_API_KEY` — Claude Opus 4.7 writer için
- `OPENAI_API_KEY` — Image prompt + writer fallback
- `PERPLEXITY_API_KEY` — Cuma günü AI haber kaynağı
- `GITHUB_TOKEN` — Salı günü repo discovery
- `KIE_API_KEY` — Görsel üretim (AI Use Case serisi)
- `NOTION_SOCIAL_TOKEN` — Sosyal Notion DB token
- `NOTION_X_DB_ID`, `NOTION_DB_REELS_KAPAK` — DB ID'leri
- `YOUTUBE_CHANNEL_ID` — kendi YouTube kanalının UC ile başlayan ID'si
- `MAIL_SENDER`, `MAIL_RECIPIENT` — sabah özet mailinin gönderici/alıcı adresi
- `APPROVAL_SECRET`, `APPROVAL_API_URL`, `APPROVAL_BASE_URL` — onay akışı (Twitter_Onay_Api ile aynı sır)
- `QUALITY_THRESHOLD` (opsiyonel, default 8), `DEDUP_DAYS` (default 30)
- `LLM_PROVIDER` (opsiyonel, default `anthropic`)

## Deploy
Railway cron servis. `cronSchedule: 10 7 * * *` (07:10 UTC = 10:10 TR). RAILPACK builder. Auto-deploy: push deploy eder.
