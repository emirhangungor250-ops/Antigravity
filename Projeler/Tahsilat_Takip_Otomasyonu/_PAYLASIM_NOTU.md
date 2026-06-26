# Paylaşım Notu — Tahsilat Takip Otomasyonu

**Mod:** C (şablona çevrildi)
**Orijinal klasör adı:** `Isbirligi_Tahsilat_Takip`

## Ne yapıldı
- **Temizlenen sırlar:** Kodda gömülü API anahtarı bulunmadı (hepsi `.env` üzerinden).
- **Scrub edilen kişisel veriler:**
  - `config.py`, `notion_client.py`, `ops_logger.py` içindeki tüm hardcoded Notion DB ID'leri ve parent page slug'ı → `os.getenv()` ile env'e taşındı
  - `email_client.py` içindeki sahibin e-posta adresleri (gönderen + alıcı) → `NOTIFY_EMAIL` env değişkenine
  - `email_client.py` docstring'indeki kişisel hesap referansı temizlendi
  - Sahibe özel Notion property adları (kişisel isim içeren ödeme + içerik alanları) → config'te `PAYMENT_TYPE_PROP` / `CONTENT_RELATION_PROP` env-driven değişkenlere çevrildi, kodda bu değişkenler kullanılıyor
  - `ops_logger.py` docstring'indeki proje-adı referansı jenerikleştirildi
  - README baştan yazıldı; GitHub repo URL'si ve sahibe özel iş birliği çerçevesi kaldırıldı

## Öğrenci ne yapmalı
1. `.env.example`'ı `.env` olarak kopyala; `NOTION_SOCIAL_TOKEN`, `COLLAB_DB_ID`, `TAHSILAT_TAKIP_DB_ID`, `COLLAB_PARENT_SLUG`, `NOTIFY_EMAIL`, `GOOGLE_OUTREACH_TOKEN_JSON` doldur.
2. `PAYMENT_TYPE_PROP`, `PAYMENT_TYPE_SKIP_VALUE`, `CONTENT_RELATION_PROP` değerlerini kendi Notion şemandaki gerçek property adlarıyla eşleştir (`.env` veya `config.py`).
3. Notion entegrasyonunu hem ana DB'ye hem tutar DB'sine bağla.

## Orijinal amaç → yeni jenerik çerçeve
- **Orijinal:** Sahibin sosyal medya marka iş birliklerinde geciken ödemeleri takip eden, Notion'daki kişisel "YouTube/Reels İşbirliği" + "Gelir > Tahsilat Takip" şemasına hardcoded bağlı bot.
- **Yeni:** Notion'da herhangi bir iş/fatura/proje kaydı tutan herkes için jenerik "geciken ödeme tarayıcı". DB ID'leri ve property adları tamamen config-driven; gecikme bandı (14/30/60 gün) + tek toplu mail + read-only join pattern'i korundu.
