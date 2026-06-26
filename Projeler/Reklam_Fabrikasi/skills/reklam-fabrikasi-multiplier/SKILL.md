---
name: reklam-fabrikasi-multiplier
description: "Kullanıcı /multiply, /multiply ads, /ad variations, /more variations, /multiply winner yazıyorsa ya da kazanan bir statik reklamı çoğaltmak, kazanan reklamın daha fazla varyasyonunu üretmek, kazananı ölçeklendirmek veya zaten çalışan bir reklamın daha fazla Andromeda uyumlu versiyonunu almak istediğini söylüyorsa bu beceriyi kullan. Kullanıcının kendi kazanan statik reklam görselini, 1 ila 3 ürün görselini, bir Marka DNA'sı belgesini ve bir VOC araştırma belgesini alır; ardından 5 ila 8 adet tam yazılmış referans görsel promptu üretir. Her varyasyonun farklı bir açısı, kancası, farkındalık düzeyi VE gerçek anlamda farklı bir görsel sahnesi vardır; böylece Meta'nın Andromeda algoritması her varyasyonu kendi Entity ID'sine sahip ayrı bir reklam olarak değerlendirir. Model seçici: GPT Image 2 (önerilen, yüksek kalite, 4K eşdeğeri image_size, fal.ai üzerinden openai/gpt-image-2/edit) veya daha ucuz alternatif olarak Nano Banana 2. Kullanıcı kazanan bir reklamı çoğaltmaktan, kazananı ölçeklendirmekten, daha fazla versiyon üretmekten, Andromeda varyasyonları oluşturmaktan veya zaten çalışan bir reklamdan daha fazla reklam almak istediğinden bahsettiğinde bu beceriyi her zaman tetikle."
---

# Reklam Fabrikası, Kazanan Reklam Çoğaltıcı 2.0

Bu beceri, kullanıcı için zaten kazanan bir statik reklamı alır ve 5 ila 8 Andromeda uyumlu referans görsel promptuna dönüştürür. Her varyasyon, orijinal reklamın dönüşüm mekaniğini (işe yarıyor olmasının sebebini) korurken görsel sahne, renk dünyası, kanca açısı ve metinde bilinçli farklılıklar yaratır. Böylece Meta her varyasyonu gerçekten yeni bir reklam olarak değerlendirir, bir kopya olarak değil.

Kullanıcı kazanan reklam görselini kompozisyonel referans olarak yükler, 1 ila 3 ürün görseli yükler ve varyasyon promptlarını birer birer yapıştırır. Her varyasyon yeni bir reklam üretir. Aynı marka, aynı ürün, farklı görsel dünya. Varsayılan model yüksek kalitede ve 4K eşdeğeri `image_size` ile GPT Image 2'dir. Nano Banana 2 daha ucuz alternatif olarak kullanılabilir.

---

## Bu beceri neden var

Meta'nın Andromeda algoritması benzer görsel gömmelere sahip reklamları aynı Entity ID altında gruplar ve açık artırmada bunlardan yalnızca birini gösterir. Kullanıcı aynı sahneyi, renk paletini ve kompozisyonu paylaşan 8 reklam üretirse (sadece farklı metinlerle), Andromeda bunları tek reklam olarak değerlendirir ve diğer 7'sini baskılar.

1 yerine 8 açık artırma bileti almak için her reklamın hem stratejik açıdan hem de içinde yaşadığı görsel dünya açısından gerçekten farklı olması gerekir.

Bu beceri, orijinal reklamı kazandıran dönüşüm mekaniğini korurken Andromeda'nın tekilleştirme sürecini geçen varyasyonlar üretir.

---

## Adım 0, Proje çıktı klasörünü çöz + önceki çalışmaları otomatik keşfet

Çıktılar, Claude Code'un açık olduğu çalışma klasörüne kaydedilir. Önce bu Bash bloğunu çalıştır:

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
  mkdir -p "$TARGET/07_Multiplied_Ads/path_b_outputs" "$TARGET/07_Multiplied_Ads/path_c_outputs" "$TARGET/07_Multiplied_Ads/path_d_outputs" "$TARGET/_meta"
  echo "READY:$TARGET"
fi

# Marka klasörü varsa ve CLAUDE.md dosyası eksikse marka belleğini (CLAUDE.md) oluştur.
# Yapacak bir şey yoksa sessizce çalışır ve idempotent davranır.
if [ -d "$TARGET" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" ]; then
  bash "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi
```

- `PROTECTED:<path>`: Reddet ve kullanıcıya Claude Code'u markaya özel bir alt klasörde açmasını söyle. Dur.
- `FIRSTRUN:<path>`: "Çıktıları `<path>/` konumuna kaydedeceğim. Bu klasöre ilk kez kaydediyorum, doğru mu? (evet/hayır)" diye sor. Evet derlerse klasörleri oluştur (`07_Multiplied_Ads` altında `path_b_outputs`, `path_c_outputs` ve `path_d_outputs` dahil) ve `<path>/_meta/folder-confirmed.flag` dosyasını yaz. Hayır derlerse dur.
- `READY:<path>`: Sessizce devam et.

Çözülen yolu `$RFLAB` olarak yakala.

Otomatik keşif: `$RFLAB/01_VOC_Research/` ve `$RFLAB/02_Brand_DNA/` klasörlerini en son dosyalar için tara. Bulunurlarsa, yeni yükleme istemek yerine bunları kullanıcıya öner:

```
ls -t "$RFLAB/01_VOC_Research/"*.html "$RFLAB/01_VOC_Research/"*.md 2>/dev/null | head -n 1
ls -t "$RFLAB/02_Brand_DNA/"*.html "$RFLAB/02_Brand_DNA/"*.md 2>/dev/null | head -n 1
```

Kullanıcıya hangi dosyaları bulduğunu ve hangilerini (varsa) sağlaması gerektiğini söyle. Proje klasöründe hiçbiri yoksa belgeleri aşağıda listelendiği gibi yüklemelerini iste.

## Kullanıcının Sağlaması Gerekenler

Kullanıcı bu beceriyi etkinleştirdiğinde, tek bir mesajda her şeyi iste:

> Kazanan reklamını çoğaltmak için dört şeye ve üç hızlı cevaba ihtiyacım var:
>
> **1. Kazanan reklamın** bu sohbete statik görseli doğrudan yapıştır veya yükle. Bu, senin için zaten performans gösteren reklam.
>
> **2. Ürün görsellerin** ürünün reklamlarda görünmesi gereken haliyle 1 ila 3 fotoğraf yükle. Bunlar her varyasyonda kullanılacak.
>
> **3. VOC araştırma belgen** tam metni yapıştır veya dosyayı yükle
>
> **4. Marka DNA'sı belgen** tam metni yapıştır veya dosyayı yükle
>
> **5. Kaç varyasyon istiyorsun?** 5 ile 8 arasında bir sayı seç. Daha fazla varyasyon, daha fazla açık artırma bileti demektir ama inceleme için de daha fazla çalışma gerektirir.
>
> **6. Eklemek istediğin belirli bir kampanya, teklif veya promosyon var mı?** Örneğin indirim, paket, ücretsiz deneme, lansman teklifi veya belirli bir harekete geçirici mesaj. Varsa kısaca açıkla. Yoksa "teklif yok" de ve varyasyonlar ürüne ve marka konumlandırmasına odaklanır.
>
> **7. Teklif her varyasyonda mı görünsün, yoksa yalnızca bir kısmında mı?** Teklifi her reklamda istiyorsan "tüm varyasyonlar" de. Bir karışım istiyorsan (bir kısmında teklifli, bir kısmında teklifsiz) "karışık" de.
>
> Dört girişi ve 5, 6 ile 7. sorulara cevaplarını birlikte yaz.

Kazanan reklam görseli, en az bir ürün görseli, Marka DNA'sı belgesi ve VOC belgesi olmadan devam etme. Herhangi biri eksikse tekrar sor.

---

## İş Akışı, Üç Aşama

---

### AŞAMA 1, Kazanan Reklamı Analiz Et

Kazanan reklam görselini dikkatle oku. Analiz çerçevesini şuradan yükle:
`references/ad-analysis.md`

Tam olarak takip et. Bu aşamanın amacı, yeniden inşa becerisinden farklıdır. Burada reklamı klonlamak için çıkarım yapmıyorsun. Çıkardıkların şunlar:
- Yapısal iskelet (varyasyonlar boyunca korunması gereken düzen deseni)
- Dönüşüm mekaniği (bu reklamın işe yarıyor olmasının sebebi, her varyasyonda mutlaka korunmalı)
- Mevcut kanca, farkındalık düzeyi ve açı (böylece varyasyonlar bilinçli olarak FARKLI olanları seçebilir)
- Görsel sahne ve renk dünyası (böylece varyasyonlar bilinçli olarak bunlardan uzaklaşabilir)

Tam analizi kullanıcıya gösterme. Aşama 1 sonrasında kullanıcıya şunu söyle:
> "Kazananın analizi tamamlandı. Şimdi varyasyon stratejin oluşturuluyor..."

---

### AŞAMA 2, Varyasyon Stratejisi Oluştur

Varyasyon motorunu şuradan yükle:
`references/variation-engine.md`

Tam olarak takip et. VOC belgesi, Marka DNA'sı belgesi ve Aşama 1 analizini kullanarak her varyasyon için bir satır içeren bir strateji tablosu oluştur (kullanıcının istediği sayıya göre toplamda 5 ila 8 satır).

Her satır şunları belirtmeli:
- **Varyasyon numarası**
- **Metin açısı** (hangi VOC acı noktası, istek veya içgörü mesajı yönlendiriyor)
- **Kanca mekaniği** (merak boşluğu, cesur iddia, desen kesintisi, ilişkilendirilebilirlik, sosyal kanıt, korku/kayıp, özlem)
- **Farkındalık düzeyi** (Habersiz, Sorun-Farkında, Çözüm-Farkında, Ürün-Farkında, En-Farkında)
- **Duygusal kayıt** (bu reklamın etkinleştirdiği baskın his)
- **Görsel sahne** (bu varyasyonun içinde yaşadığı belirli, özgün bir sahne)
- **Renk dünyası** (baskın palet ve atmosfer, diğer varyasyonlardan farklı)
- **Orijinalden ayırt edici fark** (bu varyasyonun kullanıcının kazanan reklamından ve diğer her varyasyondan gerçek anlamda nasıl farklı olduğuna dair tek cümle)

Strateji tablosunu promptları yazmadan önce kullanıcıya göster. Onaylamalarını veya düzenlemelerini iste. Kullanıcı onaylamadan Aşama 3'e geçme.

---

### AŞAMA 3, Referans Görsel Promptlarını Yaz

Prompt oluşturma kılavuzunu şuradan yükle:
`references/prompt-builder.md`

Kullanıcı stratejiyi onayladığında, 5 ila 8 adet tam referans görsel promptu yaz. Promptlar model agnostiktir; hem GPT Image 2 (varsayılan) hem de Nano Banana 2 (daha ucuz alternatif) ile çalışır. Her prompt şunları yapmalı:

- Kullanıcının kazanan reklam görselini marka ve kalite referansı olarak referans almalı
- Kullanıcının ürün görsellerini render edilecek ürün olarak referans almalı
- Orijinalden ve diğer her varyasyondan gerçek anlamda farklı bir görsel sahne belirtmeli
- Tüm metin tam olarak yazılmış olmalı, yer tutucu veya doldurulmamış parantez bulunmamalı
- Mümkün olan her yerde VOC belgesinden birebir müşteri dilini kullanmalı
- Marka DNA'sının ses tonu, renk ve estetik sınırları içinde kalmalı
- Seçilen görsel modele (GPT Image 2 veya Nano Banana 2) sıfır düzenlemeyle yapıştırılmaya hazır olmalı

Her varyasyonu açıkça numaralandır ve etiketle:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VARİYASYON 1, [Açı adı]
Farkındalık Düzeyi: [düzey]
Kanca: [mekanik]
Duygu: [kayıt]
Görsel Sahne: [kısa açıklama]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Tam prompt buraya]
```

---

## Çıktı Formatı

Çıktıyı şu sırayla sun:

1. **KAZANAN REKLAM ANALİZ ÖZETİ** orijinal reklamı neyin işe yaradığına dair 4 ila 6 satırlık kısa ve stratejik bir özet (kanca türü, düzen, dönüşüm mekaniği, farkındalık düzeyi). Kullanıcıya gösterilir.

2. **VARİYASYON STRATEJİ TABLOSU** 5 ila 8 varyasyonun tamamını kapsayan strateji tablosu. Bunu göster ve kullanıcı onayını bekle.

3. **VARİYASYON PROMPTLARI** 5 ila 8 adet tam referans görsel promptu, tam olarak yazılmış, açıkça numaralandırılmış ve etiketlenmiş. Bunları yalnızca kullanıcı strateji tablosunu onayladıktan sonra üret. Promptlar model agnostiktir; GPT Image 2 veya Nano Banana 2'ye yapıştırılabilir.

---

## Kurallar

- **Görsel varyasyon zorunludur.** Her varyasyon anlamlı biçimde farklı bir sahne ve renk dünyası belirtmelidir. Aynı sahne farklı metinle eşittir tek Andromeda Entity ID'si. Farklı sahne eşittir yeni Entity ID eşittir yeni açık artırma bileti. Bu becerinin tüm amacı budur.
- **Dönüşüm mekaniğini koru.** Her varyasyon, orijinal reklamın işe yarıyor olmasının yapısal sebebini gözetmelidir. Orijinal cesur bir sonuç iddiası formatıyla kazanıyorsa, her varyasyonun açı farklı olsa bile güçlü bir iddiası olmalıdır. Orijinal bir referans düzeniyle kazanıyorsa, her varyasyonun sosyal kanıtı olmalıdır. Mekanik reklamın DNA'sıdır.
- **İki varyasyon anlamsal olarak aynı olamaz.** İki varyasyon aynı temel mesajı aynı kitleye aynı görsel bağlamda iletiyorsa Andromeda onları kümeleyecektir. İkisi çok yakınsa, devam etmeden önce birini değiştir.
- **İki varyasyon aynı kanca mekaniğini VEYA farkındalık düzeyini VEYA görsel sahneyi paylaşamaz.** Her üçünün de varyasyon seti boyunca ayrı olması gerekir.
- **Kelime sayısı rehber, kilitleyici değil.** Orijinal kazanan reklamın kelime sayılarını görsel denge için referans olarak kullan. Mümkün olduğunda eşleştir (başlıklarda artı veya eksi 2 kelime, harekete geçirici mesajlarda ve rozette artı veya eksi 1 kelime). Kelime uzunluğunu açıyı feda edecek kadar kilitleme. Tüm amaç varyasyondur.
- **Her kelimeyi belgelere dayandır.** Tüm değiştirme metni Marka DNA'sı belgesinden (ses tonu, konumlandırma, ürün detayları) ve VOC belgesinden (müşteri dili, acı noktaları, istekler) gelmelidir. Genel ve uydurma reklam metni yasak.
- **Strateji tablosunu önce göster.** Kullanıcı varyasyon stratejisini onaylayana kadar tam promptları asla yazma. Bu, kullanıcı açıları, sahneler veya kancaları değiştirmek isterse boşa harcanan çalışmayı önler.
- **Ürün görselleri ürünü taşır.** Kullanıcının ürün görselleri, kazanan reklam referansının yanı sıra görsel modele yüklenir. Her prompt, modele yüklenen ürün görsellerinden ürünü yeni sahnede doğal biçimde yerleştirilmiş olarak render etmesini talimatlandırmalıdır. Modelden ürünü hayal gücüyle yeniden yaratmasını isteme.

---

## Görsel modelini seç

Varyasyon promptlarını sunduktan sonra kullanıcıya şu soruyu sor:

> Varyasyonlar için hangi görsel modeli kullanayım?
>
> **1. GPT Image 2** (önerilen). Yüksek kalite, 4K eşdeğeri `image_size` (kare çoğaltıcı çıktılar için varsayılan 2880x2880, fal.ai'nin GPT Image 2 uç noktasının 8,3 megapiksel sınırı altında kabul ettiği en büyük 1:1 boyut). Şu anda mevcut en iyi görsel üretim modeli. Ürün detayı, metin render, yüz tutarlılığı ve karmaşık promptlarda Nano Banana 2 ve Nano Banana Pro'dan üstün.
> **2. Nano Banana 2.** Üretim başına daha düşük maliyet isteyen kullanıcılar için daha ucuz alternatif. Seçmek için tek neden ucuzluğu; GPT Image 2 her kalite ekseninde kazanıyor.
>
> `1`, `2` yaz veya GPT Image 2 için `varsayılan` de.

`$MODEL` olarak yakala. Varsayılan `gpt-image-2`.

---

## Üretim yolunu seç

Model seçildikten sonra kullanıcıya şu soruyu sor:

> Varyasyon promptların hazır, model `$MODEL`. Görselleri gerçekten nasıl üretmek istiyorsun?
>
> **A. Manuel yapıştırma.** Ücretsiz. Promptları kopyala, kendi başına modelin web arayüzüne yapıştır, kazanan reklamını referans olarak yükle ve ürün görsellerini ekle.
> **B. Higgsfield MCP.** Higgsfield aboneliğin varsa en iyi seçenek. Hem GPT Image 2 hem de Nano Banana 2 için çalışır. İlk kullanımda tek seferlik OAuth girişi gereklidir.
> **C. Fal.ai sonuç başına ödeme.** Abonelik gerekmez. Üretim başına ödeme. `fal_api_key` gerektirir. Her iki model için de çalışır.
> **D. Playwright ile web arayüzü otomasyonu.** B veya C'den yavaş ama Higgsfield kredisi veya fal kredisi gerektirmez. GPT Image 2 için chatgpt.com'u, Nano Banana 2 için aistudio.google.com'u yönetir.
>
> A, B, C veya D yaz.

Açık bir seçim bekle. Aynı yol varyasyon başına bir kez çalışır. İki yolu asla paralel çalıştırma.

---

### Yol A: Manuel yapıştırma

Kullanıcı A'yı seçerse, otomatik hiçbir şey yapma.

**`$MODEL` `gpt-image-2` ise** kullanıcıya şunu söyle:

> https://chatgpt.com/ adresini aç, görsel oluşturucuyla yeni bir sohbet başlat ve modeli kalitesi yüksek olarak GPT Image 2'ye ayarla. Kazanan reklamını referans görsel olarak yükle, 1 ila 3 ürün görseli yükle ve her varyasyon promptunu birer birer yapıştır. Mevcut en büyük 1:1 boyutta her varyasyon için Oluştur'a tıkla.

**`$MODEL` `nano-banana-2` ise** kullanıcıya şunu söyle:

> https://aistudio.google.com/ adresini aç, Gemini 3.1 Flash Image'ı seç, kazanan reklamını referans görsel olarak yükle, 1 ila 3 ürün görseli yükle ve her varyasyon promptunu birer birer yapıştır. Her varyasyon için Oluştur'a tıkla.

Tamamlandığını onayla.

---

### Yol B: Higgsfield MCP

Yol B, varyasyonları doğrudan Claude Code içinde Higgsfield CLI aracılığıyla üretir. Higgsfield aboneliği olan kullanıcılar için en iyi seçenek. Kullanıcıya yönelik etiket `Yol B, Higgsfield MCP` olarak kalır çünkü kullanıcı tarafındaki deneyim değişmez; aynı krediler, aynı modeller, aynı Higgsfield hesabı.

`../_shared/path-b-cli-implementation.md` dosyasını yükle ve oradaki B.0 ile B.9 adımlarını takip et. Beceriye özgü değişkenler:

- `{{SKILL_SLUG}}`: `multiplier`
- `{{MODEL_ID}}`: `$MODEL` `gpt-image-2` ise `gpt_image_2`, `nano-banana-2` ise `nano_banana_flash`
- `{{ASPECT}}`: `1:1` (statik reklam varyasyonları için çoğaltıcı varsayılanı)
- `{{QUALITY}}`: `high` (GPT Image 2 için)
- `{{RESOLUTION}}`: GPT Image 2 için `4k`, Nano Banana 2 için `2k`
- `{{OUTPUT_DIR}}`: `$RFLAB/07_Multiplied_Ads/path_b_outputs`
- `{{OUTPUT_FILENAME}}`: `variation_<N>.png`; burada `<N>` kullanıcının alt kümesindeki varyasyon numarasıdır
- Referans varlıklar: önce kazanan reklam görseli, ardından kullanıcının sağladığı sırayla 1 ila 3 ürün görseli

**Alt küme seçici (beceriye özgü, B.5 onay kapısının bir parçası olarak çalışır).** Kullanıcıya şunu söyle:

> N adet varyasyon promptu hazır (1 ile N arasında varyasyonlar). Hangilerini Higgsfield üzerinden üretmemi istiyorsun? Numaraları virgülle ayırarak yaz. Örnek: "1, 3, 5 üret". Ya da her varyasyonu çalıştırmak için "hepsini" de.

Yanıt bekle. Hem `hepsini` (her varyasyon anlamında) hem de virgülle ayrılmış sayısal liste kabul et. Yanıt belirsizse tekrar sor. Her sayının 1 ile N arasında olduğunu doğrula. Tekrarlananları reddet.

**Onay özet metni (B.5).**

> Higgsfield aracılığıyla <liste> numaralı varyasyonları kullanarak K adet varyasyon üretmek üzereyim. Üretim başına maliyet: <B.4'teki krediler>. Toplam: <K çarpı üretim başına> kredi. Mevcut bakiye: <B.3'teki krediler>. Devam etmek için `evet` onayla.

**Paralel gruplar (B.7).** 5 veya daha fazla varyasyon için, üretme komutlarını paylaşılan referansta belgelendiği üzere Bash aracının `run_in_background` parametresi aracılığıyla paralel çalıştır. 5 ila 8 üretimlik tipik bir çoğaltıcı grubu, paralel çalıştırıldığında yaklaşık 90 saniyede tamamlanır; sıralı çalıştırmayla birkaç dakika sürer.

**Manifest (B.9).** Paylaşılan belgeden standart şema; `output_path`, üyenin istediği her varyasyon numarası için `{{OUTPUT_DIR}}` ile `variation_<N>.png` dosya adı birleştirilerek oluşturulur.

Eski MCP araç adları (`mcp__higgsfield__balance`, `mcp__higgsfield__generate_image` vb.) artık kullanılmıyor. CLI, Clerk yerine `higgsfield auth login` ile yönetilen OAuth akışıyla aynı Higgsfield hesabını, aynı kredileri ve aynı modelleri sunar.

---

### Yol C: fal.ai MCP üzerinden doğrudan API

**Önce kapı kontrolü.** Herhangi bir Yol C çalışmasından önce `fal-ai-prerun-check` koruma becerisini çalıştır. `pluginConfigs["reklam-fabrikasi"]` içinde `fal_api_key` varlığını ve fal-ai MCP'nin erişilebilir olduğunu doğrular. Koruma eksik veya geçersiz kimlik bilgisi bildirirse, kullanıcıya `/reklam-fabrikasi:setup-fal-ai` komutunu çalıştırmasını söyler ve durur. Kapıyı atlatma.

Kapı geçildiğinde devam et.

**Adım adım:**

1. **fal-ai MCP'nin bağlı olduğunu doğrula.** `mcp__fal-ai__*` araçlarını ara. Kapı geçilmesine rağmen mevcut değilse, kullanıcıya MCP'nin anahtarı alması için Claude Code'u yeniden yüklemesini söyle.

2. **Referans ve ürün görsellerini bir kez fal'a yükle.** Kazanan reklam için `mcp__fal-ai__upload_file` çağır. Her ürün görseli için tekrar çağır (1 ila 3). Tüm URL'leri `$IMAGE_URLS` olarak yakala.

3. **Fiyatı kontrol et.** Seçilen model için `mcp__fal-ai__get_pricing` çağır (GPT Image 2 için `openai/gpt-image-2/edit` veya Nano Banana 2 için `fal-ai/nano-banana-2`). Toplam hesapla: varyasyon sayısı çarpı görsel başına fiyat.

4. **Harcama onayı iste.** Seçilen modele göre gerçek bir maliyet belirt:
   - Yüksek kalitede, 1:1 4K eşdeğerinde GPT Image 2: yaklaşık görsel başına $0,15; 7 varyasyon için yaklaşık $1,05.
   - Nano Banana 2: yaklaşık görsel başına $0,04; 7 varyasyon için yaklaşık $0,28.

   Sor: "Devam edilsin mi? (evet/hayır)". "Evet" bekle.

5. **Her varyasyon için seçilen modele göre dallan:**

   **`$MODEL` `gpt-image-2` ise**, `mcp__fal-ai__run_model` çağır:
   - `model`: `"openai/gpt-image-2/edit"`
   - `prompt`: `<varyasyon promptu>`
   - `image_urls`: `$IMAGE_URLS`
   - `image_size`: `{"width": 2880, "height": 2880}` (statik reklam varyasyonları için 1:1 varsayılan, fal.ai'nin GPT Image 2 uç noktasının 8,3 megapiksel sınırı altında kabul ettiği en büyük 1:1 boyut)
   - `quality`: `"high"`
   - `output_format`: `"png"`
   - `num_images`: 1
   (`safety_tolerance` gönderme. Uç nokta bunu reddeder.)

   **`$MODEL` `nano-banana-2` ise**, `mcp__fal-ai__run_model` çağır:
   - `model`: `"fal-ai/nano-banana-2"`
   - `prompt`: `<varyasyon promptu>`
   - `resolution`: `"4K"`
   - `output_format`: `"png"`
   - `thinking_level`: `"high"`
   - `enable_web_search`: `true`
   - `num_images`: 1
   - `image_urls`: `$IMAGE_URLS`
   - `safety_tolerance`: `"4"`

   Dönen görsel URL'yi kaydet veya `$RFLAB/07_Multiplied_Ads/path_c_outputs/variation_N.png` konumuna indir.

6. **İlerlemeyi raporla.** Her 3 varyasyondan sonra kullanıcıya "N'den 3'ü tamamlandı. Devam edilsin mi? (evet/dur)" de.

7. **Son teslim.** `$RFLAB/07_Multiplied_Ads/path_c_outputs/manifest.json` dosyasına her varyasyon promptunu, görsel yolunu, kullanılan modeli ve toplam harcamayı listeleyen bir manifest yaz.

---

### Yol D: Playwright MCP görsel model web arayüzünü yönetir

Yol D, Playwright MCP sunucusunu kullanarak GPT Image 2 için ChatGPT'yi veya Nano Banana 2 için Google AI Studio'yu yönetir. Bu, Higgsfield MCP eklenmeden önceki versiyonlarda eski Yol B'ydi. **Sert kurallar:**

1. **Medyayı asla otomatik yükleme.** Her dosya yüklemesi kullanıcıdan açık "evet yükle" onayı gerektirir.
2. **Onay olmadan Oluştur'a asla tıklama.** Her Oluştur tıklaması kullanıcıdan açık "evet devam" onayı gerektirir.
3. **Bir seferde bir varyasyon.** Toplu işlem yok.

**Adım adım:**

1. **Playwright MCP'nin erişilebilir olduğunu onayla.** `playwright` bağlı değilse, kullanıcıya `/reklam-fabrikasi:doctor` komutunu çalıştırmasını söyle ve dur.

2. **Model arayüzünü aç.**
   - `$MODEL` `gpt-image-2` ise, `mcp__playwright__browser_navigate` ile https://chatgpt.com/ adresine git. Henüz giriş yapılmamışsa kullanıcıdan giriş yapmasını iste.
   - `$MODEL` `nano-banana-2` ise, `mcp__playwright__browser_navigate` ile https://aistudio.google.com/ adresine git. Henüz giriş yapılmamışsa kullanıcıdan giriş yapmasını iste.

3. **Modeli seç.**
   - `$MODEL` `gpt-image-2` ise, ChatGPT'de görsel oluşturucunun seçili ve kalitesinin yüksek olduğundan emin ol.
   - `$MODEL` `nano-banana-2` ise, `browser_click` ile "Gemini 3.1 Flash Image"a tıkla.

4. **Her varyasyon için (5 ila 8'den 1'i):**
   a. **Kullanıcıya** hangi varyasyonun çalışmak üzere olduğunu, açı adını ve görsel sahneyi söyle.
   b. **Referans yüklemeyi onayla.** Yalnızca ilk varyasyonda: "Kazanan reklamını referans görsel olarak yükleyelim mi? (evet/atla)". Evet derlerse `browser_file_upload` kullan.
   c. **Ürün yüklemeyi onayla.** Yalnızca ilk varyasyonda: "Ürün görsellerini yükleyelim mi (1 ila 3 dosya)? (evet/atla)". Evet derlerse her biri için `browser_file_upload` kullan.
   d. **Varyasyon promptunu** `browser_type` ile yapıştır.
   e. **Oluştur'u onayla.** "Varyasyon N için şimdi Oluştur'a tıklayayım mı? (evet/hayır)". "Evet" bekle. Ardından `browser_click` ile Oluştur'a tıkla.
   f. **Bekle** görselin render olmasını. `browser_take_screenshot` kullan ve `$RFLAB/07_Multiplied_Ads/path_d_outputs/variation_N.png` konumuna kaydet.
   g. **Temizle** sonraki varyasyondan önce giriş alanını (`browser_fill_form` ile boş değer).

5. **Hata yönetimi ve çıktı doğrulaması.**

   Her harici çağrı (Fal AI, Apify, Meta Ads, Playwright MCP, Anthropic API, web araması, web getirme) öz-iyileşme protokolünü takip eder:

   1. Katman 1 sessiz yeniden deneme: üstel geri çekilmeyle 3 kez yeniden dene. Yeniden denemeler sırasında sessiz kal.
   2. Katman 2 otomatik iyileşme: MCP'yi yeniden bağla, token'ları yenile, önbelleği temizle.
   3. Katman 3 kullanıcıya sor: Gerekeni üyeden iste.
   4. Katman 4 DM şablonu: kararlı hata ID'si ile yapılandırılmış hata raporu sun.

   Başarı ilan etmeden önce her çıktı doğrulanır:

   1. Vaat ettiğim teslimatı ürettim mi? (dosya mevcut, boş değil, beklenen bölümler var)
   2. İçerik becerinin amacıyla örtüşüyor mu? (doğru sayı, yer tutucu değil gerçek veri)
   3. Tüm yer tutucular dolduruldu mu?
   4. Sayı iddiayı karşılıyor mu? ('20 X buldum' dedim, belgede 20 X var mı?)

   Doğrulama başarısız olursa, belirgin sorunları otomatik düzeltmeye çalış. Düzeltemezsen, üyeye nelerin denendiğini, nelerin işe yarayıp nelerin yaramadığını ve somut sonraki adımları açıklayan dürüst bir rapor sun.

6. **Son teslim.** `$RFLAB/07_Multiplied_Ads/path_d_outputs/manifest.json` dosyasına her varyasyon promptunu ve görsel yolunu listeleyen bir manifest yaz.

---

## Dört yol boyunca sert kurallar

- **Asla sessizce yol değiştirme.** Kullanıcı bir yolu seçtiyse ve bir işlem başarısız olursa, yeniden deneyip denemeyeceğini, A'ya (manuel) geçip geçmeyeceğini veya vazgeçip geçmeyeceğini sor.
- **Yol B ve Yol C için modeli çağırmadan önce her zaman maliyeti göster.** Yol B Higgsfield kredilerine, Yol C fal.ai dolarına mal olur.
- **Açık bir `evet` onayı olmadan asla Higgsfield kredisi veya fal.ai ücreti alma.**
- **Her çıktıyı diske kaydet** `$RFLAB/07_Multiplied_Ads/path_X_outputs/` altına.

---

## Çıktı doğrulaması

Bu beceriyi tamamlandı ilan etmeden önce şunları doğrula:

1. Teslimat beklenen yolda mevcut:
   - `<pwd>/Reklam Fabrikası/07_Multiplied_Ads/variations-<YYYY-MM-DD>.md` konumunda varyasyon promptları belgesi.
   - Yol B görselleri (Yol B ise): `<pwd>/Reklam Fabrikası/07_Multiplied_Ads/path_b_outputs/variation_<N>.png` artı `manifest.json`.
   - Yol C görselleri (Yol C ise): `<pwd>/Reklam Fabrikası/07_Multiplied_Ads/path_c_outputs/variation_<N>.png` artı `manifest.json`.
   - Yol D görselleri (Yol D ise): `<pwd>/Reklam Fabrikası/07_Multiplied_Ads/path_d_outputs/variation_<N>.png` artı `manifest.json`.
2. Teslimat boş değil (varyasyon belgesi > 8000 bayt; görsel dosyaları her biri > 50000 bayt).
3. Beklenen içerik sayısı iddiayı karşılıyor:
   - Varyasyon belgesi kullanıcının istediği tam sayıyı içeriyor (5 ila 8).
   - Üretim istenmişse Yol B, Yol C veya Yol D çıktı klasörü aynı sayıda görsel dosyası içeriyor. Bir alt kümeyle Yol B için, manifest üyenin istediği varyasyon numaralarını tam olarak içeriyor.
4. Yer tutucu dizeler kalmadı:
   - `[Açı adı]`, `[Persona]`, `[düzey]`, `<TODO>` veya `lorem ipsum` yok.
5. Gerekli tüm bölümler dolduruldu:
   - Kazanan Reklam Analiz Özeti (4 ila 6 satır)
   - Varyasyon Strateji Tablosu (tüm 8 sütunla her varyasyon için bir satır)
   - Her varyasyon promptu başlıkla tam yazılmış (numara, açı, farkındalık, kanca, duygu, sahne)
   - Tüm varyasyonların farklı kanca mekaniği VE farklı farkındalık düzeyi VE farklı görsel sahnesi var

Doğrulama başarısız olursa:

1. Önce otomatik düzeltmeye çalış:
   - İki varyasyon aynı kancayı, farkındalığı veya sahneyi paylaşıyorsa, tekrarı yeniden üret.
   - Bir varyasyon kazanan reklamın dönüşüm mekaniğini kaybettiyse, yapısal iskelet korunarak yeniden yaz.
   - Yer tutucular kalırsa, Marka DNA'sı, VOC ve kazanan reklam analizinden doldur.

2. Otomatik düzeltme başarısız olursa, üyeye dürüst bir rapor sun:
   "Çoğaltıcı: N varyasyon ürettim ama doğrulama <sorunu> gösterdi. <düzeltme girişimi> denedim ve <işe yaramadı / kısmen işe yaradı>. Tam sonuç almak için:
   - Açı havuzu daha geniş olsun diye ek VOC acı noktaları sağlayabilirsin
   - Analizim kaçırdıysa kazanan reklamın dönüşüm mekaniğini onaylayabilirsin
   - Görsel sahneler daha fazla ayrışsın diye daha fazla ürün görseli paylaşabilirsin
   Ya da başarısız olan varyasyon numaralarını yapıştır, yalnızca onları yeniden oluşturayım."

3. Andromeda farklılaşması garanti edilemediyse (yeniden denemeler sonrasında varyasyonlar çok benzer):
   - Daha geniş parametrelerle BİR KEZ DAHA dene:
     - Taze açılar için VOC'dan ek alıcı personaları çek
     - Varyasyonlar boyunca ayrışan renk dünyalarını zorla (örn. sıcak/soğuk/monokrom/yüksek kontrast)
     - Ayrışan görsel ortamları zorla (stüdyo/yaşam tarzı/kullanım/alıntı odaklı/dönüşüm)
   - Hâlâ çok benzerse, dürüst bir rapor sun:
     "Çoğaltıcı: N gerçekten farklı varyasyon üretmeye çalıştım ama kaynak materyal yalnızca M gerçekten ayrışan açıyı destekledi. M'nin ötesine geçmek, Andromeda'nın onları tek Entity ID olarak kümeleme riskini taşıyor. Devam etmek için:
     - Daha küçük bir seti onayla (N yerine M varyasyon) ve boşa harcamayı önle
     - Yeni bir açı sağla (yeni persona, yeni acı, yeni teklif)
     - Görsel sahneler daha sert ayrışsın diye daha fazla ürün görseli paylaş
     Ya da en güçlü hissettiren varyasyonu paylaş, sadece onu farklı şekilde çoğaltayım."
