# Paylaşım Notu — Marka İş Birliği

**Mod:** C (şablona çevrildi)

## Ne yapıldı
- **Temizlenen sırlar:** Kodda gömülü API anahtarı yok. `.env.example`'daki gerçekçi görünen placeholder'lar (`secret_xxx`, `apify_api_xxx`, `sk-proj-...`) açık `<...>` placeholder formatına çevrildi.
- **Scrub edilen kişisel veriler:**
  - sahibin tam profil dosyası (ad, mail, sosyal hesaplar, gerçek iş birliği listesi, izlenme sayıları, içerik URL'leri) → silindi, yerine boş `config/creator_profile.json` şablonu
  - `config/brand_filters.json` — sahibin ~60 markalık AI kataloğu + 12 kişisel false-positive hesabı → 2'şer örnek satıra indirildi
  - `config/rakipler.csv` — sahibin ~21 rakip influencer Instagram listesi → 2 örnek satır
  - `config/kampanya.yaml` — sahibe özel kampanya/email/değer önerisi → placeholder şablon
  - `data/calisan_markalar.json` — sahibin gerçek iş birliği yaptığı ~48 marka + handle → 2 örnek satır
  - `data/raw_reels.json` (scraped çıktı) silindi; `markalar/eski-markalar` + `marka-isimleri` boşaltıldı; `dolunay-tanitim` silindi
  - `src/personalizer.py` — kişisel profil sabiti → `CREATOR_PROFILE`, tüm hardcoded isim/izlenme/marka/sosyal-link prompt ve fallback'leri profil dosyasından okur hale getirildi
  - `src/gmail_sender.py`, `railway_scheduler.py` — kişisel domain'li token env adı → `GOOGLE_OAUTH_TOKEN_JSON`; `SENDER_EMAIL` default'u boşaltıldı; credential dosya adları jenerikleştirildi
  - `src/reporter.py`, `src/response_checker.py`, `src/followup.py` — hardcoded kişisel e-posta + ad-soyad referansları kaldırıldı / env-driven yapıldı
  - `mail_templates/*.html` + `mail_templates/ornekler/*.md` — sahibin adı, sosyal linkleri, gerçek marka + izlenme örnekleri `{{ ... }}` placeholder'larına çevrildi
  - `ops_logger.py` — hardcoded ops-log DB ID'si kaldırıldı, docstring'deki proje-adı jenerikleştirildi
  - `tests/` — kişisel marka/e-posta referansları örnek değerlere güncellendi
  - `experimental/` klasörü (gitignore'lu owner scratch — test sonuç JSON'ları, deneysel scriptler) ve `Denetim_Raporu.html` silindi
  - README baştan yazıldı (kişisel GitHub repo URL'si, sahibin influencer çerçevesi, Antigravity-spesifik entegrasyon tablosu çıkarıldı)

## Öğrenci ne yapmalı
1. `.env.example`'ı `.env` olarak kopyala; `NOTION_SOCIAL_TOKEN`, `APIFY_API_KEY_1`, `HUNTER_API_KEY`, `OPENAI_API_KEY`, `SENDER_EMAIL`, `GOOGLE_OAUTH_TOKEN_JSON`, `TELEGRAM_*` doldur.
2. **`config/creator_profile.json`** — kendi adın, sosyal hesapların, başarı örneklerin. Bu dosya outreach + signature'ın temelidir.
3. `config/kampanya.yaml` — kendi nişin, hedef sektörler, anahtar kelimeler, değer önerisi.
4. `config/brand_filters.json` — ilgilendiğin kategori markaları + marka sanılan kişi/medya hesapları.
5. `config/rakipler.csv` — takip etmek istediğin rakip hesaplar.
6. `mail_templates/` içindeki `{{ ... }}` placeholder'larını kendine göre doldur.

## Orijinal amaç → yeni jenerik çerçeve
- **Orijinal:** Sahibin influencer olarak AI/teknoloji markalarıyla iş birliği kurmak için kullandığı, kendi profili + rakip listesi + marka kataloğu + iş birliği geçmişi hardcoded/config'e gömülü kişisel outreach pipeline'ı.
- **Yeni:** İçerik üreticisi, ajans veya freelancer olarak markalara düzenli soğuk e-posta atan herkes için jenerik outreach motoru. Niş, gönderen profili, hedef kitle ve rakip listesi tamamen config-driven; 5 aşamalı pipeline (scrape → analyze → contact → personalize → send) + çok adımlı follow-up + response/bounce tespiti pattern'i korundu.
