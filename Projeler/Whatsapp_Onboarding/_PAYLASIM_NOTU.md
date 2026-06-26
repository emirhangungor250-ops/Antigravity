# Paylaşım Notu — WP_Onboarding

## Mod
C — Şablona çevir

## Ne yapıldı

### Temizlenen sırlar
- **KRİTİK:** `tests/check_railway.py` içinde canlı bir Railway API token'ı
  (`14ac7442-...`) hardcoded duruyordu — dosya tamamen silindi.
- `.env` dosyası kopyalanmadı (`.env.example` korundu, placeholder'larla yeniden yazıldı).
- `.env.example` içindeki gerçek değerler temizlendi: gerçek WA telefon numarası,
  kişisel kurumsal from-email.

### Scrub edilen kişisel veriler
- `config/env.js`: resendFromEmail default'u kişisel markalı kurumsal adresten →
  `Onboarding <onboarding@example.com>`; `ADMIN_ALERT_EMAIL` env değişkeni eklendi
- `config/templates.js`: hardcoded ManyChat flow ID'leri (7 adet) ve custom field
  ID'leri → `.env`'den okunacak şekilde refactor edildi (`MANYCHAT_FLOW_DAY_N`,
  `MANYCHAT_FIELD_*`)
- `services/resend.js`: 7 günlük drip e-posta içeriği şablona indirildi — "AI Factory"
  marka adı → `[TOPLULUK ADI]`; Skool/JoinSecret/app store URL'leri → `[...URL]`
  placeholder; gerçek YouTube Short linkleri ve Cloudinary thumbnail URL'leri →
  `[VIDEO_URL_GUN_N]` / `[THUMBNAIL_URL_GUN_N]` placeholder; admin alert e-postası
  kişisel e-postadan `config.adminAlertEmail` env değişkenine taşındı
- `services/notion.js` + `server.js` + `manual_onboard.js`: hardcoded Notion DB ID
  yorumu kaldırıldı; owner'ın platformunu açık eden `Skool ID` Notion property adı →
  nötr `Uye ID`
- `package.json` description: "AI Factory WhatsApp Onboarding System" → jenerik
- Tüm `tests/*.js` dosyalarındaki kişisel test fixture'ları temizlendi: gerçek
  isim/soyisim, gerçek Railway domain'i, gerçek WA telefon numarası, gerçek
  Notion DB ID, kişisel e-posta adresleri →
  placeholder veya `process.env` referansı
- `README.md` baştan yazıldı: kişisel GitHub repo URL'si, Railway
  project/service ID'leri, gerçek domain, marka referansları çıkarıldı
- `.gitignore` sadeleştirildi (silinen dosyalara referanslar kaldırıldı)
- **Silinen dosyalar:**
  - `samples.json` — gerçek üye PII içeren Notion API response dump'ı (isim, e-posta,
    page/user ID'leri)
  - `schema.json` — owner'ın Notion DB şema dump'ı (DB ID, user ID, option ID'leri)
  - `mcp_files.json` — owner repo-bundle artefaktı, içinde gömülü `.env` içeriği
  - `antigravity_whatsapp_onboarding_v2.md` — owner'ın kişisel referanslı spec dökümanı
  - `eski_uyeler.csv` / `Eski Onboarding Workflow*.json` — gerçek üye verisi
  - `import_old_users.js` — owner'a özel CSV migration scripti
  - `tests/legacy-scripts/` — owner'ın GitHub push tooling'i (repo adı + hardcoded IP)
  - `tests/check_railway.py` — canlı Railway token içeriyordu
  - `tests/scratch_*.js`, `tests/test_volkan.js` — gerçek isimlerle owner scratch dosyaları

## Öğrenci ne yapmalı

1. `.env.example` → `.env` kopyalayın, tüm `<...>` placeholder'ları doldurun
   (Notion, ManyChat token + 7 flow ID + 2 field ID, Groq, Resend, WA telefon,
   webhook secret)
2. Notion'da bir onboarding takip database'i oluşturun. Gerekli property'ler:
   `İsim`, `Soyisim`, `Email`, `Telefon`, `Uye ID`, `Kayıt Tarihi`,
   `Onboarding Durumu` (select), `Onboarding Kanalı` (select), `Onboarding Adımı`
   (number), `Onboarding Başlangıcı` (date)
3. ManyChat'te 7 günlük drip için 7 flow oluşturun, ID'lerini `.env`'e girin
4. `services/resend.js` içindeki `[KÖŞELİ PARANTEZ]` alanlarını doldurun:
   topluluk adı, topluluk/içerik/plan URL'leri, 7 günün video ve thumbnail linkleri
5. `npm install && npm run dev` ile çalıştırın

## Mod C — Orijinal amaç → yeni jenerik çerçeve

**Orijinal:** Belirli bir topluluğun (Skool tabanlı) yeni üyelerine 7 gün boyunca
WhatsApp'tan kendi onboarding videolarını gönderen production servisi — owner'ın
ManyChat flow'ları, kendi Notion CRM'i, kendi e-posta drip içeriği, kendi Railway
deployment'ı ve kendi GitHub standalone repo'suyla çalışan canlı sistem.

**Yeni çerçeve:** Herhangi bir topluluk veya markanın kullanabileceği genel amaçlı
7 günlük WhatsApp drip-onboarding sistemi. Değerli mimari desenler korundu: webhook
fail-secure auth, Notion-backed idempotency lock, 429 backoff, hibrit WhatsApp+email
fallback, telefon validasyonu, KVKK PII masking, graceful shutdown. Owner'a özel her
şey (ManyChat flow ID'leri, Notion DB, e-posta içeriği, video linkleri, deployment
bilgileri) env değişkenlerine veya şablon alanlara taşındı; öğrenci kendi içeriğini
bağlayarak kendi onboarding sistemini çalıştırır.
