# İşletme WhatsApp Asistan — API Anahtarları Rehberi

Bu asistan 5 farklı servise bağlı: ManyChat (WhatsApp köprüsü), OpenAI (LLM + embedding), Groq (intent + ses), Supabase (veritabanı + bilgi tabanı), Resend (e-posta). Aşağıda her birinin nereden alınacağı, yaklaşık aylık maliyeti ve nasıl bağlanacağı yazıyor.

---

## 1. ManyChat (WhatsApp ↔ Bot köprüsü)

**Ne işe yarar:** WhatsApp'a gelen mesajları botun webhook'una yollar, botun cevabını WhatsApp'a iletir. Resmi WhatsApp Business API'sini ManyChat üzerinden kullanırsınız.

**Adımlar:**
1. https://manychat.partnerlinks.io/9vfoe2mjua3j-ogcg6e → kayıt ol → WhatsApp kanalını seç
2. Meta Business Manager bağla → kendi işletme telefon numaranızı onaylat
3. **Sol menü → Settings → API → Generate API Token** → bunu `MANYCHAT_API_TOKEN`'a yaz
4. Bir flow oluştur (asistanın cevabını yollayacak flow), ID'sini al → `MANYCHAT_FLOW_ID`
5. Custom field oluştur (cevap metni), ID'sini al → `MANYCHAT_FIELD_ID`
6. External Request action ekle → bu projenin webhook URL'i: `https://<railway-url>/webhook/message`
7. External Request'te custom header'a `x-webhook-secret: <WHATSAPP_WEBHOOK_SECRET>` koy

**Maliyet:** ManyChat Pro ~$15/ay başlangıç. WhatsApp Business API mesaj başına servis ücreti var (Meta, kategoriye göre ~$0.005-0.05).

---

## 2. OpenAI (ana LLM + embedding)

**Ne işe yarar:** Cevapları üretir (gpt-4.1-mini), bilgi tabanı için embedding üretir (text-embedding-3-small).

**Adımlar:**
1. https://platform.openai.com → kayıt ol → faturalama bilgisi gir
2. **API Keys** → "Create new secret key" → `OPENAI_API_KEY`'e yaz
3. Hesaba minimum $10 kredi yükle

**Maliyet (orta yoğunlukta):** Aylık $5-30. Yoğun kullanımda $50+.

---

## 3. Groq (KVKK intent + ses transkripsiyon)

**Ne işe yarar:** KVKK "onaylıyorum/evet/tamam" gibi mesajları analiz eder (llama-3.3-70b), sesli mesajları yazıya çevirir (whisper).

**Adımlar:**
1. https://console.groq.com → kayıt ol
2. **API Keys** → "Create API Key" → `GROQ_API_KEY`'e yaz

**Maliyet:** Şu an ücretsiz tier var (günlük limitler içinde). Yoğun kullanımda ~$5-10/ay.

---

## 4. Supabase (veritabanı + bilgi tabanı)

**Ne işe yarar:** Müşteri kayıtları (KVKK onayı, telefon), konuşma geçmişi (son 20 mesaj), bilgi tabanı (RAG için embedding'li chunk'lar).

**Adımlar:**
1. https://supabase.com → kayıt ol → "New Project"
2. Proje adı: istediğiniz bir ad (region: Frankfurt veya Ireland önerilir)
3. Database password belirle (kaydet, sonra lazım)
4. Proje açıldıktan sonra: **Project Settings → API**
   - `Project URL` → `SUPABASE_URL`
   - `service_role` (secret) → `SUPABASE_SERVICE_ROLE_KEY`
5. **SQL Editor → New Query** → `supabase_setup.sql` dosyasının içeriğini yapıştır → "Run"
6. Tablolar oluştu mu kontrol: **Table Editor**'da `subscribers`, `conversations`, `knowledge_chunks` görünmeli

**Maliyet:** Ücretsiz tier 500MB DB ve 2GB bandwidth verir. Bu projeye yıllarca yeter.

---

## 5. Resend (eskalasyon e-postası)

**Ne işe yarar:** Asistan bir konuyu satış/destek ekibine eskale ettiğinde mail gönderir.

**Adımlar:**
1. https://resend.com → kayıt ol
2. **Domains → Add Domain** → kendi domaininizi ekle → DNS kayıtlarını doğrula (SPF, DKIM)
3. **API Keys → Create API Key** → `RESEND_API_KEY`'e yaz
4. `.env`'de `RESEND_FROM_EMAIL=asistan@<kendi-domaininiz>` ayarla (domain doğrulandıysa istediğin alt-adres olabilir)

**Maliyet:** Ücretsiz tier ayda 3.000 mail. Bu projeye fazlasıyla yeter.

---

## 6. Webhook güvenlik şifreleri (kendin üret)

`WHATSAPP_WEBHOOK_SECRET` ve `ADMIN_SECRET` için rastgele 32 karakter üret:

```bash
openssl rand -hex 32
```

Bu komutu iki kez çalıştır, çıkanları `.env`'e yapıştır. ManyChat External Request action'da `x-webhook-secret: <WHATSAPP_WEBHOOK_SECRET>` header'ı ekle.

---

## Tahmini Aylık Toplam Maliyet

| Servis | Aylık |
|---|---|
| ManyChat Pro | $15 |
| OpenAI (orta) | $10-30 |
| Groq | $0-10 |
| Supabase | $0 (ücretsiz tier) |
| Resend | $0 (ücretsiz tier) |
| Railway (hosting) | $5-10 |
| **Toplam** | **~$30-65/ay** |

WhatsApp mesaj ücretleri Meta tarafından ayrı faturalanır (volume'a göre $10-100+/ay).
