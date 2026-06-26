# Gelen Teklif Yanıtlayıcı

Markalardan e-postayla gelen **iş birliği / sponsorluk tekliflerine** ilk yanıtı otomatik
veren bir sistem. Gelen kutunu tarar, her thread'in gerçekten ücretli bir marka iş birliği
mi olduğunu bir LLM ile yargılar, sonra iki adımlı bir akış yürütür: önce gönderenin (içerik
üreticisi) ağzından sıcak bir **tanıştırma** maili, sonra teklif/fiyatı yürüten ekip üyesinin
(Partnerships Manager) ağzından bir **teklif taslağı**.

**Bu desen şuna yarar:** İçerik üreticisi, ajans veya freelancer olarak markalardan düzenli
inbound iş birliği maili alan herkes için. Gelen teklifleri elle ayıklamak, kibarca yanıtlamak
ve fiyat görüşmesini başlatmak zaman alır; bu sistem o ilk yanıtı standartlaştırır. İki rol
(gönderen + yönetici) tek kişiye de indirilebilir. Niş, fiyatlar, kapsam ve hesap adresleri
tamamen `.env` üzerinden gelir.

## Akış

1. **Tespit** — İki gelen kutu (iş + kişisel) taranır. Markalar genelde önce kişisel kutuya yazar; ikisi de izlenir.
2. **Niteleme (LLM)** — Her aday thread "gerçekten ücretli marka iş birliği mi?" diye nitelenir. Bülten, otomatik-cevap, satış maili, komisyon-only/barter teklifleri ve **gönderenin kendi hizmetini (eğitim/danışmanlık/workshop) satın alma** talepleri ayıklanır. Yargı kelimeyle değil LLM ile yapılır.
   - **Website-grounding** (`services/brand_web.py`): e-postadaki marka linki + gönderen domaini açılıp `<title>` + meta açıklama (varsa Firecrawl ile rendered içerik) çekilir; niteleme buna dayandırılır. Marka ne yaptığını söylemese bile sistem UYDURMAZ; emin değilse genel kalır.
3. **Dil** — Marka Türkçe yazdıysa Türkçe, İngilizce veya başka dilse İngilizce yanıt.
4. **Aksiyon**
   - **Emin + iyi + yeni + kapsam-içi** → gönderenin ağzından **LLM ile kişiselleştirilmiş tanıştırma** otomatik gönderilir (yönetici CC). Güvenlik: tanıştırma yalnızca sıcak karşılama + yöneticiye devir içerir, fiyat/paket/taahhüt YAZMAZ; LLM patlarsa deterministik şablona düşer.
   - **Şüpheli / düşük teklif / yenileme / kapsam-dışı / orta-düşük güven** → tanıştırma **gönderenin kutusunda TASLAK** bırakılır (gönderen onaylar ya da siler).
   - **İş birliği değil** → dokunulmaz (atlandı etiketi).
5. **Teklif (yönetici)** — Tanıştırma yapılmış (ya da markanın direkt yöneticiye yazdığı) thread'lere, opsiyonel Notion portföyünden seçilen referanslarla yöneticinin ağzından teklif **TASLAĞI** hazırlanır. **Asla otomatik gönderilmez** — yönetici kontrol edip gönderir (To: marka, CC: gönderen = reply-all).
   - **Çoklu draft (varsayılan 3):** Tek teklif yerine farklı fiyat stratejisiyle N ayrı hazır draft bırakılır (`OFFER_VARIANTS`): **odaklı** (sadece sordukları kalem) / **paket** (kısa + uzun birlikte) / **menü** (seçenek listesi). Markanın sorduğu kalem ÖNCE verilir. Fiyatlar `.env`'den (`PRICE_SHORT`/`PRICE_LONG`/`PRICE_BUNDLE`).

## Stack

- **LLM:** Üç iş de (niteleme + tanıştırma + teklif) varsayılan `gpt-4.1-mini` @ OpenAI direkt. OpenAI hesabında "data sharing" açıksa mini tier günlük belli bir token'a kadar ücretsizdir. Model adında `/` varsa OpenRouter, yoksa OpenAI direkt; modeller `.env` ile değişir.
- **Gmail API:** 3 hesap (iş + kişisel + yönetici), scope-aware OAuth. Token'lar lokalde `oauth/*.json`, production'da env var.
- **Notion API (opsiyonel):** Referans portföyü kütüphanesi. `NOTION_PORTFOLIO_DB_ID` boşsa devre dışı.
- **Firecrawl (opsiyonel):** Marka sitesini rendered okuma (grounding).
- **Deploy:** Cron olarak çalışır (tek tur çalışıp çıkar). İki ayrı cron önerilir:
  - **yanıt cron'u** (`main.py`): asıl otomasyon, periyodik (ör. birkaç saatte bir gündüz).
  - **denetim cron'u** (`review.py`): bağımsız output audit (günlük). Temizse sessiz; sorun varsa tek uyarı maili (opsiyonel).

## Idempotency / güvenlik

- Gmail etiketleri ile tekrar işleme önlenir (`<LABEL_PREFIX>/*`).
- Teklif DAİMA taslak. Tanıştırma sadece "emin" durumda otomatik.
- `DRY_RUN=1` → hiç gönderme/taslak, sadece log. `AUTO_SEND_INTRO=0` → emin durumda bile tanıştırmayı taslak bırak (acil fren).
- `SENDER_BLOCKLIST` → ısrarcı aracı ajanslarını tamamen atla.

## Çalıştırma

```bash
pip install -r requirements.txt
DRY_RUN=1 python main.py     # hiç göndermez/taslak yazmaz, sadece loglar (önce bununla dene)
python main.py               # asıl otomasyon, tek tur
python review.py             # bağımsız denetim, tek tur
python tests/test_e2e.py     # deterministik testler (a2-a6 API'siz) + niteleme/yazım (LLM gerekir)
```

## Environment Setup

`.env.example`'ı `.env` olarak kopyalayıp doldur. Production'da aynı isimlerle servis env'ine
geçir. En az şunlar gerekir: `SENDER_NAME`, `MANAGER_NAME`, üç e-posta adresi, üç Gmail OAuth
token'ı ve bir OpenAI anahtarı. Notion portföyü ve Firecrawl opsiyoneldir.

## Uyarlama Adımları

1. `.env` → isimler, e-posta adresleri, Gmail token'ları, OpenAI anahtarı.
2. `.env` → `PRICE_*`, `OFFER_VARIANTS`, `AUDIENCE_PITCH` (kendi rate card'ın + niş cümlen).
3. `.env` → `SCOPE_NOTE` veya `config.py` içindeki varsayılan kapsam: hangi sektörler otomatik karşılansın.
4. (Opsiyonel) Notion portföy DB'si oluştur, `NOTION_PORTFOLIO_DB_ID` + property adlarını `.env`'e gir.
5. `config.py` ve `services/llm.py` içindeki prompt'ları kendi tarzına göre ince ayar yap (üslup, paket içerikleri).
