# Paylaşım Notu — Reklam Fabrikası

**Mod:** C (şablona çevrildi)

## Ne yapıldı

### Temizlenen sırlar
- Kodda gömülü API anahtarı **yoktu**. Apify ve Fal AI anahtarları zaten Claude Code'un
  `userConfig` mekanizmasıyla (OS keychain) tutuluyor; repo'da düz değer geçmiyor.
- `.mcp.json` içindeki `${user_config.apify_api_key}` ve `${user_config.fal_api_key}`
  referansları **kasıtlı** korundu — bunlar placeholder enjeksiyon noktaları, gerçek değer değil.
- Yeni `.env.example` üretildi; iki anahtar için açık `<APIFY_API_KEY>` / `<FAL_API_KEY>`
  placeholder'ları ve kayıt URL'leri yazıldı.

### Scrub edilen kişisel veriler
- `.claude-plugin/plugin.json` — `author.name` (sahibin adı) → `<KULLANICI_ADI>`;
  `repository` (sahibin GitHub deposu) → `<GITHUB_REPO>`; `license: "Proprietary"` → `"MIT"`.
- `.claude-plugin/marketplace.json` — `owner.name` (sahibin adı) → `<KULLANICI_ADI>`.
- `LICENSE` — sahibin adı + e-postası + topluluk ibareli özel (proprietary) lisans →
  standart **MIT** lisansına çevrildi (`<KULLANICI_ADI>`).
- `README.md` — başa jenerik "bu bir şablondur / DTC reklam üretim deseni" çerçevesi eklendi;
  `~/Desktop/Allbirds/` ve `~/Desktop/Liquid-IV/` örnek müşteri klasörleri `<MARKA_A>` /
  `<MARKA_B>` placeholder'larına çevrildi; "AI Factory topluluğuna iletilir" → "topluluk kanalına".
- `.github/workflows/validate-manifest.yml` — sahibin secret'larına bağlı olabileceği için
  orijinal kopyalanmadı; yerine **jenerik, secret'sız** bir örnek workflow yazıldı (sadece
  manifest doğrulayıcısını çalıştırır).

### Korundu (kasıtlı)
- DTC reklam üretim deseni, 13 kreatif döngü becerisi (skills/), dört yol kalıbı, MCP config,
  plugin/marketplace yapısı, slash komutları, manifest doğrulayıcı.
- Beceri belgelerindeki **kamuya açık DTC marka örnekleri** (Huel, AG1, Soylent vb.) —
  bunlar sahibin müşteri envanteri değil, aracın nasıl çalıştığını öğreten genel örnekler;
  öğretici değer taşıdığı için bırakıldı.
- `package-lock.json` (lockfileVersion 3) korundu — Node sürüm kayması olmaz.

## Öğrenci ne yapmalı

1. `.env.example`'ı incele. Asıl kullanımda iki anahtarı **eklenti içinden**
   `/reklam-fabrikasi:setup-apify` ve `/reklam-fabrikasi:setup-fal-ai` komutlarıyla bağla
   (anahtarlar OS keychain'e gider, dosyaya yazılmaz). CI/kabuk ortamı için istersen
   `.env.example`'ı `.env` olarak kopyalayıp `APIFY_API_KEY` + `FAL_API_KEY` doldur.
2. `.claude-plugin/plugin.json` ve `marketplace.json` içindeki `<KULLANICI_ADI>` ve
   `<GITHUB_REPO>` placeholder'larını kendi adın ve (yayınlayacaksan) repo URL'inle doldur.
3. `LICENSE` içindeki `<KULLANICI_ADI>` yerine kendi adını yaz.
4. README'deki `<MARKA_A>` / `<MARKA_B>`, çalıştığın her marka için Claude Code'u ayrı bir
   klasörde açacağını anlatan örneklerdir — kendi marka klasör adlarınla zihninde değiştir,
   ayrıca bir şey doldurman gerekmez.
5. Higgsfield (Yol B) opsiyoneldir; aboneliğin yoksa Yol C (Fal) veya Yol A (kendin yapıştır)
   ile tüm üretim akışı çalışır.

## Orijinal amaç → yeni jenerik çerçeve

- **Orijinal:** Sahibin DTC markalara reklam kreatifi üretirken kullandığı, kendi GitHub deposu
  + adı + "AI Factory" topluluğuna özel proprietary lisansla paketlenmiş Claude Code eklenti
  marketplace'i. Örnek klasörler sahibin gerçek müşterilerine (marka adlarına) işaret ediyordu.
- **Yeni:** Herhangi bir ajans, freelancer veya içerik üreticisinin birden çok DTC markaya
  uçtan uca reklam kreatifi üretmek için kuracağı **jenerik şablon**. Desen aynen korundu:
  araştır (VOC, marka DNA, reklam casusu, UGC tarayıcı) → karakter/ürün varlık hazırlama →
  kreatif üretim (statik, UGC, metin) → optimizasyon (çoğaltıcı, rakip yeniden yapılandırma) →
  açılış sayfası → canlı Meta kampanya aktarımı. Anahtarlar, marka klasörleri, kimlik bilgisi
  ve lisans tamamen öğrencinin kendi değerleriyle doldurulur.
