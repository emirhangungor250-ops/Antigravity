# Apify marka kilitli reklam çekme, paylaşılan referans

Bu referans, Reklam Fabrikası tarafından kullanılan Apify Facebook Reklam Kütüphanesi çekme işleminin tek doğru kaynağıdır. Statik beceri, markanın kendi reklamlarını çekmek için bunu yükler. Spy becerisi, aynı aktör çağrıları için tek bir bağlantı katmanını paylaşmak amacıyla ilerideki bir sürümde bunu yükleyebilir. Bu yeniden yapılandırma gerçekleşene kadar spy kendi gömülü kopyasını kullanır ve bu belge aynı sözleşmeyi birebir yansıtır.

Çekme marka kilitlidir. Her çağrı, Facebook Pages scraper aracılığıyla çözümlenen `view_all_page_id={PAGE_ID}` kullanır. Slug çakışmaları kirlenmiş sonuçlar döndürdüğünden (benzer adlı kişisel profil veya ilgisiz sayfa) ham slug hiçbir zaman reklam scraper'ına geçirilmez.

Her çağrıdan önce çağıran beceri tarafından doldurulan değişkenler:

- `{{COUNT}}` çekilecek reklam sayısı (statik 20 kullanır, spy 30 kullanır)
- `{{COUNTRY_UPPER}}` büyük harfli ISO ülke kodu (beceri sormadığında varsayılan `US`)
- `{{ACTIVE_STATUS}}` `active`, `inactive` veya `all` (varsayılan `active`)
- `{{SORT_BY}}` `impressions_desc` (varsayılan), `start_date` vb.
- `{{MEDIA_TYPE}}` `image` (varsayılan; yalnızca statik) veya `all`

---

## Adım A.0, Apify MCP'nin Bağlı Olduğunu Doğrula

Araçlarını şimdi kontrol et. `mcp__apify__curious_coder--facebook-ads-library-scraper` görünüyorsa A.1'e geç.

Apify aracı yoksa kullanıcı henüz Apify token'ını girmemiş demektir. Şu mesajı birebir gönder ve DUR:

> Apify henüz bağlı değil. Apify Kişisel API token'ını eklemek için `/reklam-fabrikasi:setup-apify` komutunu çalıştır. Kurulum 30 saniyelik akışı adım adım anlatır ve token'ı kaydetmeden önce Apify API'sine karşı doğrular. Ücretsiz katman ayda 5 $'lık kredi içerir; yaklaşık 6.500 reklamı karşılar. Kurulum tamamlandıktan sonra Claude'u tamamen kapat (Cmd+Q) ve yeniden aç, ardından beceriyi tekrar çalıştır.

MCP sunucusunu kendin kurmaya çalışma, `~/.claude.json` dosyasını düzenleme, kullanıcıdan token'ı buraya yapıştırmasını isteme. Kurulum komutu bunların tamamını halleder ve token'ı eklentinin hassas userConfig alanı aracılığıyla saklar. Bu eklentinin `.mcp.json` dosyasındaki Apify MCP girişi, başlangıçta token'ı `Authorization: Bearer` başlığı olarak enjekte eder. Token hiçbir zaman diskteki bir URL'ye yazılmaz.

Güvenlik notu: 1.3.3'ten önceki sürümlerde spy ve ugc-scraper becerileri kullanıcıdan token'ı buraya yapıştırmasını istiyor ve bunu `~/.claude.json` dosyasına URL sorgu dizisi olarak yazıyordu. MCP yetkilendirme spesifikasyonu tarafından anti-pattern olarak işaretlenen bu yöntemde URL'ye gömülü token'lar kabuk geçmişine, log dosyalarına ve disk durumuna sızıyordu. 1.3.3'ten itibaren token, eklentinin `apify_api_key` userConfig alanında saklanıyor; Claude Code bunu macOS ve Windows'ta işletim sistemi anahtar zincirinde, keychain'in bulunmadığı Linux'ta ise `~/.claude/.credentials.json` dosyasında tutuyor. Düz metin token hiçbir zaman `~/.claude.json` dosyasına yazılmıyor.

---

## Adım A.1, Token'ı settings.json'dan Oku (Yalnızca REST API Yedek Yolu İçin)

MCP sarmalayıcısı çağrılabilir olduğunda token'ı kodda kullanmana gerek yok; MCP girişi onu başlangıçta enjekte eder. Önce A.2 ve A.4'te MCP aracı yolunu kullan.

MCP sarmalayıcısının şeması mevcut oturumda yüklenemediğinde (`ToolSearch` aktör için eşleşme döndürmezse) Apify HTTP API'sine doğrudan geri dön. Token'ı konuşmaya yansıtmadan oku:

```bash
TOKEN=$(python3 -c "import json,os,sys; p=os.path.expanduser('~/.claude/settings.json'); d=json.load(open(p)) if os.path.exists(p) else {}; t=d.get('pluginConfigs',{}).get('reklam-fabrikasi',{}).get('apify_api_key',''); sys.stdout.write(t)")
```

`TOKEN` boşsa kullanıcı henüz kurulumu çalıştırmamış demektir. `/reklam-fabrikasi:setup-apify` komutunu çalıştırmasını söyle ve dur.

Token MUTLAKA aşağıdaki her REST çağrısında `Authorization: Bearer ${TOKEN}` olarak iletilmelidir. Hiçbir zaman URL sorgu dizisine koyma. Token-URL-içine yerleştirme yöntemi v1.3.3'te kaldırıldı.

---

## Adım A.2, Reklam Kütüphanesi Sayfa ID'sini Çöz (ZORUNLU)

Pages-scraper adımı hiç atlanmaz. Tek markalı istekler bile ondan geçer. Spy'ın 2.0 öncesinde kullandığı ham FB URL yaklaşımı, slug'lar kişisel profillerle çakıştığında kirlenmiş sonuçlar döndürüyordu (örn. `facebook.com/kachava` → marka değil "Alcides Kachava" adlı bir kişi).

### A.2a, Başlangıç URL'sini Türet

Çağıran becerinin ilettiği her marka için `{"url": "https://www.facebook.com/{slug}/"}` türet:

- Girdi marka adıysa slug'a dönüştür: küçük harf, boşluk ve özel karakterleri kaldır.
- Girdi Facebook URL'siyse slug'ı URL'den ayrıştır.
- Girdi sayısal Sayfa ID'siyse A.2'yi tamamen atla ve o ID ile A.3'e geç.

### A.2b, Pages Scraper'ı Çağır, Önce MCP

`mcp__apify__apify--facebook-pages-scraper` çağrılabiliyorsa kullan:

```json
{
  "startUrls": [
    {"url": "https://www.facebook.com/{slug}/"}
  ]
}
```

### A.2c, REST API Yedek Yolu

MCP aracının şeması yüklenemezse Apify HTTP API'sini doğrudan çağır:

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
    {"url": "https://www.facebook.com/<SLUG>/"}
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

Çalıştırmadan önce URL'ye gerçek slug'ı yerleştir.

---

## Adım A.3, Doğrulama Kapısı

Pages-scraper'ın döndürdüğü her öğe için sınıflandır:

| Koşul | Karar | İşlem |
|---|---|---|
| `error: not_available` | SERT HATA | Sayfa kısıtlı. Kullanıcıdan doğrudan Reklam Kütüphanesi URL'si iste (A.7'ye bak). |
| `error: no_items` | SERT HATA | Slug mevcut değil. Kullanıcıya söyle, doğru slug veya Reklam Kütüphanesi URL'si iste. |
| `categories` boş VE `pageAdLibrary.id` eksik | SERT HATA | Sayfa değil kişisel profil. Kullanıcıdan markanın doğru Sayfa slug'ını iste. |
| `pageAdLibrary.id` mevcut VE `categories` içinde `Page` var | GEÇTI | Devam et. Logo, başlık ve ad_library_id'yi kaydet. |
| `pageAdLibrary.id` mevcut AMA `title` marka adıyla eşleşmiyor | YUMUŞAK UYARI | Kullanıcıya göster: "`{slug}` adresi `{title}` olarak çözümlendi, doğru marka mı? (evet/hayır)". Onay bekle. |

**Yumuşak uyarı için başlık eşleşme sezgisi:** İkisini de küçük harfe çevir, noktalama ve boşlukları kaldır. Marka adı başlıkta veya başlık marka adında tamamen yer alıyorsa eşleşme say. Aksi hâlde uyar.

### Doğrulama sert hata verdiğinde

Kullanıcıya tam olarak ne olduğunu söyle. Ham URL çekmeye sessizce geri dönme (bu v1'in kirlenme hatasıdır).

> {Brand} tek bir Reklam Kütüphanesi sayfasına kilitlenemedi.
>
> Neden: {hata nedeni, kısıtlı sayfa veya slug bulunamadı veya kişisel profil, vb.}
>
> {Brand} markasını Meta Reklam Kütüphanesi'nde kendin bulabilirsen, doğrudan Reklam Kütüphanesi URL'sini buraya yapıştır (`https://www.facebook.com/ads/library/?...&view_all_page_id=12345...` gibi görünür) ve o ID'yi scraper'dan geçireyim. Aksi takdirde hangi markayı kullanmam gerektiğini söyle.

Kullanıcı `view_all_page_id={id}` içeren bir URL yapıştırırsa ID'yi çıkar ve o markayı id={id} ile GEÇTI olarak kabul et (logo veya başlık yok, yalnızca ID).

---

## Adım A.4, Reklamları Çek, Yalnızca Marka Kilitli URL

URL MUTLAKA `view_all_page_id={PAGE_ID}` içermelidir. Ham sayfa slug'ı hiçbir zaman geçme; bu anahtar kelime-fallback kirlenmesini tetikler.

### A.4a, Önce MCP

`mcp__apify__curious_coder--facebook-ads-library-scraper`'ı şu parametrelerle çağır:

```json
{
  "urls": [{"url": "https://www.facebook.com/ads/library/?active_status={{ACTIVE_STATUS}}&ad_type=all&country={{COUNTRY_UPPER}}&search_type=page&media_type={{MEDIA_TYPE}}&view_all_page_id={PAGE_ID}"}],
  "count": {{COUNT}},
  "scrapeAdDetails": true,
  "scrapePageAds.countryCode": "{{COUNTRY_UPPER}}",
  "scrapePageAds.activeStatus": "{{ACTIVE_STATUS}}",
  "scrapePageAds.sortBy": "{{SORT_BY}}"
}
```

`scrapeAdDetails: true` ZORUNLUDUR. Olmadan aktör yalnızca reklam kartları döndürür; `aaa_info`, `transparency_by_location`, sayfa başına IG hesabı ve `advertiser.ad_library_page_info` bloğu gelmez.

Nokta-gösterim anahtarları (`scrapePageAds.countryCode` vb.) aktörün güncel girdi şemasıdır. Eski `-dot-` formu (`scrapePageAds-dot-countryCode`) kullanımdan kaldırılmıştır; daha yeni aktör derlemelerinde sessizce varsayılanlara düşebilir. Her zaman nokta formunu kullan.

### A.4b, Gerekirse Sayfalama Yap

`totalItemCount > items.length` ise `mcp__apify__get-actor-output` ile sayfalama yap:

```json
{
  "datasetId": "<id>",
  "offset": <alınan öğe sayısı>,
  "limit": <kalan>,
  "fields": "ad_archive_id,page_name,page_id,is_active,start_date,start_date_formatted,end_date,publisher_platform,snapshot.cta_text,snapshot.cta_type,snapshot.display_format,snapshot.body.text,snapshot.title,snapshot.link_url,snapshot.images,snapshot.videos,snapshot.cards,snapshot.page_id,snapshot.page_profile_picture_url,ad_library_url,aaa_info,transparency_by_location,advertiser"
}
```

---

## Adım A.5, Kirlenme Kontrolü

Çektikten sonra, döndürülen tüm reklamlardaki farklı `page_name` değerlerini say.

- TÜM reklamlar AYNI page_name'e sahipse (veya page_name, A.3'teki doğrulanmış PAGE_TITLE ile eşleşiyorsa) GEÇTI, devam et.
- KARIŞIK page_name'ler varsa KİRLENMİŞ. Sonucu KULLANMA. Görülen page_name'lerin listesiyle çağıran beceriye başarısızlık döndür.
- SIFIR reklam varsa çağıran becerinin sıfır-reklam durumunda dallanabilmesi için boş sonuçla başarı döndür.

Tek markalı çağıranlarda (örn. kullanıcının kendi markasını çeken statik beceri) kirlenme hiçbir zaman tetiklenmemeli. Kontrol savunma kodlaması olarak kalır.

---

## Adım A.6, Yalnızca Statik Görsel Filtresi

Reklamı YALNIZCA şunların TAMAMI doğruysa tut:

- `snapshot.videos` boş, null veya eksik
- `snapshot.images` VEYA `snapshot.cards[].original_image_url` VEYA `snapshot.cards[].resized_image_url` içinde en az bir görsel URL var
- `snapshot.display_format != "VIDEO"`

Spy becerisinin kullandığı filtredir. `media_type={{MEDIA_TYPE}}` URL parametresi ile bu son filtre birlikte hiçbir video reklamın geçmemesini garanti eder.

---

## Adım A.7, Manuel Reklam Kütüphanesi URL Yedek Yolu

Bir marka için pages-scraper sert hata verdiyse ve kullanıcı `view_all_page_id={id}` içeren doğrudan Reklam Kütüphanesi URL'si yapıştırdıysa, ID'yi çıkar ve A.2 ile A.3'ü atlayarak doğrudan A.4'ü bu ID ile çağır. Çağıran becerinin logo ve sayfa başlığının mevcut olmadığını bilmesi için markayı `notes: "manually supplied via Ad Library URL"` olarak işaretle.

---

## Bu belgeyi yükleyen tüm beceriler için kesin kurallar

| Kural | Ayrıntı |
|---|---|
| Pages-scraper zorunludur | Her marka ondan geçer. İstisna yok. Tek markalı çağıranlarda da. |
| REST API yedek yolu zorunludur | MCP sarmalayıcısının şeması yüklenemezse, `~/.claude/settings.json` dosyasındaki `pluginConfigs["reklam-fabrikasi"].apify_api_key` token'ını `Authorization: Bearer` olarak kullanarak Apify HTTP API'sini doğrudan çağır. Kullanıcıya Claude'u yeniden başlatmasını söyleme. |
| Apify token'ını hiçbir zaman URL'ye koyma | Token her zaman `Authorization: Bearer` başlığında iletilmeli, hiçbir zaman URL sorgu dizisinde olmamalıdır. |
| Yalnızca marka kilitli URL | Reklam scraper'ı her zaman `view_all_page_id={PAGE_ID}` ile çağrılır. Ham slug'lar yasaktır. |
| Doğrulama kapısı | Kişisel profiller, kısıtlı sayfalar, slug uyuşmazlıkları, eyleme dönüştürülebilir hatayla sert hata. Yumuşak uyuşmazlıklar, kullanıcıya sor. |
| Kirlenme kontrolü | Karışık page_name'ler, başarısız. |
| `{{MEDIA_TYPE}}` `image` olduğunda yalnızca statik | URL parametresini geçse bile video içerikli tüm reklamları at. |
| Asla veri uydurma | Yalnızca Apify'ın döndürdüklerini göster. Eksik, eksik olarak işaretle. |
| `scrapeAdDetails: true` zorunludur | Her aktör çağrısı bunu geçirir. |
