# Paylaşım Notu — Whatsapp_Asistan

## Mod
C — Şablona çevir

## Ne yapıldı

### Temizlenen sırlar
- Koda gömülü API anahtarı bulunmadı — tüm anahtarlar `config/env.js` üzerinden
  `process.env`'den okunuyor.
- `.env.example` içindeki gerçek değerler temizlendi: ManyChat field/flow ID'leri,
  gerçek Supabase URL → `<...>` placeholder'lar.

### Scrub edilen kişisel veriler
- `config/env.js`: escalation email default'u kişisel kurumsal e-postadan `escalation@example.com` placeholder'ina cevrildi
- `server.js`: KVKK mesajındaki marka sahibi adı → `[MARKA ADI]`; kişisel KVKK
  URL'si → `KVKK_URL` env değişkeni; onboarding buton
  etiketleri (AI Factory'ye Git vb.) → `[ÜRÜN BUTONU N]`; hoş geldin mesajındaki
  "AI Factory" → `[MARKA/ÜRÜN ADI]`; KB dosya adı → `bilgi-tabani.md`
- `services/ai_engine.js`: **tamamen şablona çevrildi.** Owner'a özel hardcoded
  system prompt (~290 satır AI Factory / Dolunay / Skool / Jotform / JoinSecret
  içeriği) `prompts/system_prompt.md` adlı genel şablon dosyaya taşındı; kod artık
  şablonu okuyup `{{DETECTED_LANGUAGE}}`, `{{TODAY_DATE}}`, `{{RAG_CHUNKS}}`
  placeholder'larını dolduruyor. Eskalasyon tool adı `escalate_to_dolunay` →
  `escalate_to_human`. Sanitizer'daki owner'a özel yasak rakamlar ve hard fallback
  cevapları (Skool URL'leri, Jotform, JoinSecret, "Ece" ismi) jenerikleştirildi /
  boşaltıldı, TODO yorumlarıyla işaretlendi
- `services/knowledge_base.js`: pinning keyword listelerinden kişisel referanslar
  (`meltem`, `dolunay`, `classroom`, `antigravity`, `n8n`) temizlendi; section
  numaraları TODO yorumuyla "kendi KB yapınla değiştir" olarak işaretlendi
- `scripts/extract_escalations.js`: kişisel kurumsal e-posta referansı + sahibe
  özel "iletiyorum" pattern'ları jenerikleştirildi
- `package.json` description: "AI Factory WhatsApp Asistanı" → jenerik
- `scripts/test_burst_coalesce.js`: gerçek Railway servis URL'si → placeholder
- `Asistanin_Yol_Haritasi.md`: owner'ın konuşma playbook'u (Dolunay/AI Factory/
  classroom/Jotform/fiyatlar) → genel konuşma-tasarımı rehberi şablonu
- **Silinen dosyalar:** owner'ın gerçek bilgi tabanı dosyaları
  (`ai-factory-asistan-bilgi-tabani-v5/v6/v7.md` — 170KB içerik), classroom
  listesi, `_arsiv/` eski KB sürümleri, handover/devir/faz notları, audit ve
  simülasyon HTML raporları, owner'ın WhatsApp flow JSON export'u

### Eklenen / şablona indirilen dosyalar
- `prompts/system_prompt.md` — genel sistem prompt şablonu (owner içeriği yok)
- `bilgi-tabani.md` — boş KB şablonu, bölüm yapısı açıklamalı
- `scripts/simulation_scenarios.js` — 30 owner senaryosu → 4 jenerik örnek senaryo
- `scripts/test_conversation.js` — owner senaryoları → 3 jenerik placeholder senaryo
- `.env.example` — placeholder'lı, KVKK_URL eklendi

## Öğrenci ne yapmalı

1. `.env.example` → `.env` kopyalayın, tüm `<...>` placeholder'ları doldurun
   (OpenAI, Groq, Supabase, ManyChat, Resend anahtarları + KVKK_URL)
2. Supabase tablolarını oluşturun: `supabase_setup.sql`
3. `prompts/system_prompt.md` içindeki `[KÖŞELİ PARANTEZ]` alanlarını kendi
   markanız, ürünleriniz ve kurallarınızla doldurun
4. `bilgi-tabani.md` dosyasını kendi bilgi tabanınızla doldurun (markanız, SSS,
   paketler, eskalasyon politikası)
5. `server.js` içindeki KVKK mesajı, hoş geldin mesajı ve onboarding buton
   etiketlerini güncelleyin
6. `services/ai_engine.js` içindeki `BANNED_AMOUNTS`, `BANNED_PHRASES` ve hard
   fallback cevaplarını kendi marka kurallarınızla doldurun (`TODO:` yorumları)
7. `services/knowledge_base.js` pinning keyword'lerini ve section numaralarını
   kendi KB yapınıza göre güncelleyin
8. `scripts/simulation_scenarios.js` ve `test_conversation.js` test senaryolarını
   doldurun
9. `node scripts/seed_knowledge.js` ile KB'yi embed edin, sonra `npm start`

## Mod C — Orijinal amaç → yeni jenerik çerçeve

**Orijinal:** Belirli bir topluluğun WhatsApp satış/destek hattı — owner'ın kendi
bilgi tabanı, kendi fiyatları, kendi classroom haritası, kendi ekip kuralları ve
kendi eskalasyon e-postasıyla çalışan canlı production botu.

**Yeni çerçeve:** Herhangi bir markanın kullanabileceği genel amaçlı, ManyChat
tabanlı WhatsApp RAG asistanı iskeleti. Değerli mimari desenler korundu: KVKK onay
akışı, semantic search + keyword pinning, tool tabanlı eskalasyon, post-process
sanitizer + retry, burst coalesce, çoklu-turn simülasyon framework'ü. Owner'a özel
her şey (bilgi tabanı, system prompt içeriği, fiyatlar, marka stringleri, test
senaryoları) şablona indirildi; öğrenci kendi içeriğini doldurarak kendi botunu
çıkarır.
