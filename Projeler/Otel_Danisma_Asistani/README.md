# Otel Danışma Asistanı

İşletme/otel için Instagram, Facebook ve WhatsApp (ManyChat) üzerinden çalışan bir
danışma + fiyat/müsaitlik chatbot'u. Misafir sorularını yanıtlar, tesis bilgisi verir,
tarihe göre müsaitlik ve konaklama fiyatı çeker, tatil tarihlerini bilir. Tüm mantık
Python'da; Claude Code ile kolayca uyarlanır.

## Bu desen ne işe yarar

Müşterilerinin çoğu DM/WhatsApp'tan yazan herhangi bir konaklama işletmesi (otel, butik
otel, pansiyon, apart) için bir ön-resepsiyon asistanı kurar. "Müsait mi? Ne kadar?
Havuz var mı? Nasıl gelirim?" gibi tekrar eden soruları otomatik karşılar; rezervasyon
fiyatını booking engine'inizden canlı çeker. Aynı desen küçük değişikliklerle başka
randevu/rezervasyon işlerine de uyarlanabilir.

Üç parça birlikte çalışır:
1. Deterministik fiyat servisi (booking engine API'sinden saf HTTP, LLM yok).
2. LLM ajanı (Groq tool-calling) — soruyu anlar, doğru aracı seçer, kısa cevap üretir.
3. Yerel bilgi tabanı (knowledge_data/*.json) — tesisinizin oda/havuz/politika bilgisi.

## Stack

- Python + FastAPI (web service; Railway için hazır)
- `requests` / `httpx` (HotelRunner booking engine JSON API)
- Groq (LLM, ucuz workhorse) + opsiyonel gpt-4o-mini (görsel betimleme)
- Supabase (konuşma hafızası, opsiyonel)
- ManyChat API (IG/FB/WhatsApp yanıt gönderme)

## Çalışma Şekli

**Phase 1 — Fiyat servisi.** `POST /price` → HotelRunner booking engine'inin public JSON
API'sinden müsaitlik + fiyat. Üç GET ile (tarayıcı/screenshot/proxy YOK): sunucu zamanı →
oda tipleri + rate id'leri → fiyatlar. Tek kapı bir `X-HR-CHALLENGE` TOTP header'ıdır
(kod kendisi üretir). Booking engine host adresi env'den gelir (`HOTELRUNNER_HOST`).

**Phase 2 — Tam bot.** `POST /webhook` (ManyChat) → mesaj kuyruğa eklenir (burst coalesce) →
her mesaj medya tipine göre çözülür (ses → whisper, görsel → vision, metin → aynen) →
birleştirilir → hafıza yüklenir → ajan (Groq tool-calling: `get_hotel_info` /
`get_holiday` / `get_price`) → cevap → ManyChat push (platforma + link var/yok durumuna
göre custom field + flow). Webhook anında 200 döner, iş arka planda işlenir.

### Modüller

`config.py` (env), `llm.py` (Groq sohbet + whisper), `media.py` (medya sınıflandırma),
`vision.py` (görsel betimleme), `coalesce.py` (mesaj birleştirme), `knowledge.py`
(yerel bilgi tabanı + yönlendirme), `holidays.py` (TR tatil tablosu), `memory.py`
(Supabase hafıza), `manychat.py` (IG/FB/WP field/flow eşlemesi), `agent.py` (ana ajan),
`hotelrunner.py` (fiyat), `main.py` (FastAPI). Pipeline testi: `python test_pipeline.py`
(hiçbir gerçek API çağrısı yapmaz, tümü stub'lanır).

### `POST /price`

İstek:
```json
{ "checkin_date": "2026-08-20", "checkout_date": "2026-08-22",
  "rooms": [{"adult_count": 2, "child_count": 0, "child_ages": []}] }
```
veya düz tek-oda: `{"checkin_date": "...", "checkout_date": "...", "adult_count": 2, "child_count": 0, "child_ages": [], "room_count": 1}`

Yanıt:
```json
{ "available": true, "checkin": "...", "checkout": "...", "nights": 2,
  "link": "<booking url>", "rooms": [{"name": "...", "total": 18000.0, ...}],
  "message": "<Türkçe özet>" }
```

## Kurulum

1. `.env.example` → `.env` kopyalayın, doldurun (en az `BUSINESS_NAME`, `CONTACT_PHONE`,
   `CONTACT_EMAIL`, `HOTELRUNNER_HOST`; bot için `GROQ_API_KEY`, `MANYCHAT_TOKEN`,
   `MANYCHAT_PLATFORMS`, opsiyonel `SUPABASE_*` ve `OPENAI_API_KEY`).
2. `knowledge_data/*.json` dosyalarını **kendi tesisinizin bilgisiyle** doldurun (şablon
   olarak gelir, içini siz yazarsınız: oda tipleri, havuz/spa, yeme-içme, konum, politikalar).
3. Tesise özgü politika kurallarınızı `agent.py` içindeki "Tesise özgü politika" bölümüne
   ekleyin (örn. belge zorunluluğu, pansiyon tipi açıklaması) — ya da bilgi tabanına yazın.
4. Kurulum: `pip install -r requirements.txt`, `uvicorn main:app --reload`.

CLI fiyat testi: `python hotelrunner.py <giris-tarihi> <cikis-tarihi> <kisi-sayisi>`

## Deploy (opsiyonel)

Railway web service olarak çalışır. `railway.json`: RAILPACK builder,
`uvicorn main:app --host 0.0.0.0 --port $PORT`, restart ALWAYS. Tek replika (numReplicas=1)
varsayılır — burst coalesce in-process state'e dayanır. Başka bir platform da
kullanabilirsiniz.

ManyChat tarafında webhook adresinizi bu servise (`/webhook`) çevirin; custom field ve
flow id'lerinizi `MANYCHAT_PLATFORMS` env'ine girin.

## Model politikası

LLM tarafı Groq `openai/gpt-oss-120b` (ucuz workhorse) kullanır. Pahalı modeller (Opus /
Sonnet / gpt-4o) varsayılan yapılmaz. Fiyat akışında LLM yoktur (veri zaten yapısaldır).
Görsel betimleme yalnızca `gpt-4o-mini` kullanır (kod bu sınırı zorlar). Ses
transkripsiyonu Groq whisper ile ucuzdur.
