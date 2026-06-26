---
name: reklam-fabrikasi-spy
description: "Kullanıcı /spy, /ad-spy, /spy 2.0, /find winning ads, /competitor ads yazdığında ya da rakip reklamları casuslama isteğinde bulunduğunda bu beceriyi kullan. Üç farklı girdi biçimini kabul eder ve üçü de paralel HTML swipe dosyalarına dönüşür: (1) tek bir marka adı veya Facebook URL'si, (2) virgülle ayrılmış marka listesi, (3) niş/anahtar kelime (10 rakibi otomatik araştırır). v2.0, her marka için Facebook Pages scraper'ı ZORUNLU kılar; reklamları çekmeden önce gerçek Reklam Kütüphanesi Sayfa ID'sini çözer, ardından Reklam Kütüphanesi'ni view_all_page_id=<id> ile sorgular. Böylece sonuçların tam olarak o markaya ait olduğu GARANTILENIR; kişisel profiller veya benzer slug'lara sahip ilgisiz sayfalar sonuçlara karışmaz. Apify MCP aracı kullanılamadığında Apify REST API yedek yolu devreye girer. Yalnızca STATİK GÖRSEL REKLAMLAR getirilir (video asla). Rakip meta verileri ve logolar ./Reklam Fabrikası/03_Ad_Spy/competitors.json dosyasına kaydedilir. Reklam casusluğu, swipe dosyası, rakip reklamlar veya kazanan reklam bulma isteklerinde HER ZAMAN tetikle."
---

# Ad Spy 2.0, Marka Kilitli Rakip İstihbaratı

Bu beceri, markaya kilitli HTML reklam swipe dosyaları üretir. 2.0'ı v1'den ayıran üç fark:

1. **Zorunlu Sayfa ID çözümlemesi.** Tek bir marka bile olsa her marka, gerçek `pageAdLibrary.id` değerini almak için önce Facebook Pages scraper'dan geçer. Reklam Kütüphanesi daha sonra `view_all_page_id={id}` ile sorgulanır; sonuçların tam olarak o markaya ait olduğu GARANTILENIR.
2. **Doğrulama kapısı.** Çözümlenen sayfalar kontrol edilir. Kişisel profiller, kısıtlı sayfalar ve slug uyuşmazlıkları, swipe dosyası oluşturulmadan ÖNCE yakalanır.
3. **REST API yedek yolu.** Apify MCP sarmalayıcısının şeması mevcut oturumda yüklenemezse beceri, eklentinin hassas userConfig alanındaki token'ı kullanarak Apify HTTP API'sini doğrudan çağırır. Kullanıcının Claude'u yeniden başlatmasına gerek kalmaz.

**Yalnızca statik görsel reklamlar. Video asla.**

---

## Adım 0, Apify MCP'nin Bağlı Olduğunu Doğrula

Araçlarını şimdi kontrol et. `mcp__apify__curious_coder--facebook-ads-library-scraper` görünüyorsa **Adım 1'e geç**.

Apify aracı yoksa kullanıcı henüz Apify token'ını girmemiş demektir. Şu mesajı birebir gönder ve DUR:

> Apify henüz bağlı değil. Apify Kişisel API token'ını eklemek için `/reklam-fabrikasi:setup-apify` komutunu çalıştır. Kurulum 30 saniyelik akışı adım adım anlatır ve token'ı kaydetmeden önce Apify API'sine karşı doğrular. Ücretsiz katman ayda 5 $'lık kredi içerir; yaklaşık 6.500 reklamı karşılar. Kurulum tamamlandıktan sonra Claude'u tamamen kapat (Cmd+Q) ve yeniden aç, ardından `/spy` komutunu tekrar çalıştır.

MCP sunucusunu kendin kurmaya çalışma, `~/.claude.json` dosyasını düzenleme, kullanıcıdan token'ı buraya yapıştırmasını isteme. Kurulum komutu bunların tamamını halleder ve token'ı eklentinin hassas userConfig alanı aracılığıyla saklar. Bu eklentinin `.mcp.json` dosyasındaki Apify MCP girişi, başlangıçta token'ı `Authorization: Bearer` başlığı olarak enjekte eder; token hiçbir zaman diskteki bir URL'ye yazılmaz.

Güvenlik notu: 1.3.3'ten önceki sürümlerde bu beceri kullanıcıdan token'ı buraya yapıştırmasını istiyor ve bunu `~/.claude.json` dosyasına URL sorgu dizisi olarak yazıyordu. MCP yetkilendirme spesifikasyonu tarafından anti-pattern olarak işaretlenen bu yöntemde URL'ye gömülü token'lar kabuk geçmişine, log dosyalarına ve disk durumuna sızıyordu. 1.3.3'ten itibaren token, eklentinin `apify_api_key` userConfig alanında saklanıyor; Claude Code bunu macOS ve Windows'ta işletim sistemi anahtar zincirinde, keychain'in bulunmadığı Linux'ta ise `~/.claude/.credentials.json` dosyasında tutuyor. Düz metin token hiçbir zaman `~/.claude.json` dosyasına yazılmıyor.

---

## Adım 0.5, Proje Çıktı Klasörünü Belirle

Çıktılar, Claude Code'un açık olduğu çalışma klasörüne kaydedilir. Herhangi bir çekme işleminden önce şu Bash bloğunu çalıştır:

```
PWD_ABS="$(pwd)"
TARGET="${PWD_ABS}/Reklam Fabrikası"
PROTECTED=0
case "$PWD_ABS" in
  "$HOME"|"$HOME/"|"/"|"/tmp"|"/tmp/"|"$HOME/Downloads"|"$HOME/Desktop")
    PROTECTED=1 ;;
esac
if [ "$PROTECTED" = "1" ] && [ ! -d "$TARGET" ]; then
  echo "PROTECTED:$PWD_ABS"
elif [ ! -f "$TARGET/_meta/folder-confirmed.flag" ] && [ ! -d "$TARGET" ]; then
  echo "FIRSTRUN:$TARGET"
else
  mkdir -p "$TARGET/03_Ad_Spy" "$TARGET/_meta"
  echo "READY:$TARGET"
fi

# Marka klasörü varsa ve dosya eksikse marka hafızasını (CLAUDE.md) ekle.
# Yapacak bir şey olmadığında sessizdir ve idempotent'tir.
if [ -d "$TARGET" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" ]; then
  bash "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi
```

- `PROTECTED:<path>`: Reddet ve kullanıcıya Claude Code'u markaya özel bir alt klasörde açmasını söyle. Dur.
- `FIRSTRUN:<path>`: "Çıktıları `<path>/` konumuna kaydedeceğim. Bu klasöre ilk kez kaydediyorum, doğru mu? (evet/hayır)" diye sor. Evet ise `mkdir -p "<path>/03_Ad_Spy" "<path>/_meta" && date -u +%Y-%m-%dT%H:%M:%SZ > "<path>/_meta/folder-confirmed.flag"` komutunu çalıştır ve devam et. Hayır ise dur.
- `READY:<path>`: Sessizce devam et.

Çözümlenen `<path>` değerini yakala (aşağıda `$RFLAB` olarak anılır) ve bu becerideki tüm çıktı yollarında kullan.

## Adım 1, Girdi Biçimini Tespit Et ve Bağlamı Topla

Üç girdi biçimi desteklenir. Üçü de paralel reklam casusluğu işlemlerine dönüşür.

| Girdi | Örnekler | Mod |
|---|---|---|
| Tek marka | `Huel`, `facebook.com/huel` | **marka modu** → 1 swipe dosyası |
| Marka listesi | `Huel, Soylent, Ka'Chava` veya `Huel ve 5 rakip` | **liste modu** → N swipe dosyası paralel |
| Niş / anahtar kelime | `protein tozu`, `duruş düzeltici`, `DTC cilt bakımı` | **niş modu** → 10 rakip araştır → N swipe dosyası paralel |

Kullanıcıya 2.0'ın desteklediği seçenekleri açıkça anlat:

> **Ad Spy 2.0, üç girdi modu:**
>
> 1. **Tek marka**, ad veya Facebook URL → 1 swipe dosyası
> 2. **Liste**, 2'den 15'e kadar marka ver → o kadar swipe dosyası paralel
> 3. **Niş**, ilk 10 rakibi araştırırım, sonra hepsini paralel olarak oluştururum
>
> Üç hızlı soru:
> 1. **Neyi casusluyorsun?**
> 2. **Ülke?** (varsayılan: US)
> 3. **Marka başına kaç reklam?** (varsayılan: 30, maks: 100)

Kullanıcı bir marka verip rakip istiyorsa (örn. "Huel ve 5 rakip"), hibrit olarak ele al: belirtilen markayı dahil et ve N rakip araştır.

### Adım 1.5, Erişim Veri Kullanılabilirliği Kontrolü (Çekmeden ÖNCE kullanıcı beklentilerini belirle)

Ülke onaylandıktan sonra erişim, kitle ve şeffaflık verilerinin kullanılabilir olup olmayacağına karar ver, ardından kullanıcıya ne bekleyeceğini söyle. Bu bir eklenti sınırı değil, Meta'nın şeffaflık kuralıdır.

Erişim verisi Meta tarafından yalnızca şu koşullardan BİRİ sağlandığında yayımlanır:

1. Reklam AB'de yayınlanıyor (Dijital Hizmetler Yasası zorunluluğu)
2. Reklam İngiltere'de yayınlanıyor (Çevrimiçi Güvenlik Yasası)
3. Reklam Brezilya'da yayınlanıyor (seçim şeffaflığı kuralları)
4. Reklam siyasi veya toplumsal konu olarak sınıflandırılmış (herhangi bir ülke)

Yalnızca ABD, Kanada, Avustralya, Meksika, Japonya veya AB/İngiltere/Brezilya dışındaki başka bir pazarı hedefleyen tamamen ticari markalar için Meta YALNIZCA kreatif, metin, yayın tarihleri, format ve yayıncı platformları gösterir. Erişim, gösterim veya kitle dökümü yok.

AB'nin 27 ülke kodu: AT, BE, BG, HR, CY, CZ, DK, EE, FI, FR, DE, GR, HU, IE, IT, LV, LT, LU, MT, NL, PL, PT, RO, SK, SI, ES, SE. Artı GB (İngiltere) ve BR (Brezilya).

`COUNTRY_UPPER` değeri {AB27 ∪ GB ∪ UK ∪ BR} kümesinde ise kullanıcıya şunu söyle:

> Bilgi: Bu pazar Meta'nın şeffaflık kuralları kapsamında. Swipe dosyası AB/İngiltere/Brezilya toplam erişimini, yaş x cinsiyet dağılımlarını, hedeflenen ülkeleri ve reklam başına ödeyici/faydalanan verilerini içerecek.

Aksi hâlde kullanıcıya şunu söyle:

> Bilgi: Meta, AB, İngiltere ve Brezilya dışındaki ticari reklamlar için erişim veya gösterim sayısı yayımlamıyor. Bu pazar için en güçlü kazanan sinyali yayın süresi ve hâlâ aktif olma durumudur. Kreatif, metin, yayın tarihleri, format ve yayıncı platformları ile birlikte sayfa bloğundan markanın Instagram hesabı ve doğrulama durumunu alacaksın. Erişim verisini görmek istersen marka orada da reklam veriyorsa bu beceriyi COUNTRY=GB (İngiltere) veya herhangi bir AB ülke koduyla yeniden çalıştır.

Bu bildirime takılma; yazdır ve devam et. Swipe dosyası geldiğinde kullanıcı ne bekleyeceğini bilir.

---

## Adım 2, Reklam Kütüphanesi Sayfa ID'lerini Çöz (Her Marka İçin ZORUNLU)

Bu adım **hiç atlanmaz**. Tek markalı istekler bile pages-scraper'dan geçer. v1'de kullanılan ham FB URL yaklaşımı, slug'lar kişisel profillerle çakıştığında kirlenmiş sonuçlar döndürüyordu (örn. `facebook.com/kachava` → marka değil "Alcides Kachava" adlı bir kişi).

### 2A, Girdi `niş` ise: önce rakipleri araştır

Bir Agent çağrısı başlat (subagent_type=general-purpose):

```
"{niche}" nişindeki ilk {N} rakip markayı araştır.
YALNIZCA bir JSON dizisi döndür. Her giriş: {"name": "...", "fb_url": "https://facebook.com/..."}.

Kurallar:
- Her fb_url'nin gerçekten o markanın resmi Facebook Sayfasına ait olduğunu doğrula.
- Yalnızca doğrudan rakipler. Genel perakendeciler dahil edilmez.
- YALNIZCA JSON dizisini döndür. Yorum veya markdown çiti yok.
```

5'ten az marka dönerse kullanıcıya söyle ve devam etmek mi yoksa aramayı daraltmak mı istediğini sor.

### 2B, FB URL Listesini Oluştur

Tüm markaları tek bir `{"url": "https://www.facebook.com/{slug}/"}` nesneleri listesinde derle.

Marka adı girişinde slug'ı türet: küçük harf, boşluk ve özel karakterleri kaldır. FB URL girişinde slug'ı URL'den ayrıştır.

### 2C, Pages Scraper'ı Çağır

**Önce MCP aracını dene.** `mcp__apify__apify--facebook-pages-scraper` çağrılabiliyorsa kullan:

```json
{
  "startUrls": [
    {"url": "https://www.facebook.com/huel/"},
    {"url": "https://www.facebook.com/soylent/"},
    ...
  ]
}
```

**REST API yedek yolu.** MCP aracının şeması yüklenemezse (`ToolSearch` için sonuç dönmezse) doğrudan HTTP'ye dön. Bu 2.0'ın kritik özelliğidir; beceri hiçbir zaman Claude'un yeniden başlatılmasını bekleyerek takılmaz.

```bash
python3 << 'EOF'
import json, os, urllib.request, sys
settings_path = os.path.expanduser('~/.claude/settings.json')
if not os.path.exists(settings_path):
    sys.stderr.write("settings.json bulunamadi, once /reklam-fabrikasi:setup-apify calistir\n")
    sys.exit(1)
with open(settings_path) as f:
    d = json.load(f)
token = d.get('pluginConfigs', {}).get('reklam-fabrikasi', {}).get('apify_api_key', '')
if not token:
    sys.stderr.write("apify_api_key ayarlanmamis, once /reklam-fabrikasi:setup-apify calistir\n")
    sys.exit(1)
api_url = "https://api.apify.com/v2/acts/apify~facebook-pages-scraper/run-sync-get-dataset-items?timeout=240"
payload = {"startUrls": [
    {"url": "https://www.facebook.com/huel/"},
    {"url": "https://www.facebook.com/soylent/"}
]}
req = urllib.request.Request(
    api_url,
    data=json.dumps(payload).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    },
    method="POST"
)
with urllib.request.urlopen(req, timeout=300) as resp:
    items = json.loads(resp.read())
print(json.dumps(items, indent=2))
EOF
```

Token MUTLAKA `~/.claude/settings.json` dosyasından `pluginConfigs["reklam-fabrikasi"].apify_api_key` altından okunmalıdır; `~/.claude.json` dosyasından okuma yapma ve kullanıcıdan tekrar yapıştırmasını isteme. İstek başlığında `Authorization: Bearer ${TOKEN}` olarak ilet. Token-URL-içine yerleştirme yöntemi v1.3.3'te kaldırıldı.

---

## Adım 3, Çözümlenen Her Sayfayı Doğrula (Marka Kilidi Kapısı)

Pages-scraper'ın döndürdüğü her öğe için sınıflandır:

| Koşul | Karar | İşlem |
|---|---|---|
| `error: not_available` | **SERT HATA** | Sayfa kısıtlı. Kullanıcıdan doğrudan Reklam Kütüphanesi URL'si iste (aşağıdaki yedek yola bak). |
| `error: no_items` | **SERT HATA** | Slug mevcut değil. Kullanıcıya söyle, doğru slug veya Reklam Kütüphanesi URL'si iste. |
| `categories` boş VE `pageAdLibrary.id` eksik | **SERT HATA** | Bu bir Sayfa değil, kişisel profil. Kullanıcıdan markanın doğru Sayfa slug'ını iste. |
| `pageAdLibrary.id` mevcut + `categories` içinde "Page" var | **GEÇTI** | Devam et. Logo, başlık ve ad_library_id'yi kaydet. |
| `pageAdLibrary.id` mevcut AMA `title` marka adıyla makul ölçüde eşleşmiyor | **YUMUŞAK UYARI** | Kullanıcıya göster: "`{slug}` adresi `{title}` olarak çözümlendi, doğru marka mı? (evet/hayır)". Onay bekle. |

**Yumuşak uyarı için başlık eşleşme sezgisi:** İkisini de küçük harfe çevir, noktalama/boşlukları kaldır. Marka adı başlıkta veya başlık marka adında tamamen yer alıyorsa eşleşme say. Aksi hâlde uyar.

### Doğrulama sert hata verdiğinde

Her başarısız marka için kullanıcıya tam olarak ne olduğunu söyle. Ham URL çekmeye sessizce geri dönme (bu v1'in kirlenme hatasıdır).

> ❌ **{Brand} tek bir Reklam Kütüphanesi sayfasına kilitlenemedi.**
>
> Neden: {hata nedeni, kısıtlı sayfa / slug bulunamadı / kişisel profil / vb.}
>
> {Brand} markasını Meta Reklam Kütüphanesi'nde kendin bulabilirsen, doğrudan Reklam Kütüphanesi URL'sini buraya yapıştır (`https://www.facebook.com/ads/library/?...&view_all_page_id=12345...` gibi görünür) ve o ID'yi scraper'dan geçireyim. Aksi takdirde bu markayı atlayıp diğerleriyle devam edeceğim.

Kullanıcı `view_all_page_id={id}` içeren bir URL yapıştırırsa ID'yi çıkar ve o markayı id={id} ile GEÇTI olarak kabul et (logo/başlık yok, yalnızca ID).

### Doğrulanmış markaları competitors.json'a kaydet

Şema (yol: `$RFLAB/03_Ad_Spy/competitors.json`; `$RFLAB`, Adım 0.5'te çözümlenen proje bazlı yoldur):

```json
[
  {
    "name": "Huel",
    "slug": "huel",
    "fb_url": "https://facebook.com/huel",
    "ad_library_page_id": "{PAGE_ID}",
    "ad_library_url": "https://www.facebook.com/ads/library/?...&view_all_page_id={PAGE_ID}",
    "logo_url": "https://scontent...",
    "page_title": "Huel",
    "page_categories": ["Page", "Food & beverage company"],
    "niche": "{varsa niş, yoksa 'user-supplied'}",
    "first_seen": "YYYY-MM-DD",
    "last_spied": "YYYY-MM-DD",
    "swipe_files": ["adspy-huel-YYYYMMDD.html"]
  }
]
```

Güncelleme mantığı: dosya yoksa oluştur. Marka varsa `last_spied` değerini güncelle, swipe dosyasını ekle (tekrar yok). Marka yeniyse ekle. 2 boşluklu girintili yazdır.

Kullanıcı bir marka için manuel `view_all_page_id` verdiyse `page_title: null`, `logo_url: null`, `notes: "manually supplied via Ad Library URL"` olarak işaretle.

---

## Adım 4, Paralel Reklam Casusluğu Agent'larını Başlat

**TEK bir mesajda N Agent çağrısı gönder.** Paralel çalışırlar. Sıralı gönderme yanlıştır; marka sayısıyla doğrusal ölçeklenir.

1 marka için: yine Agent çağrısı kullan (1 agent, 1 çağrı). Satır içi yapma. Tutarlılık öngörülebilirliktir.

Her agent aşağıdaki tam prompt şablonunu alır; içinde çözümlenmiş Sayfa ID'si URL'ye gömülüdür. Agent hiçbir zaman ham slug görmez, yalnızca `view_all_page_id={id}` URL'si görür. Bu marka kilidi garantisidir.

Başlatmadan önce kullanıcıya söyle:

> 🔍 **{N} marka doğrulanmış Sayfa ID'lerine kilitlendi. {N} paralel reklam casusluğu başlatılıyor.** Tahmini süre: 60 ile 180 saniye.

### Agent Prompt Şablonu

```
Tek bir marka için marka kilitli reklam casusluğu yapıyorsun ve tek başına çalışan bir HTML swipe dosyası üretiyorsun.

== GİRDİLER ==
- Marka: {NAME}
- Slug: {SLUG}
- Reklam Kütüphanesi Sayfa ID'si: {PAGE_ID}
- Sayfa Başlığı (kanonik, pages-scraper'dan): {PAGE_TITLE_OR_NULL}
- Ülke: {COUNTRY}
- Ülke kodu (büyük harf): {COUNTRY_UPPER}
- Reklam sayısı: {COUNT}
- Çıktı yolu: $RFLAB/03_Ad_Spy/adspy-{SLUG}-{YYYYMMDD}.html

== ADIMLAR ==

1. ÇEK, yalnızca marka kilitli URL
   URL MUTLAKA view_all_page_id={PAGE_ID} içermelidir. Ham sayfa slug'ı hiçbir zaman geçme; bu anahtar kelime-fallback kirlenmesini tetikler.

   mcp__apify__curious_coder--facebook-ads-library-scraper'ı şu parametrelerle çağır:
   {
     "urls": [{"url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country={COUNTRY_UPPER}&search_type=page&media_type=image&view_all_page_id={PAGE_ID}"}],
     "count": {COUNT},
     "scrapeAdDetails": true,
     "scrapePageAds.countryCode": "{COUNTRY_UPPER}",
     "scrapePageAds.activeStatus": "active",
     "scrapePageAds.sortBy": "impressions_desc"
   }

   `scrapeAdDetails: true` ZORUNLUDUR. Olmadan aktör yalnızca reklam kartları döndürür; `aaa_info`, `transparency_by_location`, sayfa başına IG hesabı ve `advertiser.ad_library_page_info` bloğu gelmez, AB/İngiltere/Brezilya reklamları boş erişim sayısı döndürür ve beceri çıktısı eksik kalır.

   Nokta-gösterim anahtarları (`scrapePageAds.countryCode` vb.) aktörün güncel girdi şemasıdır. Eski `-dot-` formu (`scrapePageAds-dot-countryCode`) kullanımdan kaldırılmıştır; daha yeni aktör derlemelerinde sessizce varsayılanlara düşebilir. Her zaman nokta formunu kullan.

   totalItemCount > items.length ise mcp__apify__get-actor-output ile sayfalama yap:
   {
     "datasetId": "<id>",
     "offset": <alınan öğe sayısı>,
     "limit": <kalan>,
     "fields": "ad_archive_id,page_name,page_id,is_active,start_date,start_date_formatted,end_date,publisher_platform,snapshot.cta_text,snapshot.cta_type,snapshot.display_format,snapshot.body.text,snapshot.title,snapshot.link_url,snapshot.images,snapshot.videos,snapshot.cards,snapshot.page_id,snapshot.page_profile_picture_url,ad_library_url,aaa_info,transparency_by_location,advertiser"
   }

2. KİRLENME KONTROLÜ (2.0 garantisi)
   Çektikten sonra, döndürülen tüm reklamlardaki farklı page_name değerlerini say.
   - TÜM reklamlar AYNI page_name'e sahipse (veya page_name, PAGE_TITLE ile eşleşiyorsa) → GEÇTI, devam et.
   - KARIŞIK page_name'ler → KİRLENMİŞ. Swipe dosyasını OLUŞTURMA. Şunu döndür:
     {"brand": "{NAME}", "status": "failed", "error": "contaminated_results", "page_names_seen": [...]}
   - SIFIR reklam → {"brand": "{NAME}", "status": "ok", "ads_total": 0, "winners": 0, "output_path": "..."} döndür ve küçük bir "reklam bulunamadı" HTML'i oluştur.

3. FILTRELE (yalnızca statik görseller)
   Reklamı YALNIZCA şunların TAMAMI doğruysa tut:
   - snapshot.videos boş/null/eksik
   - snapshot.images VEYA snapshot.cards[].original_image_url VEYA snapshot.cards[].resized_image_url içinde en az bir görsel URL var
   - snapshot.display_format != "VIDEO"

3.5. ERİŞİM VERİSİ YAPISINI TESPIT ET
   Filtrelemeden sonra, tutulan herhangi bir reklamda `aaa_info`'nun erişim sayılarıyla dolu olup olmadığını kontrol et. Kesin alan bölgeye göre değişir:
   - AB reklamları → `aaa_info.eu_total_reach` (tam sayı)
   - İngiltere reklamları → `aaa_info.uk_total_reach` (tam sayı, `transparency_by_location.uk_transparency` üzerinden çalışırken)
   - Brezilya reklamları → `aaa_info.br_total_reach` (tam sayı)
   - Herhangi bir ülkedeki siyasi/konu reklamları → `aaa_info.total_reach` AB/İngiltere/Brezilya dışında bile mevcut olabilir

   REACH_AVAILABLE = true: tutulan herhangi bir reklam aaa_info'da null olmayan erişim değerine sahipse. Aksi hâlde REACH_AVAILABLE = false.

   HTML oluşturma adımı için hesapla ve hatırla:
   - REACH_AVAILABLE (boolean)
   - REACH_REGION ("EU", "UK", "BR", "POLITICAL" veya REACH_AVAILABLE false olduğunda null)
   - TOTAL_REACH_SUM (tam sayı, REACH_AVAILABLE true olduğunda tutulan tüm reklamlardaki toplam)

4. PUANLA
   days_running = bugün - start_date (hem unix epoch hem ISO tarihi işle).

   REACH_AVAILABLE true olduğunda (AB/İngiltere/Brezilya markası veya siyasi reklam seti):
   - Birincil sinyal: aaa_info erişimi (eu_total_reach, uk_total_reach, br_total_reach, hangisi doluysa).
   - İkincil sinyal: days_running.
   - Katmanlar erişim + süreyi harmanlayarak hem yüksek erişimli yeni bir lansmanın hem de eski yavaş koşucunun öne çıkmasını sağlar:
     - 🏆 KANITSALMIŞ KAZANAN: is_active=true VE (erişim >= 100000 VEYA days_running >= 60)
     - 🔥 SICAK KOŞUCU: is_active=true VE (erişim >= 25000 VEYA days_running >= 21)
     - ⚡ AKTİF REKLAM: is_active=true VE erişim < 25000 VE days_running < 21
     - ✅ EMEKLİ KAZANAN: is_active=false VE (erişim >= 100000 VEYA days_running >= 60)
     - ⬜ KISA KOŞU: is_active=false VE erişim < 25000 VE days_running < 60
   - Her katmanda önce erişime, sonra days_running'e göre sırala (azalan).

   REACH_AVAILABLE false olduğunda (ABD/CA/AU/JP/vb. ticari marka):
   - Birincil sinyal: is_active ile birlikte days_running.
   - Katmanlar yalnızca süre bazlıdır (önceki davranışla aynı):
     - 🏆 KANITSALMIŞ KAZANAN: is_active=true VE days_running >= 60
     - 🔥 SICAK KOŞUCU: is_active=true VE days_running >= 21
     - ⚡ AKTİF REKLAM: is_active=true VE days_running < 21
     - ✅ EMEKLİ KAZANAN: is_active=false VE days_running >= 60
     - ⬜ KISA KOŞU: is_active=false VE days_running < 60
   - Her katmanda days_running'e göre sırala (azalan).

   Katmanları şu sırayla sırala: 🏆 → 🔥 → ⚡ → ✅ → ⬜. En fazla 20'ye kap. ⬜ yalnızca 5'ten az kazanan/koşucu varsa dahil et.

5. ANALİZ ET
   Her 🏆/🔥/⚡ için 2 ile 3 cümle yaz:
   - Hook türü (kaydırmayı ne durdurur)
   - Farkındalık seviyesi (Habersiz / Sorun Farkında / Çözüm Farkında / Ürün Farkında / En Farkında)
   - Neden işe yarıyor (aciliyet, özgüllük, sosyal kanıt, kimlik, korku/arzu, zıtlık, dönüşüm)
   Kesinlikle yalnızca metin + yayın süresine dayan. Spekülasyon yapma.

   REACH_AVAILABLE true olduğunda, her kazanan kart için kitle sinyalini açıklayan kısa bir satır ekle:
   - `aaa_info.age_country_gender_reach_breakdown[]`'dan baskın yaş dilimi (örn. "35 ile 44 arası ağırlıklı")
   - Cinsiyet ağırlığı (örn. "%62 kadın") yalnızca bir taraf >= %60 ise, aksi hâlde "dengeli cinsiyet"
   - `aaa_info.location_audience`'tan en çok hedeflenen ülke (AB pan-bölge koşularında genellikle birden fazla)
   Satırı şöyle formatla: `Kitle: 35 ile 44 arası ağırlıklı, %62 kadın, birinci pazar Almanya.` REACH_AVAILABLE = true bir çalıştırma içinde bile aaa_info null olan kartlarda satırı tamamen atla (Meta bazen reklam başına null bırakıyor).

6. GÖRSELLERİ İNDİR → BASE64
   Her reklam için en iyi URL'yi seç: snapshot.cards[0].resized_image_url → original_image_url → snapshot.images[0]
   Her biri için çalıştır:
   curl -s -L --max-time 10 \
     -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
     -H "Referer: https://www.facebook.com/" \
     "<URL>" | base64
   macOS'ta düz `base64` kullan (-w bayrağı yok). Başarısız olursa → görseli null olarak işaretle. Sıralı işle.

7. HTML OLUŞTUR, Bağımsız, tüm CSS satır içi, base64 görseller, harici bağımlılık yok.
   Aşağıdaki HTML TASARIM SİSTEMİ bölümünü takip et.

8. KAYDET, $RFLAB/03_Ad_Spy/adspy-{SLUG}-{YYYYMMDD}.html'e yaz (üst agent mutlak yolu başlatmadan önce enjekte eder)

9. DÖNDÜR, yalnızca şu JSON, yorum yok:
   {
     "brand": "{NAME}",
     "output_path": "...",
     "ads_total": N,
     "winners": M,
     "reach_available": true | false,
     "reach_region": "EU" | "UK" | "BR" | "POLITICAL" | null,
     "total_reach": <tam sayı veya null>,
     "status": "ok"
   }
   Kirlenme durumunda: {"brand": "{NAME}", "status": "failed", "error": "contaminated_results", "page_names_seen": [...]}
   Diğer hatalarda: {"brand": "{NAME}", "status": "failed", "error": "<neden>"}

== HTML TASARIM SİSTEMİ ==

Palet, Reklam Fabrikası VOC HTML'iyle eşleştirilmiştir; her iki çıktı da aynı ürün ailesine ait gibi görünür. Hafif, editoryal, lacivert + arduvaz, soluk vurgu renkleri. Başlık bloğu "kontrol çubuğu" hissi için koyu lacivert kalır, sayfanın geri kalanı açık gri yüzeylerle beyazdır.

CSS değişkenleri:
  --bg: #FFFFFF;
  --bg-card: #F4F6FA;
  --bg-card-hover: #E8EDF5;
  --border: #E8EDF5;
  --border-accent: rgba(22, 36, 65, 0.10);
  --text-primary: #162441;
  --text-secondary: #8A9BBC;
  --text-dim: #6B7A99;
  --body: #2C3E50;
  --navy: #162441;
  --slate: #8A9BBC;
  --surface-light: #F4F6FA;
  --surface-mid: #E8EDF5;
  --tier-proven: #162441;
  --tier-hot: #C0392B;
  --tier-active: #1A5276;
  --tier-retired: #1A6B3C;
  --tier-short: #8A9BBC;
  --accent-red: #C0392B;
  --accent-green: #1A6B3C;
  --accent-blue: #1A5276;
  --accent-amber: #8B6914;
  --accent-purple: #5B4A8A;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;

DÜZEN:
- Başlık: tam genişlik lacivert blok (arka plan `--navy`, sayfadaki tek koyu alan). Sol: küçük arduvaz büyük harf takip eden "THE AI AD LAB" (renk `--slate`) + beyaz büyük "Ad Spy 2.0 Raporu". Sağ: marka, ülke, tarih `--slate` içinde. Altı: lacivert başlık bloğu üzerinde beyaz metin içeren 3 istatistik hapı (TARANAN REKLAMLAR / POTANSİYEL KAZANANLAR / YALNIZCA STATİK). logo_url sağlandıysa bonus hap: küçük yuvarlak logo + sayfa başlığı (marka kilidini kanıtlar), başlığın içinde.
- Sayfa gövdesi arka planı: `--bg` (beyaz). Başlığın altındaki tüm içerik, `--surface-light` kart arka planlarıyla beyaz üzerinde durur.
- Erişim kullanılabilirliği bandı (1.6.1'de YENİ):
  - REACH_AVAILABLE true → başlıkta 4. istatistik hapını göster: "TOPLAM ERİŞİM" ile toplu `TOTAL_REACH_SUM` binlik ayraçlı biçimde, değer `--accent-green` içinde. Marka kilidi satırında kart ızgarasının üstüne küçük bir hap daha ekle: "🛡 AB ŞEFFAFLIK VERİSİ MEVCUT" (veya "🛡 İNGİLTERE ŞEFFAFLIK VERİSİ" / "🛡 BREZİLYA ŞEFFAFLIK VERİSİ"), arka plan `--surface-light`, kenarlık 1px `--accent-blue`, metin `--accent-blue`.
  - REACH_AVAILABLE false → erişim hapı yok. Kart ızgarasının üstüne `reach-disclaimer` sınıflı bilgi bandı: `--surface-light` arka plan, `--accent-amber` 3px sol kenarlık, `--text-secondary` metin, tek satır: "Meta, AB, İngiltere ve Brezilya dışındaki ticari reklamlar için erişim veya gösterim sayısı yayımlamıyor. Bu marka için en güçlü kazanan sinyali yayın süresi ve hâlâ aktif olma durumudur." Bu bandı atlamayın, beklentileri belirler ve kullanıcının çekmenin başarısız olduğunu düşünmesini önler.
- Yapışkan filtre çubuğu: HEPSİ · 🏆 KANITSAL · 🔥 SICAK · ⚡ AKTİF · ✅ EMEKLİ, beyaz arka plan, `--border` alt kenarlık, katman düğmeleri ROZET STİLLERİ'ne göre biçimlendirilmiş. JS onclick data-badge'e göre filtreler.
- Kart ızgarası: grid-template-columns: repeat(auto-fill, minmax(500px, 1fr)). 768px'in altında tek sütun. Her kart: `--bg-card` arka plan, 1px `--border` kenarlık, 4px kenarlık yarıçapı, geniş dolgu.

KART YAPISI (yukarıdan aşağıya):
- Rozet satırı (soldaki rozet, sağda: X gün yayında · platformlar · varsa erişim, sağ taraf metni `--text-secondary` içinde)
  - Kartta aaa_info erişimi varsa: sağ tarafı `· 1.2M erişim` ile genişlet (kompakt biçim: 1.2M / 350K / 12.4K). Erişim alanını `--accent-green` renk font-weight 600 ile göster.
- Reklam görseli: <img src="data:image/jpeg;base64,..."> genişlik %100, yükseklik 320px, object-fit cover, 4px kenarlık yarıçapı
  Base64 null ise: `--surface-mid` arka plan ve `--text-dim` metinle <div class="img-placeholder">Görsel yok · Reklam ID: {id}</div>
- `--text-primary` kalın marka adı + `--accent-blue` içinde [Reklam Kütüphanesi →] bağlantısı (hover: altı çizili)
- Başlık: kalın `--text-primary` (lacivert), 17px, satır yüksekliği 1.4
- Gövde metni: `--body` (#2C3E50), 14px, satır yüksekliği 1.6
- CTA düğme metni: hap stili, `--surface-mid` arka plan, `--text-primary` metin, 4px kenarlık yarıçapı, 12px yazı tipi
- Ayırıcı: 1px `--border`
- 🧠 NEDEN KAZANIYOR başlığı: küçük `--text-secondary` büyük harf takip etiketi. Altında `--body` içinde 2 ile 3 cümle.
- Etiket hapları: [Hook: Tür] [Farkındalık Seviyesi], `--surface-mid` arka plan, `--text-primary` metin, 11px, 4px kenarlık yarıçapı
- KİTLE VE ERİŞİM BLOĞU (1.6.1'de YENİ, YALNIZCA kartın aaa_info'su dolu olduğunda):
  - 1px `--border-accent` üst kenarlıkla "🎯 KİTLE VE ERİŞİM" başlıklı kompakt bölüm oluştur. Bölüm başlığı `--text-secondary` büyük harf takip, 11px.
  - İçeride `etiket: değer` çiftlerinin dört küçük satırı. Etiket `--text-secondary` (arduvaz), değer `--text-primary` (lacivert).
    - Erişim: binlik ayraçlı tam sayı + `--accent-blue` içinde bölge etiketi ("1.240.000 (AB)")
    - Yaş: `aaa_info.age_audience.min`'den `aaa_info.age_audience.max`'a, artı `age_country_gender_reach_breakdown[]`'dan baskın dilim ("18 ile 65, 35 ile 44 arası ağırlıklı")
    - Cinsiyet: `aaa_info.gender_audience`'tan ve bir taraf >= %60 olduğunda erkek/kadın/bilinmeyen dağılımından ("Hepsi, %62 kadın")
    - Hedeflenen ülkeler: `aaa_info.location_audience`'tan virgülle ayrılmış, 5'ten sonra "+N tane daha" ile kısalt ("DE, FR, ES, IT, NL +6 tane daha")
  - `aaa_info.payer_beneficiary_data` mevcutsa beşinci satır ekle: "Ödeyen: <ilk faydalanan>"
  - REACH_AVAILABLE = true bir çalıştırma içinde bile aaa_info = null olan kartlarda bu bloğu gösterme. Kartın geri kalanını normal şekilde göster.
- Ayırıcı: 1px `--border`
- Alt satır: [📋 /rebuild için Kopyala] düğmesi (`--accent-blue` arka plan, beyaz metin, 4px kenarlık yarıçapı) + `--text-secondary` içinde başlangıç tarihi (arduvaz, 11px)

ROZET STİLLERİ (açık tema, alfa-%10 arka plan + 1px solid kenarlık + tam renkli metin, 11px büyük harf, 4px kenarlık yarıçapı, 4px 10px dolgu):
  🏆 KANITSAL KAZANAN → bg: rgba(22, 36, 65, 0.08);   border: #162441; color: #162441
  🔥 SICAK KOŞUCU     → bg: rgba(192, 57, 43, 0.10);  border: #C0392B; color: #C0392B
  ⚡ AKTİF REKLAM     → bg: rgba(26, 82, 118, 0.10);  border: #1A5276; color: #1A5276
  ✅ EMEKLİ KAZANAN   → bg: rgba(26, 107, 60, 0.10);  border: #1A6B3C; color: #1A6B3C
  ⬜ KISA KOŞU        → bg: rgba(138, 155, 188, 0.18); border: #8A9BBC; color: #8A9BBC

JAVASCRIPT (satır içi <script>):
- const ADS_DATA = [...tüm reklamlar JSON olarak, doluysa aaa_info verbatim taşıyarak...]
- const REACH_AVAILABLE = true | false
- const REACH_REGION = "EU" | "UK" | "BR" | "POLITICAL" | null
- Kartları sabit HTML'den değil ADS_DATA'dan oluştur
- Filtre işlevi: data-badge'e göre kartları göster/gizle
- 📋 düğmesi için panoya kopyalama işlevi. Şunu kopyalar:
    --- /REBUILD İÇİN REKLAM ---
    Reklamveren: {PAGE_NAME}
    Başlık: {TITLE}
    Gövde: {BODY}
    CTA: {CTA_TEXT}
    Reklam Kütüphanesi: https://www.facebook.com/ads/library/?id={AD_ARCHIVE_ID}
    Yayın başlangıcı: {START_DATE}
    Rozet: {BADGE_LABEL} ({DAYS} gün)
    Reklamın aaa_info erişimi varsa bir satır daha ekle:
    Erişim: {COMPACT_REACH} ({REGION}), {GENDER_SKEW}, birinci pazar {TOP_COUNTRY}
  Düğme metni 1,5 saniye boyunca "✓ Kopyalandı!" olarak değişir
- Kart hover: transform: translateY(-2px), arka plan `--bg-card-hover`, kenarlık `--text-secondary` %50 alfa, box-shadow 0 4px 16px rgba(22, 36, 65, 0.08)

ALT BİLGİ (ortalanmış, 11px, beyaz üzerinde `--text-secondary` metin, 1px `--border` üst kenarlık, geniş dikey dolgu):
  Reklam Fabrikası, Ad Spy 2.0 Raporu | {DATE} | {N} statik reklam (marka kilitli: page_id={PAGE_ID})
  REACH_AVAILABLE true ise ekle: " · Erişim verisi Meta {REGION} şeffaflık açıklamasından alınmıştır."
  REACH_AVAILABLE false ise ekle: " · Meta bu pazar için erişim verisi yayımlamıyor. Yayın süresi en güçlü mevcut kazanan sinyalidir."
  Sonraki adım: Bir 🏆 veya 🔥 seç → "📋 /rebuild için Kopyala"ya tıkla → /rebuild komutunu çalıştır

== KESİN KURALLAR (çalışman için geçerlidir) ==
- Yalnızca marka kilitli URL, ham slug ile hiçbir zaman çekme yapma
- Yalnızca statik, video içerikli tüm reklamları at
- Kirlenme kontrolü zorunludur, karışık page_name varsa iptal et ve başarısız döndür
- Asla veri uydurma, bir alan eksikse eksik olarak işaretle
- Asla erişim sayısı uydurma, aaa_info null ise çıkarım yapma, tahmin etme veya komşu reklamlardan veri alma. Bunun yerine reddi göster.
- Farklı bir bölgeden erişim verisi aramak için aynı page_id'yi farklı bir ülke ile yeniden çekme. Kullanıcının istediği ülkeye saygı duy.
- Yalnızca base64, HTML'de harici görsel URL'lerine hiçbir zaman bağlantı verme
- Kazanan puanına göre sırala, çekme sırasına göre asla değil
- En fazla 20'ye kap
- Dürüst puanlama, 3 gün aktif kazanan değildir
```

---

## Adım 5, Toplu Özet

Tüm paralel agent'lar döndükten sonra JSON'larını ayrıştır ve şunu sun:

```
✅ Ad Spy 2.0 Tamamlandı

Marka kilitlendi ve oluşturuldu:
  🏆 Ka'Chava   → 28 reklam, 12 kazanan, 4.2M erişim (AB) → adspy-kachava-{tarih}.html
  🏆 Huel       → 18 reklam, 7 kazanan,  1.8M erişim (AB) → adspy-huel-{tarih}.html
  ⚡ AG1        → 5 reklam,  3 kazanan,  erişim yok (ABD)  → adspy-ag1-{tarih}.html
  ⚪ Soylent    → 0 statik reklam (kütüphanelerinde yalnızca video yayınlanıyor)

Marka kilidi yapılamadı:
  ❌ X Markası, pages-scraper not_available döndürdü (sayfa kısıtlı).
     Yeniden denemek ister misin? Reklam Kütüphanesi URL'lerini (view_all_page_id=... içeren) yapıştır.

Toplam: {TOPLAM} statik reklam tarandı, {TOPLAM_K} {N} marka genelinde potansiyel kazanan.

Kaydedildi: $RFLAB/03_Ad_Spy/ (mevcut çalışma klasöründe)

Sonraki adım: Herhangi bir 🏆'yi aç → "📋 /rebuild için Kopyala"ya tıkla → /rebuild komutunu çalıştır
```

Özette marka başına erişim, her agent'ın `reach_available` ve `total_reach` alanlarını kullanır. Erişim yoksa `erişim yok ({ÜLKE})` göster; kullanıcı bunun bir pazar sınırlaması olduğunu bilsin, çekme hatası değil. "0 erişim" veya "bilinmeyen erişim" gösterme; bunlar bozuk veri gibi görünür.

---

## competitors.json, tam şema

Yol: `$RFLAB/03_Ad_Spy/competitors.json` (proje bazlı, Adım 0.5'te çözümlenir)

```json
[
  {
    "name": "Huel",
    "slug": "huel",
    "fb_url": "https://facebook.com/huel",
    "ad_library_page_id": "{PAGE_ID}",
    "ad_library_url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&search_type=page&media_type=image&view_all_page_id={PAGE_ID}",
    "logo_url": "https://scontent...",
    "page_title": "Huel",
    "page_categories": ["Page", "Food & beverage company"],
    "niche": "meal replacement",
    "first_seen": "2026-04-25",
    "last_spied": "2026-04-25",
    "swipe_files": ["adspy-huel-20260425.html"],
    "notes": null
  }
]
```

Doğrulamayı sert hata veren markalar için kullanıcının denemeyi görebileceği minimal bir kayıt sakla:

```json
{
  "name": "X Markası",
  "slug": "brandx",
  "fb_url": "https://facebook.com/brandx",
  "ad_library_page_id": null,
  "validation_status": "failed",
  "validation_error": "not_available, sayfa kısıtlı",
  "first_seen": "2026-04-25",
  "last_spied": "2026-04-25",
  "swipe_files": []
}
```

---

## Kesin Kurallar (beceri düzeyi)

| Kural | Ayrıntı |
|---|---|
| **Pages-scraper zorunludur** | Her marka ondan geçer. İstisna yok. Tek markalı istekler de. |
| **REST API yedek yolu zorunludur** | MCP sarmalayıcısının şeması yüklenemezse, `~/.claude/settings.json` dosyasındaki `pluginConfigs["reklam-fabrikasi"].apify_api_key` token'ını `Authorization: Bearer` başlığı olarak kullanarak Apify HTTP API'sini doğrudan çağır. Kullanıcıya Claude'u yeniden başlatmasını söyleme. |
| **Apify token'ını hiçbir zaman URL'ye koyma** | Token her zaman `Authorization: Bearer` başlığında iletilmeli, hiçbir zaman URL sorgu dizisinde olmamalıdır. URL'ye gömülü token'lar kabuk geçmişine ve disk loglarına sızar; v1.3.3'te kaldırıldı. |
| **Yalnızca marka kilitli URL** | Reklam scraper'ı her zaman `view_all_page_id={PAGE_ID}` ile çağrılır. Ham slug'lar yasaktır. |
| **Doğrulama kapısı** | Kişisel profiller, kısıtlı sayfalar, slug uyuşmazlıkları → eyleme dönüştürülebilir hatayla sert hata. Yumuşak uyuşmazlıklar → kullanıcıya sor. |
| **Agent'ta kirlenme kontrolü** | Agent'lar HTML oluşturmadan önce döndürülen tüm reklamların tek bir page_name paylaştığını doğrular. Karışık = başarısız, swipe dosyası yok. |
| **Manuel Reklam Kütüphanesi URL yedek yolu** | Kullanıcı başarısız marka için `view_all_page_id={id}` içeren bir URL yapıştırırsa kabul et ve devam et. |
| **Yalnızca statik** | Videolu tüm reklamları at. URL'de `media_type=image` + snapshot.videos ve snapshot.display_format üzerinde son filtre. |
| **Hiçbir zaman marka değiştirme** | Bir marka kilitlenemezse başarısız olarak işaretle ve kullanıcıya söyle. Hiçbir zaman ikame etme. |
| **Asla veri uydurma** | Yalnızca Apify'ın döndürdüklerini göster. Eksik → eksik olarak işaretle. |
| **`scrapeAdDetails: true` zorunludur** | Her aktör çağrısı bunu geçirir. Olmadan aktör yalnızca reklam kartları döndürür ve swipe dosyası eksik kalır. Yeni nokta-gösterim girdi anahtarları (`scrapePageAds.countryCode` vb.) kullanımdan kaldırılan `-dot-` formunun yerini alır. |
| **Asla erişim sayısı uydurma** | `aaa_info` null olduğunda (AB/İngiltere/Brezilya dışı ticari pazar), komşu reklamlardan erişim sayısını çıkarma, tahmin etme, ortalamasını alma veya alma. Bunun yerine reddi göster ve yayın süresi puanlamasına dayan. |
| **Farklı ülke ile yeniden çekme** | İstenen ülke erişim verisi döndürmüyorsa, erişim sayısı aramak için sessizce COUNTRY=GB veya COUNTRY=DE ile çekmeyi yeniden çalıştırma. Kullanıcının seçtiği ülkeye saygı duy. Kullanıcı AB erişimi istiyorsa açıkça farklı bir ülkeyle ikinci çekmeyi isteyebilir. |
| **Erişim reddi zorunludur** | `REACH_AVAILABLE` false olduğunda swipe dosyası MUTLAKA erişim-kullanılamaz bandını ve alt bilgi notunu içermelidir. Red beklentileri belirler ve kullanıcının çekmenin başarısız olduğunu düşünmesini durdurur. |
| **Yalnızca base64 görseller** | Çıktı HTML'inde hiçbir zaman harici görsel URL'lerine bağlantı verme. |
| **Paralel = tek mesaj** | Çok markalı gönderim, N Agent çağrısıyla tek mesaj olmalıdır. Sıralı = yanlış. |
| **Niş üst sınırı** | Varsayılan 10 marka, maks 15. Bunun üzerinde kullanıcıdan onay iste. |

---

## v1'den ne değişti

| Davranış | v1 (`ad-spy`) | v2.0 (`ad-spy-2.0`) |
|---|---|---|
| Tek markalı girdi için Sayfa ID çözümlemesi | İsteğe bağlı / çoğu zaman atlandı | **Zorunlu** |
| Reklam scraper URL'si | Bazen ham FB slug | **Her zaman `view_all_page_id={id}`** |
| Pages-scraper hatası | Ham URL'ye sessiz geri dönüş → kirlenme | **Eyleme dönüştürülebilir kullanıcı mesajıyla sert hata** |
| Kişisel profil tespiti | Yok | **`categories`'in "Page" içerdiğini doğrular** |
| Slug uyuşmazlığı tespiti | Yok | **Yumuşak uyarı + kullanıcı onayı** |
| MCP şeması yüklenemiyor | Yeniden başlatmaya kadar beceri takılır | **REST API yedek yolu** |
| Kirlenme tespiti | Yok | **Agent içi page_name çeşitliliği kontrolü** |
| Manuel Reklam Kütüphanesi URL kurtarma | Desteklenmez | **Kullanıcı, başarısız markalar için `view_all_page_id` URL'si yapıştırabilir** |
| Tetikleyici ifade | Çoğunlukla nişe odaklı | **Açıkça marka / liste / niş destekler** |

### v1.6.1'de ne değişti (2.0 içinde)

| Davranış | 1.6.1 öncesi | 1.6.1 |
|---|---|---|
| Aktör girdi anahtarları | `scrapePageAds-dot-countryCode` (kullanımdan kaldırılmış -dot- formu) | **`scrapePageAds.countryCode` (güncel nokta-gösterim şeması)** |
| `scrapeAdDetails` bayrağı | Ayarlanmamış, aktör yalnızca reklam kartları döndürüyordu | **Her zaman `true`, `aaa_info`, `transparency_by_location` ve `advertiser.ad_library_page_info`'yu açar** |
| Erişim + kitle verisi | Meta döndürse bile gösterilmiyordu | **`aaa_info` dolu olduğunda reklam başına gösterilir (AB/İngiltere/Brezilya pazarları)** |
| Kazanan puanlaması | Tüm pazarlarda yalnızca gün bazlı | **Dallanmış: AB/İngiltere/Brezilya için erişim + gün, diğer pazarlar için yalnızca gün** |
| Kullanıcı beklenti ayarı | Veri kullanılabilirliğinde sessiz | **Bölge bildirimi alım sırasında yazdırılır (Adım 1.5), swipe dosyasında erişim-kullanılamaz reddi** |
| Toplu özet | Marka başına `N reklam, M kazanan` | **Marka başına `N reklam, M kazanan, X erişim (BÖLGE)` veya `erişim yok (ÜLKE)`** |

---

## Çıktı doğrulama

Bu beceriyi tamamlandı ilan etmeden önce doğrula:

1. Teslimat beklenen yolda mevcut: her marka için `<pwd>/Reklam Fabrikası/03_Ad_Spy/adspy-<slug>-<YYYYMMDD>.html` ve `<pwd>/Reklam Fabrikası/03_Ad_Spy/competitors.json`.
2. Teslimat boş değil (reklam bulunduğunda her HTML dosyası > 30000 bayt).
3. Beklenen içerik sayısı iddia ile eşleşiyor:
   - Bir marka için "N reklam bulundu" dediyse HTML, 0 değil N reklam kartı içeriyor.
   - "M kazanan" dediyse dosya KANITSAL, SICAK, AKTİF veya EMEKLİ rozetli M kart gösteriyor.
   - Kirlenme kontrolü geçti (tüm reklamlar tek bir page_name paylaşıyor).
4. Yer tutucu dize kalmadı:
   - `{NAME}`, `{SLUG}`, `{PAGE_ID}`, `<TODO>` veya `lorem ipsum` yok.
5. Tüm gerekli bölümler dolu:
   - Marka, ülke, tarih, istatistik haplarıyla başlık
   - Rozet, görsel (base64), marka adı, başlık, gövde, CTA, neden-kazanıyor, etiketlerle kart ızgarası
   - Marka kilidi notiyle alt bilgi

Doğrulama başarısız olursa:

1. Önce otomatik düzeltmeyi dene:
   - Bir kartın görseli eksikse (base64 null), curl'ü daha uzun zaman aşımı ve Mozilla User Agent ile yeniden dene.
   - Bir kartın yer tutucu metni varsa neden-kazanıyor bloğunu reklamın metni ve yayın süresinden yeniden oluştur.
   - competitors.json bozuksa bellekteki doğrulanmış marka listesinden yeniden yaz.

2. Otomatik düzeltme başarısız olursa kullanıcıya dürüst bir rapor sun:
   "Ad Spy: <marka> için swipe dosyasını oluşturdum ancak doğrulama <sorun> gösterdi. <düzeltme girişimi>'ni denedim ve bu <işe yaramadı / kısmen işe yaradı>. Eksiksiz sonuç almak için şunları yapabilirsin:
   - Markanın doğrudan Reklam Kütüphanesi URL'sini `view_all_page_id=<id>` ile yapıştır
   - Ülke kodunun markanın gerçekten reklam verdiği yerle eşleştiğini onayla
   - Aynı nişten bir kardeş markayı dene
   Ya da başarıyla oluşturduğum swipe dosyalarından farklı bir marka seç."

3. Apify bir marka için sıfır reklam döndürdüyse:
   - Daha geniş parametrelerle BİR KEZ daha dene:
     - Aktif durum filtresini kaldırarak ve emekli reklamları kabul ederek tarih aralığını son 30 günden son 90 güne genişlet
     - Kullanıcı bir Marka DNA'sı belgesi sağladıysa orada adı geçen doğrudan rakipleri ara
     - Belirli markanın aktif reklamı yoksa sektör anahtar kelimesiyle ara
     - Alternatif reklam formatlarını dene (görsel + video, yalnızca statik değil), ardından yalnızca görsele son filtre uygula
   - Yine sıfırsa dürüst bir rapor sun:
     "Ad Spy: `view_all_page_id=<id>` ile country=<ÜLKE> ve aktif+emekli reklamlar denedim. Apify bu marka için 0 statik reklam döndürdü. Bu genellikle markanın Meta'da şu anda karanlıkta olduğu, yalnızca video kreatif yayınladığı veya farklı bir ülkede yayın yaptığı anlamına gelir. Devam etmek için şunları yapabilirsin:
     - Farklı bir ülke kodu dene (İngiltere, CA, AU)
     - Aynı nişten 2 ile 3 rakip marka adı ver, onları casuslayayım
     - Markayı Meta'da şu an reklam verip vermediğini onayla (önce Reklam Kütüphanesi'nde kendin ara)
     Ya da markayı bulabilirsen doğrudan Reklam Kütüphanesi URL'sini yapıştır."
