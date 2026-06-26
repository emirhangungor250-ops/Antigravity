# _PAYLASIM_NOTU

**Mod:** C (Şablona çevrilmiş)

## Ne yapıldı

- Sahibin niş kreatör listesi, kişisel Notion DB ID'leri, Drive klasör ID'si placeholder'a dönüştürüldü.
- README baştan yazıldı (jenerik niş içerik pipeline tanımı).
- `core/sanitize.py` içindeki marka tanıtım kelime listesi boşaltıldı.
- `.env.example` üzerinden gerekli anahtarlar dökümante edildi.
- HandOver ve internal proposal dokümanları çıkarıldı.

## Öğrenci ne yapmalı

1. `.env.example` → `.env`, anahtarları doldur.
2. `scripts/build_style_corpus.py` ile kendi stil corpus'unu Supabase'e seed et.
3. `core/sanitize.py` içindeki `BRAND_PROMO_PHRASES` ve `BANNED_DOMAINS`'i kendi markana göre doldur.
4. Notion'da hedef DB'ni oluştur, property şemasını `core/notion_writer.py` ile eşleştir.
5. Google Drive klasörünü oluştur, OAuth refresh token al, klasör ID'sini `.env`'e koy.
6. `tests/test_smoke.py` ile 8 servis sağlık kontrolünü çalıştır.
7. `python -m scripts.run_single <REEL_URL>` ile ilk koşumu yap.

## Orijinal amaç → yeni çerçeve

Orijinal proje, sahibinin 7+ İngilizce AI içerik üreticisi Reels'larını izleyip
kendi tonunda Türkçe scripte çeviren bir lokalizasyon pipeline'ıydı. Pattern
(8 stage: download → transcribe → correct → topic proposal → style retrieval
→ script generation → asset research → Drive brief + Notion card) korundu.
Sahibin niş kreatör listesi, kişisel Notion DB'si, sanitize kuralları
çıkarıldı. Öğrenci pattern'i kendi nişine uyarlar.
