# _PAYLASIM_NOTU

**Mod:** C (Şablona çevrilmiş)

## Ne yapıldı

- Marka-spesifik refuse mesajları, escalation hedefleri ve product card variant'ları placeholder'a indirildi.
- `ai_engine.js`'in heavy system prompt'u `prompts/system_prompt.md` şablonuna taşındı.
- `intent_router.js` içindeki marka-özel intent açıklamaları jenerikleştirildi.
- `kb_factory.js`'te `SOURCE = 'main'` (kendi KB source adınızla değiştirin).
- `escalation.js` hedef adresi `<ADMIN_EMAIL>` üzerinden okunur.
- Sahibin Notion video DB ID'si `<NOTION_DB_ID>` placeholder'ına dönüştürüldü.
- LLM testleri (`simulation_scenarios.js`) ve handover dokümanları çıkarıldı.

## Öğrenci ne yapmalı

1. `.env.example`'ı `.env` olarak kopyala, anahtarları doldur.
2. `prompts/system_prompt.md` içindeki `[KÖŞELİ PARANTEZ]` alanlarını kendi markana göre yaz.
3. `services/intent_router.js` içindeki intent listesini ve `CHEAP_SYSTEM` prompt'unu kendi senaryolarına uyarla.
4. `services/kb_factory.js` içindeki `SOURCE` değerini kendi KB source adınla değiştir.
5. `utils/sanitize.js` içindeki `BANNED_AMOUNTS`, `BANNED_PHRASES`, `HARD_FALLBACKS`'ı kendi politikana göre düzenle.
6. Kendi marka KB markdown'ını oluştur, seed scripti veya `/admin/seed-kb-factory` endpoint'i ile yükle.
7. Supabase migration'ı uygula: `supabase/migrations/20260517000000_init_instagram_asistan.sql`.
8. ManyChat Instagram channel flow'unu kur (README'de detay).

## Orijinal amaç → yeni çerçeve

Orijinal proje, sahibinin Instagram DM'lerini AI Factory topluluğunun
müşteri danışma akışına bağlayan bir RAG botuydu. Pattern (rate limit
+ burst coalesce + cheap-then-deep router + RAG-A/RAG-B + sanitize +
escalation) korundu. Marka-spesifik içerikler (Skool URL'leri, paket
fiyatları, üye başarı hikayeleri, jotform formu) tamamen kaldırıldı.
Öğrenci pattern'i alıp kendi markası için doldurur.
