# Paylaşım Notu — Whatsapp_Asistan_Isletme

## Mod
B — Bilgi tabanı içeriğini öğrenci koyar.

## Ne yapıldı
- **Sırlar:** Kaynakta koda gömülü API anahtarı bulunmadı (tüm anahtarlar `.env` üzerinden, `.env` kopyalanmadı). Webhook/admin şifre placeholder'ları boş bırakıldı.
- **Kişisel / marka verisi temizliği:**
  - Klasör adı işletme markası içeren addan `Whatsapp_Asistan_Isletme` olarak jenerikleştirildi.
  - İşletme marka adı tüm dosyalardan kaldırıldı; yerine `BUSINESS_NAME` env değişkeni eklendi (`config/env.js`, `server.js`, `services/ai_engine.js`, `services/escalation.js`).
  - Hardcoded gerçek telefon numaraları, e-posta adresleri, ofis adresi ve işletme domaini → kaldırıldı / placeholder'a çevrildi.
  - System prompt'taki sabit iletişim bilgileri bloğu kaldırıldı; artık iletişim bilgisi bilgi tabanından (KB) okunuyor.
  - KB dosyası marka adı içeren addan `bilgi-tabani-v1.md` olarak yeniden adlandırıldı; tüm referanslar güncellendi.
  - `package.json` adı/açıklaması jenerikleştirildi.
  - README + API_ANAHTARLARI_REHBERI baştan jenerik yazıldı.
- **İçerik şablona indirildi:**
  - `bilgi-tabani-v1.md` — işletmenin gerçek villa kataloğu, fiyatları, iletişim bilgileri tamamen silindi; yapı (section numaraları 0-7) korundu, her bölüme "Buraya kendi bilgi tabanınızı yazın" placeholder'ı kondu. Villa kiralama örneği iskelet olarak bırakıldı.

## Öğrenci ne yapmalı

### 1. Bilgi tabanını doldur (en önemli adım)
`bilgi-tabani-v1.md` dosyasını kendi işletmenizin bilgileriyle doldurun: şirket bilgileri, ürün/hizmet kataloğu, fiyatlandırma, ödeme/iptal politikaları, SSS, iletişim. Section numaralarını (`## 0.1`, `## 1.1` ...) DEĞİŞTİRMEYİN — `services/knowledge_base.js` pinning bunları kullanır.

Sektörünüz villa kiralama değilse `services/knowledge_base.js` içindeki keyword listelerini (`PRICING_KEYWORDS`, `POLICY_KEYWORDS`, `VILLA_KEYWORDS`, `REGION_KEYWORDS`) kendi terimlerinizle güncelleyin.

### 2. `.env` değişkenlerini doldur
`.env.example`'ı `.env` olarak kopyalayın. Doldurulması gerekenler:
- `BUSINESS_NAME`, `BUSINESS_SECTOR` — işletme adı ve sektörü
- `MANYCHAT_API_TOKEN`, `MANYCHAT_FIELD_ID`, `MANYCHAT_FLOW_ID`
- `OPENAI_API_KEY`, `GROQ_API_KEY`
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `ESCALATION_EMAIL`, `ADMIN_NOTIFY_EMAIL`
- `WHATSAPP_WEBHOOK_SECRET`, `ADMIN_SECRET` (`openssl rand -hex 32` ile üretin)
- `KVKK_URL` — kendi KVKK metni linkiniz

Detaylı kurulum: `API_ANAHTARLARI_REHBERI.md`.

### 3. Seed + deploy
Supabase tablolarını `supabase_setup.sql` ile kur, `node scripts/seed_knowledge.js` ile KB'yi embed et, sonra çalıştır.
