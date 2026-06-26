# RUNBOOK: YouTube Yorum Otomasyonu

Bir YouTube kanalının yorumlarını günlük tarayan iki fazlı otomasyon. Faz 1: yeni cevaplanabilir yorumları sınıflar, sıralar ve "Yorumu Yanıtla" derin linkli mail raporu atar; kanalın gerçek cevaplarını sessizce öğrenme corpus'una biriktirir. Faz 2 (opsiyonel): corpus'tan few-shot ile kanal sahibinin sesinde taslak üretir, tek-tık onay/yayın akışı `web/app.py`'dedir.

## Servis

| Tetik | Komut | İş |
|-------|-------|----|
| Günlük cron (ör. `0 6 * * *` UTC) | `python main.py` | Yorum çek → corpus seed → sınıfla → kalite kapısı → mail raporu |

Periyodik bir iştir: süreç işini bitirince çıkmalıdır (worker değil, cron). `YT_PHASE=2` set edilirse aynı komut değişmeden Faz 2'ye (`generate.py`) geçer.

## Deploy

Bir platforma deploy edeceksen (Railway, Render, Fly.io vb.) bu klasörü servis kök dizini olarak ver; aksi halde build sessizce başarısız olabilir. `railway.json` Railway için hazırdır (günlük cron). Lokalde de elle çalıştırabilirsin.

- **Cron anlık çalıştırma:** redeploy cron'u tetiklemez; platformun cron override'ı gerekir.
- **Lokal test (mail atmadan):** `YT_DRY_RUN=1 python main.py`.

## Veri

Kendi Supabase projende: `yt_comments` (durum + idempotency), `yt_reply_corpus` (öğrenme, pgvector + `match_reply_corpus` RPC). Şema `db/schema.sql`. Aynı yorum iki kez raporlanmaz; pencereyi genişletmek güvenlidir.

## Env Var

Faz 1 zorunlu (eksikse koşu başta iptal olur, log'a "Eksik anahtar" düşer):

- `YOUTUBE_CHANNEL_ID` (hangi kanal taranacak)
- `YOUTUBE_API_KEY` (okuma, OAuth yok)
- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`
- `VOYAGE_API_KEY` (embedding, voyage-3)
- `RESEND_API_KEY` (rapor maili, kendi doğrulanmış domain'in)
- `OPENAI_API_KEY` (veya `OPENAI_API_KEY_DATA_SHARED`): sınıflama + Faz 2 taslak

Kimlik + davranış anahtarları (opsiyonel, default'lar `config.py`'de):

- `YT_CREATOR_NAME`, `YT_CREATOR_BIO` (AI'nın taklit edeceği ses)
- `YT_PHASE` (1=rapor+öğren, 2=AI taslak), `YT_AUTO_POST` (Faz 2 gölge dönem freni), `YT_DRY_RUN`
- `YT_LOOKBACK_DAYS`, `YT_MAX_THREADS`, `YT_MAX_EMAIL_CARDS`, `YT_REPORT_MIN_SCORE`
- `YT_REPORT_TO` / `YT_REPORT_FROM` / `YT_REPORT_REPLY_TO`
- Faz 2 ek: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_FORCESSL_TOKEN_JSON` (yorum yazma OAuth), `YT_APPROVAL_BASE_URL` + `YT_APPROVAL_SECRET` (onay servisi), `YT_COPY_PAGE_URL` (kopyala sayfası)

## Triyaj

| Belirti | Bak | Çöz |
|---------|-----|-----|
| Mail hiç gelmedi | Cron log'unda son koşu çıktısı | "Yeni cevaplanabilir yorum yok" veya "eşiği geçmedi" ise normal, mail bilinçli atılmıyor. Log yoksa cron hiç koşmamış: deploy başarılı mı, kök dizin doğru mu bak |
| Koşu çöküyor, uyarı maili geldi | Log'daki "Koşu hatası" satırı | En sık: Supabase free-plan uykusu (pause olur, dashboard'dan restore et) veya YouTube API kota/key sorunu |
| Koşu başta iptal, "Eksik anahtar(lar)" | Log'daki eksik key listesi | İlgili env var'ı ekle, redeploy |
| Rapor çöp dolu / her şey maile giriyor | Sınıflama fail-open çalışmış olabilir (LLM patlarsa herkes score=60 alır) | OpenAI key'i + log'u kontrol et; kalıcıysa `YT_REPORT_MIN_SCORE` yükselt |
| Mail "doğrulanamadı" uyarısı | Gönderim Resend üzerinden mi (kendi domain'in) | `RESEND_API_KEY` + domain DKIM/SPF kaydı |
| Faz 2: taslak var ama yayınlanmıyor | `YT_AUTO_POST` değeri + force-ssl token | Gölge dönemde (`=0`) otomatik yayın bilinçli kapalı; token yoksa `setup_youtube_forcessl.py` ile bir kez OAuth onayı |

## Loglar

- **Cron log'u** tek koşu özeti basar: çekilen thread, corpus'a eklenen, yeni yorum, maile giren, elenen, corpus toplamı.
- **Supabase `yt_comments`** kalıcı durum kaydıdır: hangi yorum ne zaman raporlandı/taslaklandı/yayınlandı buradan görülür.
- Lokal smoke testleri: `tests/smoke_phase1.py`, `tests/preview_drafts.py` (mail atmadan kontrol).
