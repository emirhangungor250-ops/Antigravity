# Whatsapp_Asistan

ManyChat üzerinden çalışan, WhatsApp hattında gelen müşteri mesajlarını yapay zeka
ile yanıtlayan RAG tabanlı asistan. Bu bir **şablondur**: bilgi tabanı, sistem
prompt'u ve marka kuralları boş gelir; kendi içeriğinizle doldurursunuz.

## Özellikler

- KVKK onay akışı (LLM tabanlı akıllı niyet tespiti, Groq)
- ManyChat entegrasyonu (custom fields, flow triggering)
- OpenAI gpt-4.1-mini yanıt motoru + tool çağrısı (eskalasyon)
- Sesli mesaj desteği (Groq Whisper transkript)
- RAG bilgi tabanı (Supabase pgvector, text-embedding-3-small)
- Otomatik dil tespiti (Türkçe, İngilizce, Almanca vb.)
- Supabase conversation memory (son 20 mesaj)
- Post-process sanitize + retry (yasak rakam/ifade/em-dash filtresi)
- Eskalasyon e-postası (Resend API)
- Burst coalesce (kısa aralıkla gelen mesajları tek cevapta birleştirme)
- Simülasyon test framework'ü

## Mimari Katmanlar

| Katman | Görev | Dosya |
|---|---|---|
| Webhook handler | ManyChat mesajını al, dedup, history kaydet | `server.js` |
| Intent classifier | KVKK onay niyeti tespiti (Groq) | `services/intent_classifier.js` |
| Knowledge base / RAG | Embedding sorgu + section bazlı pinning | `services/knowledge_base.js` |
| AI engine | System prompt + GPT-4.1-mini + tool çağrısı + sanitize | `services/ai_engine.js` |
| Memory | Subscriber + conversation tablosu (Supabase) | `services/memory.js` |
| Escalation | Resend ile mail, 30 dk dedup, test guard | `services/escalation.js` |
| Manychat | Custom field + flow trigger | `services/manychat.js` |
| Transcription | Groq Whisper ses mesajı transkript | `services/transcription.js` |
| Language detector | Mesaj dilini tespit | `services/language_detector.js` |

## Doldurmanız Gereken Şablon Dosyalar

Bu proje, asistanin **davranisini** ve **bilgisini** sizden bekler:

| Dosya | Ne yaparsınız |
|---|---|
| `prompts/system_prompt.md` | Asistanin rolü, tonu, kuralları — `[KÖŞELİ PARANTEZ]` alanlarını doldurun |
| `bilgi-tabani.md` | Asistanin bilgi tabanı — markanız, ürünleriniz, SSS |
| `Asistanin_Yol_Haritasi.md` | Konuşma tasarımı rehberi (referans) |
| `server.js` | KVKK mesajı, hoş geldin mesajı, onboarding buton etiketleri |
| `services/ai_engine.js` | Sanitizer: yasak rakamlar, yasak ifadeler, hard fallback cevapları |
| `services/knowledge_base.js` | Pinning keyword'leri + KB section numaraları |
| `scripts/simulation_scenarios.js` ve `scripts/test_conversation.js` | Test senaryoları |

## Post-Process Sanitize

`services/ai_engine.js` cevap return etmeden önce `checkViolations()` çalıştırır:
em-dash, kullanıcı sormadan app linki, sahte indirim, eskalasyon imzası tool olmadan
kullanımı kontrol edilir. `BANNED_AMOUNTS` ve `BANNED_PHRASES` dizilerini kendi
marka kurallarınızla doldurursunuz. İhlal varsa LLM'e bir kez retry; ikinci turda
da ihlal varsa hard fallback / daha temiz olan döner.

## Simülasyon Test Framework'ü

```bash
node scripts/simulate_conversations.js
# tek senaryo: node scripts/simulate_conversations.js --scenario 1
node scripts/test_conversation.js   # scripted regression
```

`simulate_conversations.js` `SIMULATION_MODE='true'` set eder; `escalation.js` bu
modda gerçek mail göndermez. `sim-*` ve `test-runner-*` subscriber ID'leri için de
ek koruma var. Çoklu-turn senaryolar hafıza ve profil-drift bug'larını yakalar.

## Kurulum

1. `npm install`
2. `.env.example` dosyasını `.env` olarak kopyalayın, tüm `<...>` placeholder'ları doldurun
3. Supabase tablolarını oluşturun: `supabase_setup.sql`
4. `prompts/system_prompt.md` ve `bilgi-tabani.md` dosyalarını kendi içeriğinizle doldurun
5. KB'yi seed edin: `node scripts/seed_knowledge.js`
6. `npm start`

## Deploy (Railway)

- Builder: NIXPACKS. `railway.json` ve `nixpacks.toml` hazır gelir.
- Start: `npm run seed && npm start` (her başlangıçta KB reseed edilir).
- KB güncellemesi sonrası reseed gerekir.

## Bakım Kuralları

- KB güncelledikten sonra reseed çalıştır (`node scripts/seed_knowledge.js`).
- Yeni senaryo ekledikten sonra simülasyonu koştur, sıfır ihlal hedefle.
- Eskalasyon kuralı değiştirdiysen test guard'ı doğrula.
- Production logunda `sanitize_violations_persist_after_retry` varsa yeni edge
  case'i system prompt'a ekle.
