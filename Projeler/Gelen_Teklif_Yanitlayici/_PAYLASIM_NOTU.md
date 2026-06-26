# Paylaşım Notu — Gelen Teklif Yanıtlayıcı

**Mod:** C (şablona çevrildi)

## Ne yapıldı

- **Temizlenen sırlar:** Kodda gömülü gerçek API anahtarı yoktu. `.env.example` baştan yazıldı; tüm değerler açık `<...>` placeholder ya da boş. Gerçek token/credential dosyaları (`.env`, `oauth/*.json`, `token*.json`) zaten allowlist kopyaya hiç girmedi.
- **Scrub edilen kişisel veriler:**
  - **İsimler/roller:** Sahibin adı + Partnerships Manager'ın adı tüm kod, prompt ve imzalardan kaldırıldı. İki jenerik rol kuruldu: **GÖNDEREN** (`config.SENDER_NAME`) ve **YÖNETİCİ** (`config.MANAGER_NAME`), ikisi de ENV'den. Sabit cinsiyet/zamir iddiası (İngilizce he/him) `SENDER_PRONOUN` env'ine çevrildi (varsayılan `they`).
  - **E-posta adresleri:** 3 sabit kişisel adres → `SENDER_PRIMARY_EMAIL` / `SENDER_PERSONAL_EMAIL` / `MANAGER_EMAIL` env'leri. Hesap anahtarları (kişisel adlar) → jenerik `inbox_primary/inbox_personal/manager`.
  - **Gmail token env adları:** Kişisel adlı token env'leri → `GOOGLE_PRIMARY/PERSONAL/MANAGER_TOKEN_JSON`. Lokal token dosya adları jenerikleştirildi (`gmail-primary-token.json` ...).
  - **Lokal mutlak yollar:** `config.py`'deki sahibe özel mutlak yol bağımlılığı (merkezi credential + oauth klasörü) kaldırıldı; artık aynı klasördeki `.env`'i (`config.load_env`) + proje-köküne göreli `oauth/` klasörünü okur (`__file__`'a göre dinamik). Sahibin makinesine özel mutlak yol: sıfır eşleşme.
  - **Notion portföy DB ID'si** (hardcoded 32-hex) → `NOTION_PORTFOLIO_DB_ID` env'i; boşsa portföy devre dışı. Notion property adları (`Marka/Kategori/Platform/İzlenme/Konu/URL`) `NOTION_PROP_*` env'leriyle değiştirilebilir. Token adayları `NOTION_SOCIAL/BUSINESS/REELS_TOKEN` → `NOTION_TOKEN`/`NOTION_TOKEN_2`.
  - **Fiyatlar/paketler:** Hardcoded `$800/$2000/$2500/$2800` → `PRICE_SHORT/PRICE_LONG/PRICE_BUNDLE` env'leri (pipeline + templates + writer prompt + testler hepsi bunları kullanır).
  - **İş birliği kapsamı (niche):** Sahibe özel kapsam metni (marka örnekleriyle) `SCOPE_NOTE` env'ine taşındı; jenerik bir tech/dijital örnek varsayılan bırakıldı. Teklifteki "uyum cümlesi" `AUDIENCE_PITCH` env'i oldu.
  - **Kara liste:** Sahibin `aha.inc/ahacreator` sabit blocklist'i boşaltıldı; `SENDER_BLOCKLIST` env'iyle doldurulur (mantık + testler korundu, testler değeri geçici ekleyip kaldırır).
  - **Uyarı maili (review.py):** Sabit kişisel alıcı + gönderen adresi + iç proje ön eki kaldırıldı → `ALERT_EMAIL_TO` / `ALERT_EMAIL_FROM` / `RESEND_API_KEY` env'leri; üçü de yoksa uyarı atlanır.
  - **Yorumlar/dokümanlar:** Tüm tarihli kişisel notlar, gerçek müşteri/kurum vaka adları, gerçek marka adları ve takipçi sayısı jenerikleştirildi. README + RUNBOOK baştan yazıldı.
  - **Kod fonksiyonları yeniden adlandırıldı:** kişisel-adlı yardımcı fonksiyon ve sabitler jenerik adlara çevrildi (`_manager_in_thread`, `_sender_addr_in_thread`, `MANAGER_ACCOUNT`; çağrı yerleri pipeline + review'da güncellendi).
  - **Testler (`tests/test_e2e.py`):** Senaryolardaki kişisel adresler/isimler/kurumlar jenerik marka ve örnek adreslere çevrildi (mantık ve kapsam aynı). Bölüm C canlı testi jenerik hesap anahtarlarıyla yeniden kuruldu.

## Doğrulama

- 10 Python dosyası `py_compile` ile derlendi, tam import grafiği hatasız yüklendi (isimli + isimsiz).
- Deterministik test grupları (A2-A6, **88 kontrol**) hem boş hem dolu `.env` ile **88/88 PASS**.
- Rename bütünlüğü kontrol edildi: kişisel-adlı eski yardımcı fonksiyon/sabit referansı kalmadı (hepsi `_manager_in_thread`/`_sender_addr_in_thread`/`MANAGER_ACCOUNT` jenerikleriyle değişti).
- Self-grep: kişisel ad/sır/mutlak-yol için **sıfır** gerçek eşleşme (kalan tek şey Türkçe "çağrı"/"çağrıştıran" kelimesi = yanlış-pozitif).

## Öğrenci ne yapmalı

1. `.env.example`'ı `.env` olarak kopyala. EN AZ şunları doldur:
   - `SENDER_NAME`, `MANAGER_NAME` (tek kişiysen ikisi aynı olabilir), `SENDER_PRONOUN`, `AUDIENCE_PITCH`
   - `SENDER_PRIMARY_EMAIL`, `SENDER_PERSONAL_EMAIL`, `MANAGER_EMAIL`
   - Üç Gmail OAuth token'ı: `GOOGLE_PRIMARY/PERSONAL/MANAGER_TOKEN_JSON` (ya da `oauth/*.json` dosyaları)
   - `OPENAI_API_KEY_DATA_SHARED` (yoksa `OPENAI_API_KEY`)
2. **Fiyatlar:** `PRICE_SHORT` / `PRICE_LONG` / `PRICE_BUNDLE` + `OFFER_VARIANTS` kendi rate card'ına göre.
3. **Kapsam:** `SCOPE_NOTE` (veya `config.py` içindeki varsayılan) — hangi sektörler otomatik karşılansın, hangileri taslak kalsın.
4. **(Opsiyonel) Referans portföyü:** Notion DB oluştur, `NOTION_TOKEN` + `NOTION_PORTFOLIO_DB_ID` gir. Property adların farklıysa `NOTION_PROP_*` ile eşle. İstemiyorsan boş bırak (teklif referanssız çıkar).
5. **(Opsiyonel) Grounding:** `FIRECRAWL_API_KEY` (marka sitesini rendered okuma). Yoksa ham title/meta'ya düşer.
6. **(Opsiyonel) Uyarı maili:** `RESEND_API_KEY` + `ALERT_EMAIL_TO` + `ALERT_EMAIL_FROM`.
7. İlk çalıştırmayı `DRY_RUN=1 python main.py` ile yap (hiçbir şey göndermez, sadece loglar). Doğruysa `DRY_RUN=0`.
8. Üslubu kendine uydur: `services/llm.py` içindeki `INTRO_SYSTEM` / `WRITER_SYSTEM` prompt'ları + `core/templates.py` fallback metinleri (paket içeriği: bonus Story, usage rights, Spark code vb. senin tekliflerine göre düzenle).

## Orijinal amaç → yeni jenerik çerçeve

- **Orijinal:** Belirli bir içerik üreticisinin (AI/teknoloji nişi, ~250K takipçi) markalardan gelen inbound iş birliği maillerini, kendi adı + Partnerships Manager'ı + sabit fiyat kartı + kişisel Notion portföyü hardcoded olacak şekilde işleyen, kişiye özel bir yanıt pipeline'ı.
- **Yeni:** Markalardan inbound iş birliği/teklif maili alan HERHANGİ bir içerik üreticisi / ajans / freelancer için jenerik bir "ilk yanıt" motoru. İki rol (gönderen + teklif yöneticisi) tek kişiye indirilebilir. Niş, fiyatlar, kapsam, hesap adresleri, referans portföyü ve üslup tamamen config/env-driven. Korunan değerli desen: LLM-nitelemeyle kör otomasyonu önleme (eğitim/danışmanlık talebini iş birliğinden ayırma dahil) + website-grounding + güvenli oto-tanıştırma (fiyatsız) + yöneticiye N çoklu teklif draftı + bağımsız output-audit cron'u + isim/selamlama/HTML sağlamlık kalkanları.
