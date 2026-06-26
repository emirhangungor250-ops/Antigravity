# Paylaşım Notu — Proje Dashboard

**Mod:** C (şablona çevrildi)
**Orijinal klasör adı:** `Patron_Dashboard`

## Ne yapıldı
- **Temizlenen sırlar:** Kodda gömülü API anahtarı yok (tüm collector'lar env-driven).
- **Scrub edilen kişisel veriler:**
  - `config/projects.yaml` — sahibin ~19 Railway servisi + project ID envanteri (gerçek UUID'ler) tamamen kaldırıldı → 2 örnek placeholder satır
  - `config/subscriptions.yaml` — sahibin gerçek aylık abonelik + harcama kalemleri kaldırıldı → örnek satırlar (monthly_usd: 0)
  - `config/ignored_signals.yaml` — sahibin proje adları kaldırıldı → 2 örnek satır
  - `collectors/notion_collector.py` — sahibin 9 kişisel Notion DB'sinin label + metrik konfigürasyonu (`db_specs`, `PATRON_METRICS`) → `DB_SPECS` + `DB_METRICS` jenerik yapılarına çevrildi, 2 örnek bırakıldı, TODO yorumu eklendi
  - `collectors/signals.py` — `Patron_Dashboard` self-referansı `Proje_Dashboard`'a güncellendi
  - `launchagent/*.plist` — sahibin kişisel mutlak dosya yolları `<PROJE_YOLU>` placeholder'ına; dosya `com.proje-dashboard.plist` olarak yeniden adlandırıldı
  - `mockups/*.html` — design draft'larındaki ~14 kişisel servis adı + sahibin adı jenerik örnek adlara çevrildi
  - `run.py`, `render/template.html` — "Patron dashboardumda" / "Patron Dashboard" / "Antigravity ekosistemi" ifadeleri jenerikleştirildi
  - `data/state.json` (76KB üretilmiş snapshot, sahibin tüm filo verisi) + `patron-dashboard.html` (üretilmiş render) silindi — bunlar her run'da yeniden oluşur

## Öğrenci ne yapmalı
1. `.env.example`'ı `.env` olarak kopyala; en az `RAILWAY_TOKEN` ve `NOTION_SOCIAL_TOKEN` doldur. Maliyet collector'ları opsiyonel.
2. `config/projects.yaml` → 2 örnek satırı kendi Railway servislerinle değiştir (service ID + project ID Railway panelinden).
3. `config/subscriptions.yaml` → kendi abonelik/harcama kalemlerini gir.
4. `collectors/notion_collector.py` → `DB_SPECS` ve `DB_METRICS`'e izlemek istediğin Notion DB'lerini ekle; karşılık gelen DB ID env var'larını `.env`'e yaz.
5. LaunchAgent kuracaksan `launchagent/com.proje-dashboard.plist` içindeki `<PROJE_YOLU>` placeholder'larını kendi mutlak yolunla değiştir.

## Orijinal amaç → yeni jenerik çerçeve
- **Orijinal:** Sahibin ~19 production servisini, 9 kişisel Notion DB'sini ve gerçek aylık harcamasını gösteren, tüm infra envanteri hardcoded gelen kişisel "patron panosu".
- **Yeni:** Çok-projeli bir filo çalıştıran herkes için jenerik sağlık + maliyet + bekleyen-iş panosu. İzlenecek servisler, DB'ler ve abonelikler tamamen config-driven; collector mimarisi, 5-sekmeli render ve "bekleyen iş → brief kopyala" pattern'i korundu.
