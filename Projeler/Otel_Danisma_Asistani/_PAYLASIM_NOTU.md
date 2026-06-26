# Paylaşım Notu — Otel Danışma Asistanı

**Mod:** C (şablona çevrildi)

## Ne yapıldı

- **Temizlenen sırlar / tesise özel teknik değerler:**
  - Booking engine host'u (tesisin gizli rezervasyon adresi, aynı zamanda fiyat
    API'sinin TOTP challenge seed'i) → `HOTELRUNNER_HOST` env'ine taşındı
    (`<tesis-adi>.hotelrunner.com` placeholder).
  - Sabit kodlanmış bir ülke IP'si (yurt dışı sunucudan yerel fiyatı zorlamak için
    X-Forwarded-For değeri) → `HOTELRUNNER_GEO_IP` env'ine taşındı, varsayılan BOŞ.
  - ManyChat custom field + flow id envanteri (sahibin ManyChat hesabının IG/FB/WP
    için kayıtları) → placeholder `<..._ID>` / `<..._NS>` eşlemesine indirildi; gerçek
    değerler `MANYCHAT_PLATFORMS` env JSON'undan okunur.
  - Tesise özel önekli env adları (ManyChat token, hafıza tablosu vb.) jenerik adlara
    çevrildi (`MANYCHAT_TOKEN`, `DRY_RUN`, `WEBHOOK_SECRET`, `AGENT_MODEL`,
    `VISION_MODEL`, `HISTORY_WINDOW`, `chat_memory`). Kodda gerçek API anahtarı zaten
    YOKTU (hepsi env'den okunuyordu).

- **Scrub edilen kişisel / işletmeye özel veriler:**
  - Tesisin gerçek adı → `BUSINESS_NAME` env'i + sistem promptu "tesisimiz" jeneriği.
    Bot karakteri "{business} temsilcisi" olarak parametreleştirildi.
  - İletişim bilgileri (telefon, e-posta, web adresi) → `CONTACT_PHONE` / `CONTACT_EMAIL`
    env'leri. Grup eşiği → `GROUP_THRESHOLD`.
  - **knowledge_data/*.json (7 dosya)** — tesisin gerçek bilgisi (adres, oda/havuz/spa
    detayları, fiyat/pansiyon politikaları, ödeme/taksit, etkinlik programı + kişi adları,
    yerel ulaşım) TAMAMEN çıkarıldı → "buraya kendi bilginizi yazın" yapısını koruyan boş
    şablon iskeleti.
  - Sistem promptundaki tesise özel zorunlu politikalar generic örnek bölüme indirildi;
    çocuk yaş sınırı `CHILD_MAX_AGE` env'i ile parametreleştirildi.
  - Bot User-Agent + logger isimleri jenerikleştirildi (`HotelChatBot/2.0`, `hotel-chat.*`);
    FastAPI başlığı → "Otel Danışma Asistanı".
  - Knowledge routing ipuçlarındaki tesise özel terimler (kişi adları, yerel ulaşım/kurum
    adları) jenerik karşılıklara ("havalimanı", "toplu taşıma") indirildi.

- **Kopyaya alınmayanlar (allowlist dışı):** sahibin n8n workflow export'ları
  (webhook/ID içerir), iç çalışma/devir notları (`HANDOVER_*`, devir/cutover/denetim
  belgeleri) ve gerçek `.env`.

- **Doğrulama:** Tüm Python modülleri derlendi; stub'lı `test_pipeline.py` 22/22 geçti
  (hiçbir gerçek API çağrısı yapılmadan). README baştan jenerik olarak yazıldı.

## Öğrenci ne yapmalı

1. `.env.example` → `.env` kopyala ve doldur:
   - **Tesis kimliği:** `BUSINESS_NAME`, `CONTACT_PHONE`, `CONTACT_EMAIL`
     (opsiyonel: `GROUP_THRESHOLD`, `CHILD_MAX_AGE`).
   - **Fiyat servisi:** `HOTELRUNNER_HOST` (kendi rezervasyon sayfanızın
     `<tesis-adi>.hotelrunner.com` adresi). HotelRunner kullanmıyorsanız `hotelrunner.py`
     yerine kendi booking engine'inize uygun bir fiyat çekici yazılmalı.
   - **Bot:** `GROQ_API_KEY` (console.groq.com), `MANYCHAT_TOKEN` (ManyChat → Settings → API),
     `MANYCHAT_PLATFORMS` (kendi custom field + flow id eşlemeniz, JSON),
     opsiyonel `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (hafıza) ve `OPENAI_API_KEY`
     (görsel betimleme; sadece gpt-4o-mini).
2. **`knowledge_data/*.json`** dosyalarının içini kendi tesisinizin bilgisiyle doldurun
   (oda tipleri, havuz/spa, yeme-içme, toplantı, konum/ulaşım, genel bilgi/politikalar).
   Şablon yapı korunur; `<...>` placeholder'larını gerçek bilgiyle değiştirin.
3. Tesise özel zorunlu kurallarınızı (örn. belge şartı, pansiyon tipi açıklaması)
   `agent.py` içindeki "Tesise özgü politika" bölümüne ekleyin veya bilgi tabanına yazın.
4. ManyChat tarafında webhook'unuzu `/webhook` adresine yönlendirin; custom field + flow
   kurulumunuzu `manychat.py` `_DEFAULT_PLATFORMS` yapısına göre yapın.

## Orijinal amaç → yeni jenerik çerçeve

- **Orijinal:** Tek bir termal otelin Instagram/Facebook/WhatsApp ManyChat botu. Otelin
  rezervasyon booking engine adresi, ManyChat hesabının field/flow id'leri, adres +
  iletişim + oda/havuz/politika/etkinlik bilgileri ve tesise özel kurallar koda/JSON'a
  gömülüydü.
- **Yeni:** Müşterileri DM/WhatsApp'tan yazan herhangi bir konaklama işletmesi için jenerik
  ön-resepsiyon asistanı. İşletme adı, iletişim, grup/çocuk eşikleri, booking engine host'u,
  bilgi tabanı ve ManyChat id eşlemesi tamamen env/config-driven. Üç parçalı desen korundu:
  (1) booking engine'den saf-HTTP deterministik fiyat servisi (LLM yok), (2) Groq
  tool-calling ajanı (get_hotel_info / get_holiday / get_price), (3) burst coalesce + medya
  pipeline (ses → whisper, görsel → gpt-4o-mini, metin) + Supabase hafıza + ManyChat teslim.
