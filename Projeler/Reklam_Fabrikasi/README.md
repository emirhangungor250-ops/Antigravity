# Reklam Fabrikası

> **Bu bir şablondur.** DTC (doğrudan tüketiciye satan) markalar için uçtan uca reklam üretim
> sistemi: müşteriyi araştır, markayı çıkar, neyin kazandığını incele, kreatif üret, kazananı
> çoğalt. İçinde gerçek API anahtarı veya kişisel veri yoktur; tüm değerler senin dolduracağın
> `<...>` placeholder'larıdır. Bu desen, ajans/freelancer/içerik üreticisi olarak birden çok
> markaya düzenli reklam kreatifi üreten herkes için çalışır. Kurulum için önce `.env.example`'ı
> oku, sonra eklentiyi Claude Code'a ekle.

Meta ve ötesinde ücretli reklam yayınlayan DTC markaları için tam kreatif döngüsünü bir araya getiren, özel Claude Code eklenti marketplace'i. Ayrıca, claude.ai web uygulamasında çalışan Meta'nın mcp.facebook.com/ads adresindeki resmi Ads MCP'sine zengin bağlamlı promptlar hazırlayan bir aktarım iş akışı içerir. Müşteri sesi araştırması, marka DNA'sı çıkarımı, reklam casusu, marka karakter yayınlaması, ürün fotoğrafı üretimi, statik reklam üretimi, UGC senaryolaştırma, yüz tutarlılıklı UGC video, reklam metni, reklam çoğaltma, rakip yeniden yapılandırma, tek dosya HTML açılış sayfaları ve canlı Meta kampanya çalışmasına yapılandırılmış aktarım; tek bir kurulumun arkasında.

## Sürüm öncesi doğrulama

Herhangi bir sürüm artışını yayınlamadan önce, eklenti manifest'ini Claude Code'un belgelenmiş şemasına karşı doğrula:

```
python3 scripts/validate-manifest.py
```

Betik, bilinmeyen anahtarlar, eksik zorunlu alanlar, geçersiz `userConfig` türleri ve üç dosya arasındaki sürüm farklılığı için `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` ve `package.json`'u kontrol eder. Başarıda 0, herhangi bir başarısızlıkta belirli dosya ve alan hatasıyla 1 ile çıkar. Manifest'e dokunan her push öncesinde çalıştır.

İki otomasyon katmanı bunu destekler:

- `.git/hooks/pre-commit` adresindeki yerel pre-commit kancası, her commit'te doğrulayıcıyı çalıştırır ve başarısız olursa commit'i engeller. Kanca makine başınadır ve git tarafından takip edilmez; dolayısıyla yeni bir klonda mevcut kancasının gövdesini kopyalayarak (veya `python3 scripts/validate-manifest.py` çalıştıran eşdeğer shell'i yapıştırarak) ve `chmod +x .git/hooks/pre-commit` ile kurulu hale getir.
- `.github/workflows/validate-manifest.yml` adresindeki GitHub Actions iş akışı, `main`'e her push ve `main`'i hedefleyen her pull request'te aynı betiği çalıştırır. Başarısız doğrulama, iş akışını başarısız kılar ve birleştirmeyi engeller. Bu gerçek uygulama katmanıdır; yerel kanca hızlı hata kolaylığıdır.

Doğrulama kuralları, v1.3.4 kurulum regresyonunu tetikleyen izin verilen `userConfig` giriş anahtarları (https://code.claude.com/docs/en/plugins-reference adresinden alınan) dahil olmak üzere `scripts/validate-manifest.py` içinde satır içi olarak belgelenmiştir.

## Beceriler

Bir koruma becerisiyle birlikte iş akışı aşamasına göre düzenlenmiş on üç kreatif döngü becerisi:

### Araştırma (paralel çalıştır)

- `reklam-fabrikasi-voc`, müşteri sesi araştırması, `./Reklam Fabrikası/01_VOC_Research/` konumuna çıktı verir
- `reklam-fabrikasi-brand-dna`, Playwright renk örneklemesiyle canlı marka DNA'sı çıkarımı, `./Reklam Fabrikası/02_Brand_DNA/` konumuna çıktı verir
- `reklam-fabrikasi-spy`, statik reklam swipe dosyaları için Meta Reklam Kütüphanesi tarayıcısı, `./Reklam Fabrikası/03_Ad_Spy/` konumuna çıktı verir
- `reklam-fabrikasi-ugc-scraper`, swipe dosyaları için viral TikTok UGC tarayıcısı

### Karakter yayınlama ve varlık hazırlama (marka DNA'sından sonra)

- `reklam-fabrikasi-character`, çalışma başına 1-10 marka karakteri; eşleşen kıyafet fotoğrafı artı `./Reklam Fabrikası/11_Characters/<isim>/` altında 3:4 2K'da tam vücut yayını. Tüm reklamlarda tutarlılık için yüz referansı olarak ürün fotoğrafına ve ugc-prompt'a beslenir. Dört üretim yolu.
- `reklam-fabrikasi-product-shot`, tek kaynak ürün görselinden stüdyo, tutulmuş veya giyilmiş ürün fotoğrafları. Tek çıpa fotoğrafı artı açı, karakter, arka plan ve etkileşim değişimleri için v1 sonrası döngü. `./Reklam Fabrikası/_assets/product-shots/<cikti-adi>/` konumuna çıktı verir. Dört üretim yolu.

### Kreatif üretim (araştırmadan sonra, paralel çalıştır)

- `reklam-fabrikasi-static`, kanıta dayalı statik reklam konsept sistemi. Apify aracılığıyla markanın son 20 canlı Meta reklamını tarar, Marka DNA'sı ve VOC'u işler, web aramasıyla Kreatif Araştırma ve Strateji Motorunu çalıştırır, sohbette onay/reddet/düzenle için düz metin olarak 6-10 konsept sunar, ardından 5 sabit görsel aile genelinde onaylanan konsept başına 5 GPT Image 2 render promptu yazar. Yalnızca GPT Image 2. Dört üretim yolu.
- `reklam-fabrikasi-ugc-prompt`, dört üretim yoluyla UGC senaryosundan 6 Seedance 2.0 video promptu. Projede kaydedilmiş karakterler varsa beceri, tüm 6 varyant genelinde tek bir karakteri kilitler; böylece her video aynı kreatiflerin yüzle eşleştirilmiş varyasyonu olarak okunur.

### Optimizasyon yan döngüleri (isteğe bağlı, paralel çalıştır)

- `reklam-fabrikasi-multiplier`, dört üretim yoluyla kazanan statik reklamın 5-8 Andromeda dostu varyasyonu
- `reklam-fabrikasi-rebuild`, dört üretim yoluyla bir rakibin kazanan statik reklamını referans görsel promptu olarak yeniden yapılandırma (GPT Image 2 önerilir, ucuz alternatif olarak Nano Banana 2)

### Dağıtım

- `reklam-fabrikasi-copy`, Meta reklam başlıkları, açıklamaları, ana metni

### Hedef

- `reklam-fabrikasi-landing-page`, kazanan reklamdan artı Marka DNA'sı artı VOC'tan, mesaj eşleştirme uygulaması, marka token enjeksiyonu, Meta Piksel iskeleti ve yazmadan önce 34 noktalı anti-AI özeleştirisiyle tek dosya HTML açılış sayfası. `./Reklam Fabrikası/10_Landing_Pages/` konumuna çıktı verir

### Canlı Meta Reklamları (aktarım iş akışı)

- `reklam-fabrikasi-meta-handoff`, proje bağlamınızı (Marka DNA'sı, VOC, metin, reklam özelliği) claude.ai web uygulaması içinde çalışan mcp.facebook.com/ads adresindeki Meta'nın resmi Ads MCP'si için yapıştırmaya hazır bir prompta paketler

## MCP sunucuları

Eklentiyle birlikte dört MCP sunucusu gelir:

| Sunucu | Taşıma | Amaç |
|---|---|---|
| `apify` | HTTP | Reklam casusu ve UGC tarayıcısı için kazıma |
| `playwright` | Yerel Node | Marka DNA'sı ve Yol D üretimi için tarayıcı otomasyonu |
| `fal-ai` | HTTP | Yol C üretimi için sonuç başına ödemeli görsel ve video modeller |
| `higgsfield` | HTTP | Yol B üretimi için abonelik tabanlı görsel ve video modeller |

## Dört yol kalıbı

Üretim becerileri dört paralel yol sunar; kullanıcı araçlara ve bütçeye göre seçer:

1. **Yol A, Kendin Yap yapıştırma.** Beceri promptları yazar ve kullanıcı bunları model arayüzüne kendisi yapıştırır.
2. **Yol B, Higgsfield MCP.** Higgsfield aboneliği olan kullanıcılar için. Claude, resmi Higgsfield MCP sunucusu aracılığıyla üretir; ilk kullanımda `/mcp` üzerinden OAuth girişi.
3. **Yol C, fal.ai doğrudan API.** Claude, fal-ai MCP aracılığıyla modeli çağırır; sonuç başına ödeme, abonelik gerekmez.
4. **Yol D, Playwright web arayüzü otomasyonu.** Claude, ilgili web arayüzünü tarayıcıda açar, promptu yapıştırır, medyayı ekler ve her adımda açık kullanıcı onayıyla Oluştur'a tıklar. Otomatik yükleme yok, "evet" olmadan Oluştur'a tıklama yok.

Statik, yeniden yapılandırma, çoğaltıcı, karakter, ürün fotoğrafı ve ugc-prompt'un tümü bugün dört yolu destekliyor.

## Önerilen görsel model

Statik beceri, `quality: "high"` ve 4K eşdeğer `image_size` ayarında GPT Image 2'ye (`openai/gpt-image-2/edit` fal.ai'de) sabit kodlanmıştır. Model seçici yok. Diğer tüm görsel üretim becerileri (çoğaltıcı, yeniden yapılandırma, karakter, ürün fotoğrafı), varsayılan olarak GPT Image 2 ve ucuz alternatif olarak Nano Banana 2 içeren bir model seçici sunar. GPT Image 2, şu anda mevcut en iyi görsel üretim modelidir; ürün ayrıntısı, metin oluşturma, yüz tutarlılığı ve karmaşık promptlarda Nano Banana 2 ve Nano Banana Pro'nun önündedir.

Nano Banana 2 (`fal-ai/nano-banana-2/edit`), üretim başına daha düşük maliyet isteyen kullanıcılar için ucuz alternatif olarak mevcut. Onu seçmenin tek nedeni daha ucuz maliyettir. v1.5.0 yapısında GPT Image 2 yerine Nano Banana 2 için kalite gerekçesi yok.

Her iki model da dört üretim yoluna bağlıdır. GPT Image 2 için fal.ai Yol C uç noktası `safety_tolerance` parametresini kabul etmez (yalnızca Nano Banana ailesi kabul eder); dolayısıyla bağlantı, her GPT Image 2 çağrısında bunu atlar.

## Aktarım yoluyla canlı Meta kampanya çalışması

Meta, resmi Ads MCP'sini 29 Nisan 2026'da `mcp.facebook.com/ads` adresinde yayınladı. O MCP yalnızca claude.ai web uygulaması içinde çalışır çünkü Meta'nın OAuth istemcisi yalnızca `https://claude.ai/api/mcp/auth_callback` yönlendirme URI'sini beyaz listeye alıyor. Claude Code bu geri çağırmayı alamaz; dolayısıyla canlı Meta kampanya yönetimi Claude Code'un kendisi içinde çalışamaz.

Boşluğu kapatmak için `reklam-fabrikasi-meta-handoff` becerisi, kullanıcının claude.ai'de yeni bir sohbete yapıştırdığı zengin bağlamlı bir prompt hazırlar. Aktarım, kullanıcının Claude Code'da inşa ettiği her şeyi (Marka DNA'sı, VOC, reklam metni, image_hash veya post_id referansları) bir araya getirir ve seçilen moda göre alıcı Claude'u profesyonel bir Meta reklamları analisti veya profesyonel bir Meta reklamları stratejisti olarak yapılandırır. Kullanıcının makinesinde Meta kimlik bilgisi yaşamaz. Kimlik doğrulama, claude.ai'nin kendisi içindeki Meta'nın OAuth akışıdır.

## Kurulum

Ön koşullar:

- Claude Code (en güncel)
- Node.js 20 veya üstü
- Yol C görsel ve video üretimi için Fal AI API anahtarı (https://fal.ai/dashboard/keys)
- Reklam casusu ve UGC tarayıcı becerileri için Apify API token'ı (https://console.apify.com/account/integrations); başlamak için ücretsiz katman yeterli
- İsteğe bağlı: Yol B üretimi için Higgsfield aboneliği

Eklentiyi Claude Code'a ekle, ardından makine kurulumunu tamamlamak için `/reklam-fabrikasi:setup` komutunu bir kez çalıştır. Her şeyin sağlıklı olduğunu doğrulamak için istediğin zaman `/reklam-fabrikasi:doctor` kullan.

## Çıktı klasör yapısı

Her beceri teslim edilebilir dosyalarını Claude Code'un açık olduğu klasördeki `./Reklam Fabrikası/` altında numaralı bir alt klasöre yazar. Her marka veya müşteri kendi tam çıktı yapısını alır. Bir müşteri için `~/Desktop/<MARKA_A>/` ve diğeri için `~/Desktop/<MARKA_B>/` klasörlerinde Claude Code'u aç; ikisi hiçbir zaman karışmaz.

```
~/Desktop/<MARKA_A>/                  (proje klasörün)
└── Reklam Fabrikası/                    (ilk beceri çalıştırmasında otomatik oluşturulur)
    ├── 01_VOC_Research/              reklam-fabrikasi-voc
    ├── 02_Brand_DNA/                 reklam-fabrikasi-brand-dna
    ├── 03_Ad_Spy/                    reklam-fabrikasi-spy
    ├── 04_Static_Ads/                reklam-fabrikasi-static
    ├── 05_UGC/
    │   ├── scraper/                  reklam-fabrikasi-ugc-scraper
    │   └── prompts/                  reklam-fabrikasi-ugc-prompt
    ├── 06_Ad_Copy/                   reklam-fabrikasi-copy
    ├── 07_Multiplied_Ads/            reklam-fabrikasi-multiplier
    ├── 08_Rebuilt_Competitor_Ads/    reklam-fabrikasi-rebuild
    ├── 09_Meta_Handoff/              reklam-fabrikasi-meta-handoff
    ├── 10_Landing_Pages/             reklam-fabrikasi-landing-page
    ├── 11_Characters/                reklam-fabrikasi-character (karakter başına kıyafet.png + tamvucut.png + character-spec.json alt klasörü)
    ├── _assets/
    │   ├── product-images/           ham ürün görsel yüklemeleri, kullanıcı tarafından bırakılan
    │   └── product-shots/            reklam-fabrikasi-product-shot (çıktı adı başına _v1.png, _v2.png, product-shot-spec.json alt klasörü)
    └── _meta/                        proje başına durum (state.json, folder-confirmed.flag)
```

Claude Code'u markaya özel klasörde aç. Her marka kendi tam çıktı yapısını alır. Beceriler aynı proje klasöründeki önceki çıktıları otomatik keşfeder; bir marka klasöründe statik reklam istediğinde eklenti orada kaydedilmiş o markanın VOC ve Marka DNA'sı belgelerini kullanır.

Makine düzeyinde durum (kurulum günlükleri, kurulum bayrakları, Meta Reklamları Python sanal ortamı, CLI PATH sembolik bağlantı bayrağı) `~/Reklam-Fabrikasi/_meta/` konumunda yaşar. Bu ağaç makine başınadır ve tüm proje klasörlerinde paylaşılır. Proje çalışması klasör başınadır; makine durumu makine başınadır.

## Kreatif döngü

Her kullanıcı aynı döngüyü takip eder. Müşteriyi araştır, markayı çıkar, neyin kazandığını incele, üç formatta kreatif yayınla (statik, UGC, metin), ardından kazananları çoğalt ve yeniden yapılandır. Döngü dönmeye devam eder çünkü her çıktı bir sonraki girdiye beslenir. `scripts/chain-map.json` adresindeki zincir haritası, `/next` komutunun doğru bir sonraki adımı önerebilmesi için her beceri için girdileri, çıktıları, paralelliği ve MCP bağımlılıklarını kodlar.

## Bilinen tuhaflıklar

- macOS Claude Code masaüstü uygulaması CLI ikili dosyasını kullanıcı PATH'inde değil, `~/Library/Application Support/Claude/claude-code/<sürüm>/claude.app/Contents/MacOS/claude` konumunda tutar. Eklenti, ilk SessionStart'ta otomatik olarak sembolik bağlantı oluşturur; böylece `claude` her yeni shell'de çalışır. Hiç `claude: command not found` görürsen, düzeltmek için `/reklam-fabrikasi:repair-path` çalıştır.

## Destek

Sorular, hatalar veya özellik istekleri topluluk kanalına iletilir.
