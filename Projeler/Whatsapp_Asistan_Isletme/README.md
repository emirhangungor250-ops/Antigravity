# İşletme WhatsApp Asistanı

İşletmenizin WhatsApp hattına gelen müşteri mesajlarını yapay zeka ile yanıtlayan, ManyChat üzerinden çalışan RAG tabanlı asistan. Villa kiralama, otel, emlak, e-ticaret gibi her sektöre uyarlanabilir; tüm işletme bilgisi `bilgi-tabani-v1.md` dosyasından gelir.

## Asistanın işi

1. **Açılış keşfi** — müşterinin ihtiyacını anlamak için kısa sorular sorar
2. **Profil eşleştirmesi** — müşteri profilini tespit eder
3. **Öneri** — bilgi tabanındaki uygun ürün/hizmetleri sunar
4. **Eskalasyon** — satış/destek talebi netleştiğinde `ESCALATION_EMAIL` adresine mail atar; ekip devralır

## Mimari katmanlar

| Katman | Görev | Dosya |
|---|---|---|
| Webhook handler | ManyChat'ten gelen mesaj, KVKK akışı, idempotency, burst coalesce | `server.js` |
| Intent classifier | KVKK onay niyeti (Groq llama-3.3-70b) | `services/intent_classifier.js` |
| Knowledge base / RAG | OpenAI embedding + Supabase pgvector + section pinning | `services/knowledge_base.js` |
| AI engine | System prompt + gpt-4.1-mini + escalate_to_team tool + post-process sanitize | `services/ai_engine.js` |
| Memory | Subscriber + conversation (Supabase) | `services/memory.js` |
| Escalation | Resend ile mail, 30 dk dedup, test guard | `services/escalation.js` |
| Manychat | Custom field set + flow trigger | `services/manychat.js` |
| Transcription | Groq Whisper sesli mesaj | `services/transcription.js` |
| Language detector | TR/EN/DE/RU vs. otomatik dil tespiti | `services/language_detector.js` |

## Bilgi tabanı (KB)

İşletmenizin **ürün/hizmet kataloğu + politikalar + SSS** bilgisi `bilgi-tabani-v1.md` dosyasına yazılır. Bu dosya markdown başlıklarına göre chunk'lara bölünür, OpenAI embedding'i çıkarılır, Supabase'e yüklenir.

**Section numaralandırma (önemli — pinning bunu kullanır):**
- `0.x` — Rol ve konuşma akışı (her sorguda zorunlu pinli)
- `1.x` — Şirket bilgileri
- `2.x` — Bölge / kategori
- `3.x` — Ürün / hizmet kategorileri
- `4.x` — Ödeme, iptal, iade politikaları
- `5.x` — SSS
- `6.x` — İletişim
- `7.x` — Operasyonel (ek hizmetler)

Section numaralarını değiştirmeyin; sadece içeriği doldurun. Kendi sektörünüz için `services/knowledge_base.js` içindeki keyword listelerini de uyarlayın.

**Reseed:** `node scripts/seed_knowledge.js` (eski chunk'ları siler, KB'yi yeniden embed eder).

## Kurulum

1. **`.env` oluştur:** `.env.example`'ı kopyala, anahtarları doldur. Detay: `API_ANAHTARLARI_REHBERI.md`.
2. **Bağımlılıkları kur:** `npm install`
3. **Supabase tabloları:** Supabase SQL Editor'da `supabase_setup.sql`'i çalıştır.
4. **KB'yi seed et:** `bilgi-tabani-v1.md`'yi doldur, sonra `node scripts/seed_knowledge.js`.
5. **Çalıştır:** `npm start` (lokal test için) veya Railway'e deploy et.

## Deploy (Railway)

- Builder: `RAILPACK`, Root directory: monorepo içindeyse proje klasörü dolu olmalı.
- Tüm `.env` değişkenlerini Railway → Variables sekmesine kopyala.
- Health check: `/health`.

## Sanitize (post-process)

`services/ai_engine.js` cevap dönmeden önce şunları kontrol eder:
- **Em-dash (—)** yasak.
- **Sahte kampanya/indirim** yasak.
- **Sahte satış/rezervasyon onayı** yasak.
- **İletim cümlesi tool çağrısı olmadan** yasak.

İhlal varsa LLM bir kez retry'a çağrılır. İkinci turda ihlal sürerse hard-fallback sabit cevap döner ve admin log'a alarm düşer.

## Test

- **Lokal sohbet:** `npm run dev` → ManyChat webhook'u localhost'a çevir (ngrok) → WhatsApp'tan test mesajı at.
- **KB kontrol:** `npm run kb:list`, `npm run kb:search <kelime>`.

## Bakım

- KB güncellendikçe reseed çalıştır (`npm run seed`).
- Sanitize alarmları Railway loglarında görünür. Yeni edge case'ler çıkarsa `services/ai_engine.js` içindeki yasak listesine ekle.
- 30 dakikalık eskalasyon dedup süresini değiştirmek istersen: `services/escalation.js` → `ESCALATION_DEDUP_WINDOW_MS`.
