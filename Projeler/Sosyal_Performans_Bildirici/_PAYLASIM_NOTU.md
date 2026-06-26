# Paylaşım Notu — Sosyal Performans Bildirici

**Mod:** C (şablona çevrildi)

## Orijinal amaç → yeni jenerik çerçeve

Orijinal proje, belirli bir kişinin sosyal medya hesaplarını tarayıp izlenme
barajını aşan videoları belirli bir ekip üyesine raporlayan bir bottu. Yeni
çerçeve: **herhangi birinin sosyal medya hesaplarını tarayıp eşik üstü içerikleri
raporlayan jenerik bot.** Çekirdek desen (Apify çoklu platform çekimi + baraj
filtresi + dedupe + digest mail) aynen korundu; tüm kişiye özel kabuk çıkarıldı.

## Yapılan temizlik

### Kişisel veri scrub
- `IG_USERNAME`, `TIKTOK_USERNAME`, `YOUTUBE_SEARCH_QUERY`, `YOUTUBE_CHANNEL_KEYWORDS`
  default değerleri (kişisel sosyal handle'lar) → jenerik placeholder'lar
- `REPORT_TO` (ekip üyesinin e-postası) → `report-recipient@example.com`
- `REPORT_FROM` (kişisel isim + e-posta) → jenerik gönderici
- `TECH_ERROR_TO` (kişisel Gmail) → `admin@example.com`
- Tüm kişisel isim referansları kod ve loglardan çıkarıldı
- LLM prompt'undaki kişiye özel hitap jenerikleştirildi
- README'deki GitHub repo + monorepo root-dir referansları çıkarıldı

### Sırlar
- Koda gömülü sır bulunmadı (sırlar `.env` / `credentials.json` / `token.json`'da, kopyalanmadı)
- Gmail OAuth token yolu sahibin merkezi credential dizinini gösteriyordu →
  `data/gmail-token.json` lokal yoluna çevrildi
- `ops_logger.py`'de hardcoded Notion ops-log DB id'si vardı → kaldırıldı,
  artık tamamen `NOTION_DB_OPS_LOG` env var'ından okunuyor (boşsa Notion'a yazmaz)

### Owner-specific schema bindings → env/config
- Notion token (`NOTION_SOCIAL_TOKEN`/`NOTION_API_TOKEN`) → `NOTION_TOKEN`
  (config, state_manager, ops_logger, diagnose hepsinde)

## Öğrenci ne yapmalı

1. `.env.example` → `.env` kopyala, doldur:
   - `APIFY_API_KEY_1` — Apify API anahtarı (zorunlu)
   - `APIFY_TIKTOK_ACTOR`, `APIFY_YOUTUBE_ACTOR` — Apify Store'dan tercih ettiğin actor id'leri
   - `IG_USERNAME` / `TIKTOK_USERNAME` / `YOUTUBE_SEARCH_QUERY` — kendi hesapların
   - `IG_VIEW_THRESHOLD` vb. — kendi izlenme barajların
   - `GMAIL_OAUTH_JSON` — Gmail OAuth token (kendi OAuth akışınla üret)
   - `REPORT_TO` / `REPORT_FROM` / `TECH_ERROR_TO` — mail adresleri
2. **Notion opsiyonel:** `NOTION_TOKEN` + `NOTION_DB_NOTIFIED_VIDEOS` doldurursan
   state Notion'da tutulur. Boş bırakırsan lokal `notified_state.json` kullanılır.
   `NOTION_DB_OPS_LOG` doldurursan operasyonel loglar da Notion'a yazılır.
3. `python -m scripts.diagnose` ile kurulumunu doğrula.
4. Railway'de Cron Job olarak deploy et (örn. haftada 2-3 kez).
