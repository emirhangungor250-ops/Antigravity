# WhatsApp Onboarding

Yeni kayıt olan üyelere 7 gün boyunca WhatsApp üzerinden onboarding videoları
gönderen drip otomasyon sistemi. Telefon numarası geçersizse e-posta fallback'e
düşer (hibrit teslim). Bu bir **şablondur**: ManyChat flow ID'leri, e-posta drip
içeriği, video linkleri ve Notion şeması sizden gelir.

## Akış

```
Yeni üye → Webhook (Zapier vb.) → Express → Notion CRM + ManyChat API → WhatsApp
                                          ↳ Hibrit fallback: Resend (email + WA CTA)
```

## Altyapı

| Bileşen | Detay |
|---------|-------|
| Runtime | Node.js 20+ (Express) |
| Hosting | Railway (Worker — 7/24) |
| CRM | Notion database |
| Mesajlaşma | ManyChat WhatsApp API |
| E-posta fallback | Resend API |
| Telefon validasyonu | Groq (LLaMA, libphonenumber-js fast-path) |

Railway servis/proje ID'leri, domain ve GitHub repo bilgileri bu şablonda
**yer almaz** — kendi Railway projenizi oluşturup deploy edersiniz.

## Webhook Endpoints

| Endpoint | Tetikleyen | Açıklama |
|----------|-----------|----------|
| `POST /webhook/new-paid-member` | Webhook kaynağı | Yeni üyeyi Notion'a kaydeder |
| `POST /webhook/membership-questions` | Webhook kaynağı | Telefon valide eder, WhatsApp onboarding başlatır |
| `POST /webhook/wa-optin` | ManyChat | Email fallback'teki kullanıcıyı WhatsApp kanalına geçirir |
| `POST /webhook/wa-failed` | ManyChat | WhatsApp teslim başarısızsa hibrit fallback email gönderir |
| `GET /health` | Monitoring | Servis sağlık kontrolü |

## Doldurmanız Gereken Şablon Alanlar

| Dosya | Ne yaparsınız |
|---|---|
| `.env` | Tüm API anahtarları + ManyChat flow/field ID'leri + WA business telefon |
| `config/templates.js` | ManyChat flow ID'leri `.env`'den okunur — env'i doldurun |
| `services/resend.js` | 7 günün e-posta konuları, gövdeleri, video + thumbnail URL'leri, link `[KÖŞELİ PARANTEZ]` alanları |
| Notion DB | `Uye ID`, `Email`, `İsim`, `Soyisim`, `Telefon`, `Onboarding Durumu` vb. property'leri içeren bir database oluşturun |

## Ortam Değişkenleri

Zorunlu: `NOTION_API_KEY`, `NOTION_DATABASE_ID`, `MANYCHAT_API_TOKEN`,
`GROQ_API_KEY`, `WEBHOOK_SECRET`. Detay ve placeholder'lar için `.env.example`.

Opsiyonel: `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `WA_BUSINESS_PHONE`,
`ADMIN_SECRET`, `ADMIN_ALERT_EMAIL`, `MANYCHAT_FLOW_DAY_0..6`,
`MANYCHAT_FIELD_ONBOARDING_NAME`, `MANYCHAT_FIELD_WHATSAPP_PHONE`.

## Dosya Yapısı

```
WP_Onboarding/
├── server.js              # Express + webhook endpoints + boot validations + graceful shutdown
├── cron.js                # Günlük cron — Notion run-lock + 429 retry + atomic dual-channel
├── manual_onboard.js      # Tek seferlik manuel onboarding script
├── services/
│   ├── notion.js          # CRUD + run-lock + schema validate + bounded pagination
│   ├── manychat.js        # Subscriber + sendFlow + flow validation + timeouts
│   ├── phoneValidator.js  # Telefon validasyonu (PII masked logs)
│   └── resend.js          # Email fallback + hibrit WA CTA (ŞABLON: drip içeriği)
├── config/
│   ├── templates.js       # ManyChat flow ID eşleştirmeleri (env'den okur)
│   └── env.js             # Fail-fast env validation
├── utils/
│   ├── logger.js          # Yapılandırılmış log + recursive PII redaction
│   └── phone.js           # toE164 + maskPhone
├── tests/                 # Debug / test script'leri
├── package.json
├── railway.json
└── .env.example
```

## Mimari Notları (Production Hardening)

- `WEBHOOK_SECRET` fail-secure: yoksa boot çöker, tüm `/webhook/*` 401 döner
- Day 0 çift gönderim engeli: Notion-backed transaction lock
- 429 exponential backoff, multi-instance run-lock, SIGTERM graceful shutdown
- KVKK: telefon/email/secret alanları log'da otomatik maskelenir
- `AbortSignal.timeout` her dış fetch'te, bounded pagination

## Kurulum

```bash
npm install
cp .env.example .env   # tüm <...> placeholder'ları doldurun
# config/templates.js + services/resend.js içindeki şablon alanları doldurun
# Notion DB'yi gerekli property'lerle oluşturun
npm run dev
```

## Deploy (Railway)

Builder NIXPACKS, start `node server.js`. `railway.json` hazır gelir. Kendi
Railway projenizi oluşturup GitHub repo'nuza bağlayın; push → auto-deploy.
