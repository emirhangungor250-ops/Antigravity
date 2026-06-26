# Paylaşım Notu — YT_Aciklama_Otomasyonu

## Mod
B — İçerik korpusu (stil + affiliate) öğrenci koyar.

## Ne yapıldı
- **Sırlar:**
  - `.env` (gerçek anahtar dökümü içeriyordu) kopyalanmadı.
  - `.env.example` içindeki gerçek değerler temizlendi: hardcoded Notion DB ID, YouTube channel ID ve gerçek API anahtarı örnek değerleri placeholder'a çevrildi.
  - `scripts/build_style_corpus.py` içindeki hardcoded fallback channel ID kaldırıldı (artık env'den boş gelir).
- **Kişisel veri temizliği:**
  - "Dolunay" / "<KULLANICI_ADI>" referansları tüm kod ve dokümandan kaldırıldı (`description_builder.py`, `notion_service.py`, `google_auth.py`, `build_style_corpus.py`, `google_docs_service.py`, `README.md`).
  - `core/description_builder.py` system prompt'undaki kişisel marka linkleri (AI Factory skool URL, jotform işletmen formu) kaldırıldı; yerine `CREATOR_NAME` ve `ORGANIC_CTA_BLOCK` env değişkenleri eklendi.
  - `build_style_corpus.py` içindeki "dolunay" affiliate-hint regex'i `AFFILIATE_HINT_KEYWORD` env değişkenine taşındı.
  - "Antigravity" / kişisel proje yolu referansları jenerikleştirildi.
- **İçerik korpusu şablona indirildi:**
  - `data/style_corpus.json` — kanal sahibinin gerçek 23 video açıklaması (AI Factory linkleri, affiliate kodları, kişisel bilgiler içeriyordu) tamamen silindi; yapısı korunmuş 2 örnek placeholder bırakıldı + `_NOT` açıklaması eklendi.
  - `data/brand_affiliates.json` — gerçek affiliate linkleri (`topview`, `nim`, `hostinger`, `flowith`, `higgsfield`, `repocloud` — hepsi `dolunay` referans kodlu) silindi; 2 örnek placeholder + `_NOT` açıklaması bırakıldı.

## Öğrenci ne yapmalı

### 1. İçerik korpusunu kendi kanalınla doldur (en önemli adım)
- **`data/style_corpus.json`** — Kendi YouTube kanalınızdan 10-20 gerçek video açıklamasını ekleyin. LLM bu örneklerden sizin yazım stilinizi öğrenir. `python scripts/build_style_corpus.py` ile otomatik üretebilir veya elle doldurabilirsiniz.
- **`data/brand_affiliates.json`** — Kendi iş birliği/affiliate linklerinizi `marka_anahtari: link` formatında ekleyin.

### 2. `.env` değişkenlerini doldur
`.env.example`'ı `.env` olarak kopyalayın. Doldurulması gerekenler:
- `NOTION_SOCIAL_TOKEN`, `NOTION_DB_YOUTUBE_ISBIRLIKLERI` — kendi Notion token + video DB ID'niz
- `ANTHROPIC_API_KEY`
- `YOUTUBE_CHANNEL_ID` — kendi kanalınızın UC ID'si
- `CREATOR_NAME` — açıklama prompt'unda geçecek kanal sahibi adı
- `ORGANIC_CTA_BLOCK` — organic videolarda kullanılacak kendi sabit CTA link bloğunuz
- `AFFILIATE_HINT_KEYWORD` — kendi promo kodunuz (style corpus affiliate tespiti için, opsiyonel)
- `APIFY_API_KEY_1` — style corpus scrape için
- `GOOGLE_OUTREACH_TOKEN_JSON` — Drive OAuth token (Docs üretimi için)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID` — bildirim için

### 3. Notion DB şeması
Kod `Durum`, `URL`, `Drive` property'lerini ve `youtube_logo` page icon ayrımını bekler. Kendi Notion DB'nizi bu şemaya göre kurun veya `core/notion_service.py` içindeki property adlarını uyarlayın.
