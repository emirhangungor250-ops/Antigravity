# Paylaşım Notu — Personel Mail Hatırlatıcı

**Mod:** C (şablona çevrildi)

## Orijinal amaç → yeni jenerik çerçeve

Orijinal proje, belirli bir kişinin marka işbirliği e-postalarını takip eden,
ona özel hatırlatma gönderen bir bottu. Yeni çerçeve: **herhangi bir personelin
gelen kutusunu tarayıp geciken iş thread'lerine hatırlatma atan jenerik bot.**
Çekirdek desen (stale thread detection + LLM sınıflandırma + Notion state +
digest mail) aynen korundu; tüm kişiye/markaya özel kabuk çıkarıldı.

## Yapılan temizlik

### Kişisel veri scrub
- İzlenen hesap adı (kişiye özel e-posta) → `STAFF_EMAIL` env var'ı
- Rapor alıcısı (kişisel Gmail adresi) → `ALERT_EMAIL` env var'ı, `admin@example.com` placeholder
- Tüm `Ceren` / `Dolunay` isim referansları → "personel" / "karşı taraf" jenerik rolleri
- GitHub repo URL'i ve Railway root-dir referansları README'den çıkarıldı
- LLM prompt'undaki kişiye özel bağlam jenerikleştirildi

### Sırlar
- Koda gömülü sır bulunmadı (sırlar zaten `.env` / `credentials.json`'da, kopyalanmadı)
- `.env` (gerçek) ve `__pycache__` kopyalanmadı

### Owner-specific schema bindings → env/config
- Notion thread DB id (`NOTION_DB_CEREN_COLLAB_THREADS`) → `NOTION_DB_THREADS`
- Notion token (`NOTION_SOCIAL_TOKEN`/`NOTION_API_TOKEN`) → `NOTION_TOKEN`
- Pipeline DB id ve sahibin içerik-pipeline status listesi → `NOTION_DB_PIPELINE` +
  `PIPELINE_TARGET_STATUSES` env var'ları (jenerik default'larla)
- Sahibe özel "sadece reels/youtube ikonlu kart" filtresi tamamen kaldırıldı
- Sahibe özel Notion kolon adı (`"Collab, #, @, vs."`) → `PIPELINE_COLLAB_PROP` env var'ı
- `core/decision.py` ve testlerdeki `responded_by_ceren` → `responded_by_staff`

## Öğrenci ne yapmalı

1. `.env.example` → `.env` kopyala, doldur:
   - `STAFF_EMAIL` — izlenecek gelen kutusu
   - `GROQ_API_KEY` — Groq API anahtarı
   - `NOTION_TOKEN` + `NOTION_DB_THREADS` — thread state DB'si
   - `GMAIL_TOKEN_JSON` — Gmail OAuth token (kendi OAuth akışınla üret)
   - `ALERT_EMAIL` — digest'in gideceği adres
2. **LLM sınıflandırma mantığı:** `core/thread_analyzer.py` içindeki `SYSTEM_PROMPT`'u
   kendi senaryona göre değiştir (kategoriler, örnekler). Kategori ENUM adlarını
   değiştirirsen `core/decision.py` → `COLLAB_CATEGORIES` setini de güncelle.
3. **Notion şeması:** `services/notion_threads.py` başındaki nottaki property
   adlarıyla bir Notion DB oluştur (veya kod içindeki adları kendi DB'ne uyarla).
4. **Pipeline entegrasyonu opsiyonel:** İstemiyorsan `NOTION_DB_PIPELINE`'ı boş bırak.
5. **Buton webhook'u opsiyonel:** Mute/snooze butonlarını istiyorsan
   `webhook_server.py`'yi ayrı bir servis olarak deploy et, `WEBHOOK_BASE_URL` +
   `BUTTON_HMAC_SECRET` doldur.
