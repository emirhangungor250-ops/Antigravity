# YouTube Yorum Otomasyonu

Bir YouTube kanalının yorumlarını her gün tarayan, cevaplanmaya değer yeni yorumları
tek bir mail raporunda toplayan ve zamanla kanal sahibinin cevap tarzını öğrenip taslak
üreten iki fazlı bir sistem. İçerik üreticileri için: yorum kutusunda boğulmadan, gerçekten
cevap bekleyen yorumlara öncelik verip yanıtı tek tıkla göndermeni sağlar.

**Bu desen şuna yarar:** Yorum hacmi yüksek herhangi bir kanal/topluluk için. Sistem önce
hangi yorumun cevaba değer olduğunu (soru mu, dolu bir katkı mı, yoksa kısa övgü/spam mı)
bir LLM ile sınıflar; sonra senin geçmişte verdiğin gerçek cevapları sessizce öğrenir ve
o sese uygun taslaklar yazar. Kimin sesi, hangi kanal, hangi mail — hepsi env'den gelir.

## İki Faz

- **Faz 1 (varsayılan):** Her gün yeni cevaplanabilir yorumları çeker, akıllı sıralar
  (soru/dolu üstte), "Yorumu Yanıtla" derin linkiyle mail atar. Sen YouTube'da elle
  cevaplarsın. Sistem bu sırada kanalın gerçek cevaplarını **corpus**'a biriktirir (öğrenme).
- **Faz 2 (opsiyonel):** Yeterli örnek birikince, yeni yoruma en benzer geçmiş cevapları
  çekip senin sesinde taslak üretir. **Emin → yayınla** (gölge dönemde tek-tık onayla),
  **biraz fikri var → taslak**, **emin değil → dokunma**. Her onaylanan cevap corpus'a akar.

## Stack

- **YouTube Data API v3** — okuma API key ile (Faz 1, OAuth yok); yazma `youtube.force-ssl` OAuth (Faz 2).
- **Supabase (Postgres + pgvector)** — `yt_comments` (durum/idempotency) + `yt_reply_corpus` (öğrenme).
- **Voyage `voyage-3`** (1024d) — yorum embedding'i, benzerlik retrieval.
- **OpenAI `gpt-4.1-mini`** (varsayılan, env'den değişir) — yorum sınıflama + Faz 2 cevap üretimi.
- **Resend** — günlük rapor maili (kendi doğrulanmış domain'inden).

## Çalışma Şekli

`main.py` (Faz 1) → `core/comment_pipeline.py`:
1. `youtube_client.fetch_comment_threads()` — kanal geneli son yorumlar.
2. **Öğrenme (A):** kanalın zaten cevapladığı thread'lerden `(yorum, kanal cevabı)` çifti → `corpus.seed_pairs()`.
3. **Rapor (B):** izleyici yazmış + kanal cevaplamamış + yeni + raporlanmamış yorumlar →
   `llm.classify_worth_batch()` ile sıralanır → `yt_comments`'e yazılır → `mail_report.send_report()`.

## Kurulum

1. `.env.example`'ı `.env` olarak kopyala ve doldur. Faz 1 için zorunlu:
   `YOUTUBE_CHANNEL_ID`, `YOUTUBE_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`,
   `VOYAGE_API_KEY`, `RESEND_API_KEY`, `OPENAI_API_KEY`.
2. Kimlik: `YT_CREATOR_NAME` + `YT_CREATOR_BIO` — AI bu profilin sesinde cevap yazar.
3. Veritabanı: `db/schema.sql`'i kendi Supabase projende (SQL Editor) çalıştır.
4. Test (mail atmadan):
   ```
   YT_DRY_RUN=1 python main.py
   ```
   Salt-okuma smoke testi: `python tests/smoke_phase1.py` (DB'ye yazmaz).

## Çalıştırma

Periyodik bir iş olduğu için günlük bir cron (ör. her gün bir kez) olarak çalıştırılır.
`railway.json` Railway için hazır (günlük cron, `python main.py`); lokalde de elle koşabilirsin.
Bir platforma deploy edeceksen monorepo'da servis ayarında bu klasörü kök dizin olarak ver.

## Faz 2 (AI taslak + onay akışı)

`YT_PHASE=2` set edildiğinde aynı komut `generate.py`'ye geçer. Her cevaplık yoruma
`reply_writer.py` senin sesinde taslak üretir, maile koyar. Gölge dönem: `YT_AUTO_POST=0`
(otomatik yayın yok; öğrenme pasif corpus seed'iyle sürer).

- **Kopyala akışı:** Mail kartında "Cevabı kopyala" butonu cevabı + YouTube linkini link
  hash'inde taşır; eşlik eden **YouTube_Kopya_Sayfa** projesi (`YT_COPY_PAGE_URL` env'i)
  cevabı panoya kopyalar ve YouTube'u açar. HTML mailler JS çalıştıramadığı için kopyalama
  ayrı sayfada yapılır. Link üretilemezse kart YouTube derin linkine düşer (kırılmaz).
- **Otomatik yayın (opsiyonel):** `web/app.py` HMAC imzalı tek-tık "onayla ve yayınla"
  akışıdır; oto-yayın istersen kullanılır. Yorum yazma izni için bir kez
  `setup_youtube_forcessl.py` ile OAuth onayı verilir.

## Eşlik eden proje

Faz 2 kopyala butonu, ayrı bir statik sayfa servisi olan **YouTube_Kopya_Sayfa** ile çalışır.
İkisi `YT_COPY_PAGE_URL` üzerinden eşlenir. Faz 1'de bu servise gerek yoktur.
