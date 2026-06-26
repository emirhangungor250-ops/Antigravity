# Paylaşım Notu — Akıllı Watchdog

**Mod:** C (şablona çevrildi)

## Ne yapıldı
- **Temizlenen sırlar:** Kodda gömülü sır bulunmadı (sırlar zaten `.env` içinde).
- **Scrub edilen kişisel veriler:**
  - `config.py` içindeki 20+ Railway service ID + Notion DB ID envanteri (tüm aktif ekosistem listesi) tamamen kaldırıldı
  - Sahibin e-posta adresi (`ALERT_EMAIL` default'u + `alerter.py` From başlığı) placeholder'a çevrildi
  - README'deki izlenen proje isimleri, cloud routine trigger ID'si, kişisel env var listesi temizlendi
  - `railway_log_checker.py` içindeki proje-adı yorumu jenerikleştirildi

## Öğrenci ne yapmalı
1. `.env.example`'ı `.env` olarak kopyala, anahtarları doldur: `GROQ_API_KEY`, `ALERT_EMAIL`, `NOTION_API_TOKEN`, `RAILWAY_TOKEN`.
2. `config.py` → `MONITORED_PROJECTS` listesindeki iki örnek satırı kendi projelerinle değiştir/çoğalt. Her satır için Notion DB ID + Railway service ID gir.
3. Gmail API OAuth2 token'ını `GOOGLE_OUTREACH_TOKEN_JSON`'a (veya Service Account JSON'a) yerleştir.

## Orijinal amaç → yeni jenerik çerçeve
- **Orijinal:** Sahibin ~20 production cron/servisini izleyen, hardcoded ID envanteriyle gelen kişisel watchdog.
- **Yeni:** Birden fazla otomasyon/cron çalıştıran herkes için jenerik sağlık-izleme iskeleti. İzlenecek servisler config'te boş örnek satır olarak bırakıldı; pattern (2 katmanlı kontrol + LLM şema-kayması analizi + sessiz inbox label'lama) korundu.
