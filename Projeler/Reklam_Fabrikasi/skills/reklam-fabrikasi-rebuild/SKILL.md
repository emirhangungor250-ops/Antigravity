---
name: reklam-fabrikasi-rebuild
description: "Kullanıcı /rebuild, /rebuild ad, /reverse engineer ad yazıyorsa ya da bir rakip reklamı kendi markası için yeniden inşa etmek veya yeniden yaratmak istediğini söylüyorsa bu beceriyi kullan. Bu beceri, rakibin kazanan statik reklam görselini, bir Marka DNA'sı belgesini ve bir VOC araştırma belgesini alır; ardından rakip reklamı kullanıcının markası için yeni bir reklama dönüştüren tam yazılmış bir referans görsel promptu üretir. Tüm metin, ürün ve görsel değişimler açıkça yazılmıştır. İsteğe bağlı olarak 5 alıcı persona varyasyonu üretir. Model seçici: GPT Image 2 (önerilen, yüksek kalite, 4K eşdeğeri image_size, fal.ai üzerinden openai/gpt-image-2/edit) veya daha ucuz alternatif olarak Nano Banana 2. Kullanıcı rakip bir reklamı yeniden inşa etmekten, kazanan bir reklamı yeniden yaratmaktan veya reklam üretimi için referans görsel kullanmaktan bahsettiğinde bu beceriyi her zaman tetikle."
---

# Reklam Fabrikası, Rakip Reklam Yeniden İnşası

Bu beceri, rakibin kazanan statik reklamını markan için kullanıma hazır bir referans görsel promptuna dönüştürür. Reklamı, Marka DNA'sı belgeni ve VOC belgeni yüklersin; beceri orijinal reklamı analiz eder ve görsel modelin (varsayılan olarak GPT Image 2, daha ucuz alternatif olarak Nano Banana 2) tam olarak neyi değiştireceğini ve neyi koruyacağını bilmesi için her metin ve görsel değişimi açıkça yazar.

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
  mkdir -p "$TARGET/08_Rebuilt_Competitor_Ads/path_b_outputs" "$TARGET/08_Rebuilt_Competitor_Ads/path_c_outputs" "$TARGET/08_Rebuilt_Competitor_Ads/path_d_outputs" "$TARGET/_meta"
  echo "READY:$TARGET"
fi

# Marka klasörü varsa ve CLAUDE.md dosyası eksikse marka belleğini (CLAUDE.md) oluştur.
# Yapacak bir şey yoksa sessizce çalışır ve idempotent davranır.
if [ -d "$TARGET" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" ]; then
  bash "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi
```

- `PROTECTED:<path>`: Reddet ve kullanıcıya Claude Code'u markaya özel bir alt klasörde açmasını söyle. Dur.
- `FIRSTRUN:<path>`: "Çıktıları `<path>/` konumuna kaydedeceğim. Bu klasöre ilk kez kaydediyorum, doğru mu? (evet/hayır)" diye sor. Evet derlerse klasörleri oluştur ve `<path>/_meta/folder-confirmed.flag` dosyasını yaz. Hayır derlerse dur.
- `READY:<path>`: Sessizce devam et.

Çözülen yolu `$RFLAB` olarak yakala.

Otomatik keşif: Önceki çalışmalar için `$RFLAB/01_VOC_Research/`, `$RFLAB/02_Brand_DNA/` ve `$RFLAB/03_Ad_Spy/` klasörlerini tara. Dosyalar mevcutsa, yeni yükleme istemek yerine bunları kullanıcıya öner:

```
ls -t "$RFLAB/01_VOC_Research/"*.html "$RFLAB/01_VOC_Research/"*.md 2>/dev/null | head -n 1
ls -t "$RFLAB/02_Brand_DNA/"*.html "$RFLAB/02_Brand_DNA/"*.md 2>/dev/null | head -n 1
ls -t "$RFLAB/03_Ad_Spy/"*.html 2>/dev/null | head -n 5
```

Kullanıcıya hangi dosyaları bulduğunu söyle ve hangi rakip reklam görselini yeniden inşa etmek istediklerini sor.

## Kullanıcının Sağlaması Gerekenler

Kullanıcı bu beceriyi etkinleştirdiğinde, tek bir mesajda aşağıdakilerin hepsini sağlamalarını hemen iste:

> Reklam yeniden inşa promptunu oluşturmak için üç şeye ve iki hızlı cevaba ihtiyacım var:
>
> **1. Rakibin kazanan reklamı** bu sohbete statik görseli doğrudan yapıştır veya yükle
>
> **2. Marka DNA'sı belgen** tam metni yapıştır veya dosyayı yükle
>
> **3. VOC araştırma belgen** tam metni yapıştır veya dosyayı yükle
>
> **4. Eklemek istediğin belirli bir kampanya, teklif veya promosyon var mı?**
> Örneğin: indirim ("bu hafta %20 indirim"), paket anlaşma, ücretsiz deneme, sezonluk kampanya, lansman teklifi veya reklamın yönlendirmesini istediğin belirli bir harekete geçirici mesaj. Varsa kısaca açıkla. Yoksa "teklif yok" de ve yeniden inşa ürüne ve marka konumlandırmasına odaklanır.
>
> **5. Bu yeniden inşanın 5 persona varyasyonunu ister misin?**
> Her varyasyon orijinal reklamla aynı düzen ve yapıyı kullanacak ama VOC araştırmandan farklı bir alıcı persona açısına geçiş yapacak.
>
> Üç girişi ve 4. ile 5. sorulara cevaplarını birlikte yaz.

Görsel, Marka DNA'sı belgesi ve VOC belgesi olmadan devam etme. Herhangi biri eksikse tekrar sor.

---

## İş Akışı, Üç Aşama

---

### AŞAMA 1, Rakip Reklamı Analiz Et

Reklam görselini dikkatle oku. Reklam analiz çerçevesini şuradan yükle:
`references/ad-analysis.md`

Tam olarak takip et. Rakip reklamın her yapısal, görsel ve metin öğesini kapsayan tam bir dahili analiz üret. Bu analiz senin çalışma belgendir; Aşama 2'de kesin değişimler yapmak için kullanırsın.

Tam analizi kullanıcıya gösterme. Aşama 1 sonrasında kullanıcıya şunu söyle:
> "Reklam analiz edildi. Yeniden inşa promptun oluşturuluyor..."

---

### AŞAMA 2, Yeniden İnşa Promptu Oluştur

Prompt oluşturma kılavuzunu şuradan yükle:
`references/prompt-builder.md`

Aşama 1 analizi, Marka DNA'sı belgesi ve VOC belgesini kullanarak tam referans görsel promptunu oluştur. Bu prompt görsel modele (varsayılan olarak GPT Image 2, daha ucuz alternatif olarak Nano Banana 2) tam olarak neyi değiştireceğini ve neyi koruyacağını söyler. Her metin değişimi, kullanılacak tam kelimelerle birlikte senin tarafından önceden yazılır.

Kullanıcı:
1. Rakip reklam görselini doğrudan seçilen model arayüzüne referans görsel olarak yükleyecek
2. Kendi ürün görselini yanına yükleyecek
3. Promptunu modelin metin alanına yapıştıracak

Promptun eksiksiz ve bağımsız olmalı. Kullanıcı sıfır düzenlemeyle doğrudan yapıştırabilmeli.

---

### AŞAMA 3, Persona Varyasyonları (istenirse)

Kullanıcı persona varyasyonlarına evet dediyse, şunu yükle:
`references/persona-variations.md`

Her biri VOC belgesinden farklı bir alıcı personayı hedefleyen 5 tam varyasyon promptu üret. Her varyasyon tam bağımsız bir referans görsel promptudur (hem GPT Image 2 hem de Nano Banana 2 ile çalışır). Her birini açıkça etiketle:

**VARİYASYON 1, [Persona Adı/Açıklaması]**
[Tam prompt]

**VARİYASYON 2, [Persona Adı/Açıklaması]**
[Tam prompt]

...ve böyle 5. varyasyona kadar devam et.

---

## Çıktı Formatı

Çıktıyı şu sırayla sun:

1. **REKLAM ANALİZ ÖZETİ** orijinal reklamı neyin işe yaradığına dair 4 ila 6 satırlık kısa ve stratejik özet (kanca türü, düzen, metin yaklaşımı, farkındalık düzeyi).

2. **YENİDEN İNŞA PROMPTU** tam referans görsel promptu, açıkça etiketlenmiş, GPT Image 2 veya Nano Banana 2'ye yapıştırmaya hazır.

3. **PERSONA VARİYASYONLARI** yalnızca istenirse. Hepsi tam yazılmış, açıkça numaralandırılmış ve etiketlenmiş.

---

## Kurallar

- **Kelimelere sen karar verirsin, görsel model değil.** Prompttaki her metin öğesinin tam değiştirme metni yazılmış olmalıdır. "Başlığı alakalı bir şeyle değiştir" asla yazma. Gerçek başlığı yaz.
- **HER metin öğesinde orijinal kelime sayısını eşleştir.** Bu becerinin en önemli disiplinidir. Kazanan reklamın 4 kelimelik bir başlığı varsa, senin değiştirme başlığın 4 kelimedir (en fazla 3 ila 5 kelime, asla daha fazlası). HGPM 2 kelimeyse, seninki de 2 kelime. Alt başlık 8 kelimeyse, seninki de 8 kelime. Rozet 3 kelimeyse, seninki de 3 kelime. Gövde metninin satır sayısı ve yaklaşık kelime sayısı orijinalle eşleşir. Kelime sayısı reklamın görsel planıdır ve görsel plan onu kazandıran şeydir. Bu kuralı kır ve reklamı kırarsın.
- **Persona varyasyonları aynı düzeni kullanır.** Orijinal reklamın yapısı, metin yerleşimi ve görsel hiyerarşisi tüm varyasyonlarda aynı kalır. Yalnızca metin açıları, acı noktaları ve müşteri dili değişir.
- **Her kelimeyi belgelere dayandır.** Tüm değiştirme metni Marka DNA'sı belgesinden (ses tonu, konumlandırma, ürün detayları) ve VOC belgesinden (müşteri dili, acı noktaları, istekler) gelmelidir. Genel reklam metni uydurma.
- **Yaratıcı yorum yok.** Bu beceri yeniden inşa eder ve uyarlar, yeniden tasarlamaz. Orijinal reklamın düzeni şablondur. Senin işin kesin değiştirmedir, yeniden hayal değil.

---

## Görsel modelini seç

Yeniden inşa promptunu (ve persona varyasyonlarını) sunduktan sonra kullanıcıya şu soruyu sor:

> Yeniden inşayı üretmek için hangi görsel modeli kullanayım?
>
> **1. GPT Image 2** (önerilen). Yüksek kalite, 4K eşdeğeri `image_size` (kare yeniden inşa çıktıları için varsayılan 2880x2880, fal.ai'nin GPT Image 2 uç noktasının 8,3 megapiksel sınırı altında kabul ettiği en büyük 1:1 boyut). Şu anda mevcut en iyi görsel üretim modeli. Ürün detayı, metin render, yüz tutarlılığı ve karmaşık promptlarda Nano Banana 2 ve Nano Banana Pro'dan üstün.
> **2. Nano Banana 2.** Üretim başına daha düşük maliyet isteyen kullanıcılar için daha ucuz alternatif. Seçmek için tek neden ucuzluğu; GPT Image 2 her kalite ekseninde kazanıyor.
>
> `1`, `2` yaz veya GPT Image 2 için `varsayılan` de.

`$MODEL` olarak yakala. Varsayılan `gpt-image-2`.

---

## Üretim yolunu seç

Model seçildikten sonra kullanıcıya şu soruyu sor:

> Yeniden inşa promptun hazır, model `$MODEL`. Görseli gerçekten nasıl üretmek istiyorsun?
>
> **A. Manuel yapıştırma.** Ücretsiz. Promptu kendi başına modelin web arayüzüne yapıştır, rakip reklamı referans olarak yükle ve ürün görselini ekle.
> **B. Higgsfield MCP.** Higgsfield aboneliğin varsa en iyi seçenek. Hem GPT Image 2 hem de Nano Banana 2 için çalışır. İlk kullanımda tek seferlik OAuth girişi gereklidir.
> **C. Fal.ai sonuç başına ödeme.** Abonelik gerekmez. Üretim başına ödeme. `fal_api_key` gerektirir. Her iki model için de çalışır.
> **D. Playwright ile web arayüzü otomasyonu.** B veya C'den yavaş ama Higgsfield kredisi veya fal kredisi gerektirmez. GPT Image 2 için chatgpt.com'u, Nano Banana 2 için aistudio.google.com'u yönetir.
>
> A, B, C veya D yaz.

Açık bir seçim bekle. Kullanıcı 5 persona varyasyonu istediyse, aynı yol varyasyon başına bir kez çalışır. İki yolu asla paralel çalıştırma.

---

### Yol A: Manuel yapıştırma

Kullanıcı A'yı seçerse, otomatik hiçbir şey yapma.

**`$MODEL` `gpt-image-2` ise** kullanıcıya şunu söyle:

> https://chatgpt.com/ adresini aç, görsel oluşturucuyla yeni bir sohbet başlat ve modeli kalitesi yüksek olarak GPT Image 2'ye ayarla. Rakip reklamı referans görsel olarak yükle, ürün görselini yükle ve yeniden inşa promptunu yapıştır. Mevcut en büyük 1:1 boyutta Oluştur'a tıkla. Persona varyasyonların varsa, her biri için tekrarla.

**`$MODEL` `nano-banana-2` ise** kullanıcıya şunu söyle:

> https://aistudio.google.com/ adresini aç, Gemini 3.1 Flash Image'ı seç, rakip reklamı referans görsel olarak yükle, ürün görselini yükle ve yeniden inşa promptunu yapıştır. Oluştur'a tıkla. Persona varyasyonların varsa, her biri için tekrarla.

Tamamlandığını onayla. İşin bitti.

---

### Yol B: Higgsfield MCP

Yol B, yeniden inşayı (ve persona varyasyonlarını) doğrudan Claude Code içinde Higgsfield CLI aracılığıyla üretir. Higgsfield aboneliği olan kullanıcılar için en iyi seçenek. Kullanıcıya yönelik etiket `Yol B, Higgsfield MCP` olarak kalır çünkü kullanıcı tarafındaki deneyim değişmez; aynı krediler, aynı modeller, aynı Higgsfield hesabı.

`../_shared/path-b-cli-implementation.md` dosyasını yükle ve oradaki B.0 ile B.9 adımlarını takip et. Beceriye özgü değişkenler:

- `{{SKILL_SLUG}}`: `rebuild`
- `{{MODEL_ID}}`: `$MODEL` `gpt-image-2` ise `gpt_image_2`, `nano-banana-2` ise `nano_banana_flash`
- `{{ASPECT}}`: `1:1` (yeniden inşa varsayılanı)
- `{{QUALITY}}`: `high` (GPT Image 2 için), Nano Banana 2 için yine de geç (CLI bunu yok sayar)
- `{{RESOLUTION}}`: GPT Image 2 için `4k`, Nano Banana 2 için `2k`
- `{{OUTPUT_DIR}}`: `$RFLAB/08_Rebuilt_Competitor_Ads/path_b_outputs`
- `{{OUTPUT_FILENAME}}`: `rebuild_<N>.png`; burada `<N>` ana yeniden inşa için 0, persona varyasyonları için 1 ila 5
- Referans varlıklar: önce rakip reklam görseli, ardından üye ürün görseli

**Alt küme seçici (beceriye özgü, B.5 onay kapısının bir parçası olarak çalışır).** Kullanıcıya şunu söyle:

> Ana yeniden inşa promptu ve N persona varyasyonu hazır (0 ile N arası numaralar; 0 ana yeniden inşa, 1 ile N arasındakiler personalar). Hangilerini Higgsfield üzerinden üretmemi istiyorsun? Numaraları virgülle ayırarak yaz. Örnek: "0, 2, 4 üret". Ya da her promptu çalıştırmak için "hepsini" de.

Sıfır persona varyasyonu varsa, tek geçerli sayı 0'dır. Yanıt bekle. Hem `hepsini` hem de virgülle ayrılmış sayısal liste kabul et. Belirsizse tekrar sor. Her sayının 0 ile N arasında olduğunu doğrula. Tekrarlananları reddet.

**Onay özet metni (B.5).**

> Higgsfield aracılığıyla <liste> numaralı prompt numaralarını kullanarak K yeniden inşa promptu üretmek üzereyim. Üretim başına maliyet: <B.4'teki krediler>. Toplam: <K çarpı üretim başına> kredi. Mevcut bakiye: <B.3'teki krediler>. Devam etmek için `evet` onayla.

**Manifest (B.9).** Paylaşılan belgeden standart şema; `output_path`, üyenin istediği prompt numarası için `{{OUTPUT_DIR}}` ile `rebuild_<N>.png` dosya adı birleştirilerek oluşturulur.

Eski MCP araç adları (`mcp__higgsfield__balance`, `mcp__higgsfield__generate_image` vb.) artık kullanılmıyor. CLI, Clerk yerine `higgsfield auth login` ile yönetilen OAuth akışıyla aynı Higgsfield hesabını, aynı kredileri ve aynı modelleri sunar.

---

### Yol C: fal.ai MCP üzerinden doğrudan API

**Önce kapı kontrolü.** Herhangi bir Yol C çalışmasından önce `fal-ai-prerun-check` koruma becerisini çalıştır. `pluginConfigs["reklam-fabrikasi"]` içinde `fal_api_key` varlığını ve fal-ai MCP'nin erişilebilir olduğunu doğrular. Koruma eksik veya geçersiz kimlik bilgisi bildirirse, kullanıcıya `/reklam-fabrikasi:setup-fal-ai` komutunu çalıştırmasını söyler ve durur. Kapıyı atlatma.

Kapı geçildiğinde devam et.

**Adım adım:**

1. **fal-ai MCP'nin bağlı olduğunu doğrula.** `mcp__fal-ai__*` araçlarını ara. Kapı geçilmesine rağmen mevcut değilse, kullanıcıya MCP'nin anahtarı alması için Claude Code'u yeniden yüklemesini söyle.

2. **Referans ve ürün görsellerini bir kez fal'a yükle.** Rakip reklam görseli için `mcp__fal-ai__upload_file` çağır, URL'yi yakala. Ürün görseli için tekrar çağır, URL'yi yakala. Her run_model çağrısında kullanmak üzere her ikisini `$IMAGE_URLS = [<competitor_url>, <product_url>]` olarak yakala.

3. **Fiyatı kontrol et.** Seçilen model için `mcp__fal-ai__get_pricing` çağır (GPT Image 2 için `openai/gpt-image-2/edit` veya Nano Banana 2 için `fal-ai/nano-banana-2`). Toplam hesapla: 1 + (persona varyasyonları varsa 5) prompt çarpı görsel başına fiyat.

4. **Harcama onayı iste.** Seçilen modele göre gerçek bir maliyet belirt:
   - Yüksek kalitede, 1:1 4K eşdeğerinde GPT Image 2: yaklaşık görsel başına $0,15; yalnızca ana yeniden inşa için $0,15 veya 5 persona varyasyonuyla $0,90.
   - Nano Banana 2: yaklaşık görsel başına $0,04; yalnızca ana yeniden inşa için $0,04 veya 5 persona varyasyonuyla $0,24.

   Sor: "Devam edilsin mi? (evet/hayır)". "Evet" bekle.

5. **Yeniden inşa promptu (ve her persona varyasyonu) için seçilen modele göre dallan:**

   **`$MODEL` `gpt-image-2` ise**, `mcp__fal-ai__run_model` çağır:
   - `model`: `"openai/gpt-image-2/edit"`
   - `prompt`: `<yeniden inşa promptu>`
   - `image_urls`: `$IMAGE_URLS`
   - `image_size`: `{"width": 2880, "height": 2880}` (yeniden inşa çıktıları için 1:1 varsayılan, fal.ai'nin GPT Image 2 uç noktasının 8,3 megapiksel sınırı altında kabul ettiği en büyük 1:1 boyut)
   - `quality`: `"high"`
   - `output_format`: `"png"`
   - `num_images`: 1
   (`safety_tolerance` gönderme. Uç nokta bunu reddeder.)

   **`$MODEL` `nano-banana-2` ise**, `mcp__fal-ai__run_model` çağır:
   - `model`: `"fal-ai/nano-banana-2"`
   - `prompt`: `<yeniden inşa promptu>`
   - `resolution`: `"4K"`
   - `output_format`: `"png"`
   - `thinking_level`: `"high"`
   - `enable_web_search`: `true`
   - `num_images`: 1
   - `image_urls`: `$IMAGE_URLS`
   - `safety_tolerance`: `"4"`

   Dönen görsel URL'yi kaydet veya `$RFLAB/08_Rebuilt_Competitor_Ads/path_c_outputs/rebuild_N.png` konumuna indir.

6. **Son teslim.** `$RFLAB/08_Rebuilt_Competitor_Ads/path_c_outputs/manifest.json` dosyasına her promptu, görsel yolunu, kullanılan modeli ve toplam harcamayı listeleyen bir manifest yaz.

---

### Yol D: Playwright MCP görsel model web arayüzünü yönetir

Yol D, Playwright MCP sunucusunu kullanarak GPT Image 2 için ChatGPT'yi veya Nano Banana 2 için Google AI Studio'yu yönetir. Bu, Higgsfield MCP eklenmeden önceki versiyonlarda eski Yol B'ydi. **Sert kurallar:**

1. **Medyayı asla otomatik yükleme.** Her dosya yüklemesi kullanıcıdan açık "evet yükle" onayı gerektirir.
2. **Onay olmadan Oluştur'a asla tıklama.** Her Oluştur tıklaması kullanıcıdan açık "evet devam" onayı gerektirir.
3. **Bir seferde bir prompt.** Persona varyasyonları arasında toplu işlem yok.

**Adım adım:**

1. **Playwright MCP'nin erişilebilir olduğunu onayla.** `playwright` bağlı değilse, kullanıcıya `/reklam-fabrikasi:doctor` komutunu çalıştırmasını söyle ve dur.

2. **Model arayüzünü aç.**
   - `$MODEL` `gpt-image-2` ise, `mcp__playwright__browser_navigate` ile https://chatgpt.com/ adresine git. Henüz giriş yapılmamışsa kullanıcıdan giriş yapmasını iste.
   - `$MODEL` `nano-banana-2` ise, `mcp__playwright__browser_navigate` ile https://aistudio.google.com/ adresine git. Henüz giriş yapılmamışsa kullanıcıdan giriş yapmasını iste.

3. **Modeli seç.**
   - `$MODEL` `gpt-image-2` ise, ChatGPT'de görsel oluşturucunun seçili ve kalitesinin yüksek olduğundan emin ol.
   - `$MODEL` `nano-banana-2` ise, `browser_click` ile "Gemini 3.1 Flash Image"a tıkla.

4. **Yeniden inşa promptu için (ve istenirse her persona varyasyonu):**
   a. **Kullanıcıya** hangi promptun çalışmak üzere olduğunu söyle.
   b. **Referans yüklemeyi onayla.** "Rakip reklam görselini referans olarak yükleyelim mi? (evet/atla)". Evet derlerse, kullanıcının sağladığı rakip reklam yoluyla `browser_file_upload` kullan.
   c. **Ürün yüklemeyi onayla.** "Ürün görselini yükleyelim mi? (evet/atla)". Evet derlerse, ürün görseli yoluyla `browser_file_upload` kullan.
   d. **Promptu** `browser_type` veya `browser_fill_form` ile yapıştır.
   e. **Oluştur'u onayla.** "Şimdi Oluştur'a tıklayayım mı? (evet/hayır)". "Evet" bekle. Ardından `browser_click` ile Oluştur'a tıkla.
   f. **Bekle** görselin render olmasını. `browser_take_screenshot` kullan ve `$RFLAB/08_Rebuilt_Competitor_Ads/path_d_outputs/rebuild_N.png` konumuna kaydet (ana yeniden inşa için N=0, persona varyasyonları için 1 ila 5).

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

6. **Son teslim.** `$RFLAB/08_Rebuilt_Competitor_Ads/path_d_outputs/manifest.json` dosyasına her promptu ve görsel yolunu listeleyen bir manifest yaz.

---

## Dört yol boyunca sert kurallar

- **Asla sessizce yol değiştirme.** Kullanıcı bir yolu seçtiyse ve bir işlem başarısız olursa, yeniden deneyip denemeyeceğini, A'ya (manuel) geçip geçmeyeceğini veya vazgeçip geçmeyeceğini sor.
- **Yol B ve Yol C için modeli çağırmadan önce her zaman maliyeti göster.** Yol B Higgsfield kredilerine, Yol C fal.ai dolarına mal olur.
- **Açık bir `evet` onayı olmadan asla Higgsfield kredisi veya fal.ai ücreti alma.**
- **Her çıktıyı diske kaydet** `$RFLAB/08_Rebuilt_Competitor_Ads/path_X_outputs/` altına.

---

## Çıktı doğrulaması

Bu beceriyi tamamlandı ilan etmeden önce şunları doğrula:

1. Teslimat beklenen yolda mevcut:
   - `<pwd>/Reklam Fabrikası/08_Rebuilt_Competitor_Ads/rebuild-<YYYY-MM-DD>.md` konumunda yeniden inşa prompt belgesi.
   - Yol B görselleri (Yol B ise): `<pwd>/Reklam Fabrikası/08_Rebuilt_Competitor_Ads/path_b_outputs/rebuild_<N>.png` artı `manifest.json`.
   - Yol C görselleri (Yol C ise): `<pwd>/Reklam Fabrikası/08_Rebuilt_Competitor_Ads/path_c_outputs/rebuild_<N>.png` artı `manifest.json`.
   - Yol D görselleri (Yol D ise): `<pwd>/Reklam Fabrikası/08_Rebuilt_Competitor_Ads/path_d_outputs/rebuild_<N>.png` artı `manifest.json`.
2. Teslimat boş değil (yeniden inşa belgesi > 4000 bayt; görsel dosyaları her biri > 50000 bayt).
3. Beklenen içerik sayısı iddiayı karşılıyor:
   - 1 ana yeniden inşa promptu her zaman mevcut.
   - Kullanıcı varyasyonlara evet dediyse (ve yalnızca o zaman) 5 persona varyasyonu mevcut.
   - Görsel sayıları eşleşiyor: üretim yolu başına 1 görsel (varyasyonsuz) veya 6 görsel (varyasyonlarla). Bir alt kümeyle Yol B için, manifest üyenin istediği prompt numaralarını tam olarak içeriyor.
4. Yer tutucu dizeler kalmadı:
   - `[başlık]`, `[HGPM]`, `[Persona Adı]`, `<TODO>` veya `lorem ipsum` yok.
   - "alakalı bir şeyle değiştir" taslakları yok.
5. Gerekli tüm bölümler dolduruldu:
   - Reklam Analiz Özeti (4 ila 6 satır)
   - Her metin değişimi açık yazılmış tam yeniden inşa promptu
   - Persona varyasyonları (istenirse) hepsi aynı düzenle, farklı personalarla tam yazılmış 5 varyasyon
   - Kelime sayıları her metin öğesinde orijinal reklamla eşleşiyor

Doğrulama başarısız olursa:

1. Önce otomatik düzeltmeye çalış:
   - Bir metin değişiminde gerçek değiştirme metni eksikse, Marka DNA'sından ve VOC'dan yaz.
   - Kelime sayısı kaydıysa (değiştirme çok uzun veya kısa), orijinali artı/eksi 1 ila 2 kelime içinde eşleşecek biçimde yeniden yaz.
   - Bir persona varyasyonu eksikse, farklı VOC açısı kullanarak yeniden üret.
   - Yer tutucular kalırsa, analiz, Marka DNA'sı ve VOC'dan doldur.

2. Otomatik düzeltme başarısız olursa, üyeye dürüst bir rapor sun:
   "Yeniden inşa: Promptu ürettim ama doğrulama <sorunu> gösterdi. <düzeltme girişimi> denedim ve <işe yaramadı / kısmen işe yaradı>. Tam sonuç almak için:
   - Rakip reklam görselinin daha yüksek çözünürlüklü versiyonunu sağlayabilirsin
   - Değiştirmeleri kilitlemek için ürün adını ve temel USP'yi onaylayabilirsin
   - Herhangi bir uyum kısıtlaması paylaşabilirsin (kaçınılacak iddialar, dahil edilmesi gereken dil)
   Ya da başarısız olan değiştirmeyi yapıştır, yalnızca o öğeyi yeniden oluşturayım."

3. Analiz rakip reklamdan yeterli yapısal detay çıkaramadıysa:
   - Daha geniş parametrelerle BİR KEZ DAHA dene:
     - Görseli düzen, tip hiyerarşisi ve renk bloklarına odaklanarak yeniden oku
     - Okunması zor metinler için kullanıcıdan açıklayıcı detay iste
   - Hâlâ yetersizse, dürüst bir rapor sun:
     "Yeniden inşa: Rakip reklamdan her metin ve görsel öğeyi çıkarmaya çalıştım ama bazı bölümler okunamaz veya belirsizdi. Devam etmek için:
     - Aynı reklamın daha yüksek çözünürlüklü versiyonunu yükleyebilirsin
     - Okuyabildiğin metni yazabilirsin böylece gerçek veriye sahip olurum
     - Kaynak URL'yi paylaşabilirsin (Ad Library linki) temiz bir kopyasını çekeyim
     Ya da açıkça okuyabildiğim farklı bir rakip reklam seç."
