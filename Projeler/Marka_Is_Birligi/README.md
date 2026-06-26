# 🤝 Marka İş Birliği — Otomatik Outreach Sistemi

Markalarla iş birliği kurma, kişiselleştirilmiş outreach gönderimi ve
follow-up yönetimi yapan tam otomatik bir pipeline.

**Bu desen şuna yarar:** İçerik üreticisi, ajans veya freelancer olarak
markalara/şirketlere düzenli soğuk e-posta atan herkes için. Rakip
hesapları analiz ederek yeni potansiyel markaları keşfeder, iletişim
bilgilerini bulur, AI ile kişiselleştirilmiş mail üretir ve çok adımlı
takip dizisi ile süreci otomatik yürütür. Niş, profil ve hedef kitle
tamamen config dosyalarından gelir — kendi kullanımına uyarlayabilirsin.

## 🔄 Pipeline Akışı

```
1. Scrape      → 2. Analyze        → 3. Find Contacts    → 4. Personalize     → 5. Send
   (Apify)        (marka tespiti)     (Hunter + web)        (OpenAI)            (Gmail API)
```

1. **Scrape** (`scraper.py`) — Apify ile takip ettiğin rakip hesapların son içeriklerini çeker
2. **Analyze** (`analyzer.py`) — Caption + mention analiziyle yeni markaları keşfeder; `config/brand_filters.json` listeleriyle false positive / bilinen marka filtresi uygular
3. **Find Contacts** (`contact_finder.py`) — Web scrape (About/Team/Contact sayfaları) → Hunter.io domain search → Hunter.io email verify. Doğrulanamayan email gönderilmez.
4. **Personalize** (`personalizer.py`) — OpenAI ile markaya özel HTML email üretir. Gönderen profil bilgileri `config/creator_profile.json`'dan okunur. API yoksa `mail_templates/` fallback şablonları kullanılır.
5. **Send** (`outreach.py`) — Gmail API ile gönderim, günlük limit, CSV'ye kayıt.

### Çok Adımlı Email Sequence

| Adım | Zamanlama | Modül |
|------|-----------|-------|
| İlk Outreach | Haftalık | `outreach.py` |
| Follow-up 1 | +5 gün | `followup.py` |
| Follow-up 2 | +5 gün daha | `followup.py` (cevap yoksa kapanış) |

### Ek Mekanizmalar
- **Response Checker** (`response_checker.py`) — Gelen yanıt ve bounce tespiti
- **Reporter** (`reporter.py`) — Haftalık Telegram istatistik raporu

## 📂 Proje Yapısı

```
Marka_Bulma_Outreach/
├── railway_scheduler.py     ← Railway zamanlayıcı + health server
├── railway.json             ← Railway deploy konfigürasyonu
├── requirements.txt
├── env_loader.py            ← Lokal env yükleyici
├── src/                     ← Ana kaynak kod (scraper, analyzer, contact_finder,
│                              personalizer, outreach, followup, response_checker,
│                              reporter, gmail_sender, website_discovery, utils/)
├── config/
│   ├── kampanya.yaml         ← Kampanya konfigürasyonu (kendi nişine göre doldur)
│   ├── creator_profile.json  ← 🔧 Outreach gönderen kişinin profili (KENDİNİ YAZ)
│   ├── brand_filters.json    ← Marka tespit filtreleri (kendi listenle doldur)
│   └── rakipler.csv          ← Takip edilen rakip hesap listesi (kendi listenle doldur)
├── data/                    ← 🔒 .gitignore'da (dinamik/hassas veri)
│   └── calisan_markalar.json ← Zaten çalışılan markalar (dedup template'i)
├── mail_templates/          ← Fallback HTML/MD şablonları + ornekler/
├── markalar/                ← Marka isim listeleri (şablon)
└── tests/                   ← pytest test suite
```

## ⏰ Railway Zamanlama

Railway üzerinde 7/24 çalışan bir scheduler servisi olarak deploy edilir.
Zamanlama `railway_scheduler.py` içinde tanımlıdır (haftalık pipeline +
follow-up kontrolü + haftalık rapor). Her pipeline çalışmasından önce
otomatik Response Check yapılır.

Health check endpoint'i `GET /` üzerinden JSON durum bilgisi döndürür.

## 🔑 Environment Setup

`.env.example`'ı `.env` olarak kopyalayıp doldur. Railway'de aynı isimlerle
servis env'ine geçir.

| Servis | Env Variable | Kullanım |
|--------|-------------|----------|
| Notion | `NOTION_SOCIAL_TOKEN`, `NOTION_DB_BRAND_REACHOUT`, `NOTION_DB_BRAND_LOGS`, `NOTION_DB_OPS_LOG` | Outreach + log DB'leri |
| Apify | `APIFY_API_KEY_1`, `APIFY_API_KEY_2` | Rakip içerik scraping (rotasyon) |
| Hunter.io | `HUNTER_API_KEY` | Email bulma + doğrulama |
| OpenAI | `OPENAI_API_KEY` | GPT email kişiselleştirme |
| Gmail OAuth | `SENDER_EMAIL`, `GOOGLE_OAUTH_TOKEN_JSON` | Email gönderim (Railway'de base64 encoded token) |
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Haftalık rapor |
| Davranış | `ALLOW_RISKY_EMAILS` (default false), `PORT` | Hunter `risky` filtresi |

## 🧩 Uyarlama Adımları

1. `config/creator_profile.json` → kendi adın, profillerin, başarı örneklerin.
2. `config/kampanya.yaml` → kendi nişin, hedef sektörler, anahtar kelimeler.
3. `config/brand_filters.json` → ilgilendiğin kategori markaları + false positive hesaplar.
4. `config/rakipler.csv` → takip etmek istediğin rakip hesaplar.
5. `mail_templates/` → fallback şablonlardaki `{{ ... }}` placeholder'larını kendine göre doldur.

## 📊 CSV Veri Modeli (`data/markalar.csv`)

Her satır bir markayı temsil eder. Önemli sütunlar: `lead_id`, `marka_adi`,
`instagram_handle`, `email`, `email_status`, `outreach_status`,
`outreach_thread_id`, `followup_status`, `followup2_status`.
