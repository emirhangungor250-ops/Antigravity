---
name: reklam-fabrikasi-product-shot
description: "Kullanıcı herhangi bir ürün çekimi üretmek istediğinde bu beceriyi kullan. Tek beceri içinde üç mod: (1) Stüdyo, düz renkli arka planda temiz ürün çekimi; (2) Tutma, ürünü tutan kişi, eller veya kollar görünür; (3) Giyme veya kullanma, ürünü giyen kişi (giysi, aksesuar) ya da aktif kullanan kişi (cilt bakımı, içecek, takviye). Şu komutlarda tetikle: /product-shot, /productshot, /studio-shot, /packshot, /clean shot, /hold shot, /worn shot, /lifestyle shot, /someone holding the product, /someone wearing my product, /show product in use, ya da doğal dil ifadelerinde: 'bu iPhone fotoğrafını stüdyo çekimine dönüştür', 'içeceğimi tutan birinin çekimini yap', 'tişörtümü giyen biri', 'seru yüze sürülürken göster', 'ürünümün lifestyle fotoğrafına ihtiyacım var'. Kişi kaynağı olarak /character ile kaydedilmiş bir karakter (reklamlarda yüz tutarlılığı için önerilir), tek satırda tanımlanan rastgele bir kişi veya kişisiz tercih kullanılabilir. Varsayılan olarak GPT Image 2 kullanır. Temel çekim üretildikten sonra kullanıcılar tam akışı yeniden başlatmadan açı, karakter, arka plan veya etkileşimi hızla değiştirebilir. Çıktılar _assets/product-shots/<çıktı-adı>/ dizinine kaydedilir. Yol A (manuel yapıştırma), Yol B (Higgsfield MCP, her iki model), Yol C (fal.ai direkt, fal-ai-prerun-check ile korumalı, her iki model), Yol D (Playwright ChatGPT veya Nano Banana 2 web arayüzünü kullanır) seçeneklerini içerir."
---

# Reklam Fabrikası, Ürün Çekimi Üreticisi

Tek beceri içinde üç mod. Temel çekim üretildikten sonra kullanıcı, tam akışı yeniden başlatmadan açı, karakter, arka plan veya etkileşimi hızla değiştirebilir.

1. **Stüdyo.** Düz renkli arka planda temiz ürün çekimi. Kişi yok.
2. **Tutma.** Bir kişinin tuttuğu ürün. Eller veya kollar görünür.
3. **Giyme veya kullanma.** Giyilen (giysi, aksesuar) veya aktif kullanılan ürün (sürülen serum, yudumlanmış içecek, alınan takviye).

Her üretimde tek bir Fal çağrısı yapılır. Çıktılar aynı klasör içinde `_v1`, `_v2`, `_v3` olarak otomatik artış gösterir.

**Referans görsel kuralı, evrensel.** Her üretimde aynı referanslar yüklenir: ürün görseli ve (Tutma veya Giymeyle kaydedilmiş bir karakter için) karakterin `fullbody.png` dosyası. Beceri önceki üretimleri (v1, v2 vb.) referans olarak yüklemez. Varyasyonlar prompt değişiklikleriyle elde edilir, çıktılar girdi olarak zincire bağlanmaz.

---

## Adım 0a, Proje çıktı klasörünü belirle

Çıktılar Claude Code'un açık olduğu çalışma klasörüne kaydedilir. Önce bu Bash bloğunu çalıştır:

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
  mkdir -p "$TARGET/_assets/product-images" "$TARGET/_assets/product-shots" "$TARGET/_meta"
  echo "READY:$TARGET"
fi

# Marka belleğini (CLAUDE.md) oluştur. Marka klasörü varsa ve dosya
# eksikse çalışır. Yapacak bir şey yoksa sessiz ve tekrarsız çalışır.
if [ -d "$TARGET" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" ]; then
  bash "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi
```

- `PROTECTED:<path>`: Reddet ve kullanıcıya markaya özel bir alt klasörde Claude Code'u açmasını söyle. Dur.
- `FIRSTRUN:<path>`: "Ürün çekimlerini `<path>/_assets/product-shots/` dizinine kaydedeceğim. Bu klasöre ilk kez kaydediyorum, doğru mu? (evet/hayır)" diye sor. Evet'te klasörleri oluştur ve `<path>/_meta/folder-confirmed.flag` yaz. Hayır'da dur.
- `READY:<path>`: Sessizce devam et.

`$RFLAB` olarak yakala. Çıktılar şuraya kaydedilir:

```
$RFLAB/_assets/product-shots/<çıktı-adı>/
```

Ham yüklemeler şuraya kaydedilir:

```
$RFLAB/_assets/product-images/
```

---

## Adım 0b, Mevcut proje bağlamını otomatik keşfet

Proje klasörünü tara:

- `$RFLAB/11_Characters/` içinde kayıtlı karakterleri ara. Klasör adlarının listesini yakala. Tutma ve Giyme modlarında karakter kaynağı seçeneğini açar.
- `$RFLAB/02_Brand_DNA/` içinde en güncel Marka DNA'sı dosyasını ara. Bulunursa belirt.
- `$RFLAB/_assets/product-shots/` içinde önceki çekim klasörlerini ara. Kullanışlı bağlam.

Kullanıcıya tek kısa satırla bildir:

> Proje bağlamı: Marka DNA'sı bulundu, 3 karakter mevcut (sofia, kai, marcus).

Veya:

> Proje bağlamı: taze proje, henüz Marka DNA'sı veya karakter yok.

---

## Adım 1, Ürün görselini seç

Öncelik sırasıyla tara:

1. `$RFLAB/_assets/product-images/*.{png,jpg,jpeg,webp}`
2. `$RFLAB/_assets/product-shots/*/*_v*.png` (kullanıcılar bazen önceki çekimleri rafine eder)

Eşleşme varsa, göreli yollarla numaralı liste olarak göster. Kullanıcı bir numara seçer veya `yükle` der.

### `yükle` derlerse veya eşleşme yoksa

> Ürün görselinizi `$RFLAB/_assets/product-images/` dizinine bırakın. Dosya adı küçük harfle, kelimeler arasında tire, boşluksuz olsun, örn. `pynk-kutu-pembe.jpg`. Hazır olunca söyleyin.

Bekle, yeniden tara, güncellenmiş listeyi sun.

### Seçim sonrasında

Tam mutlak yolu `$SRC_IMG` olarak yakala. Claude prompt oluşturmadan önce görsel bağlamı edinmek için görseli Read aracıyla oku.

---

## Adım 2, Modu seç

> Ne tür bir çekim istiyorsunuz?
>
> **1. Stüdyo.** Düz renkli arka planda temiz ürün çekimi. Kişi yok.
> **2. Tutma.** Bir kişinin tuttuğu ürün. Eller veya kollar görünür.
> **3. Giyme veya kullanma.** Giyilen veya aktif kullanılan ürün.
>
> `1`, `2` veya `3` yanıtlayın.

`$MODE` olarak yakala.

---

## Adım 3, Kişi kaynağı (Yalnızca Tutma ve Giyme)

**Mod Stüdyo ise bu adımı atla.**

### Karakter varsa

> Çekimde kim olsun?
>
> **1. Kayıtlı karakter kullan (önerilir).** Mevcut: <liste>. Bir isim girin. Reklamlarda yüz tutarlılığı için en iyisi. Karakterin tam boy görseli referans olarak eklenir.
> **2. Rastgele kişi.** Kişiyi tarif ediyorum, model her üretimde yeni bir yüz yaratır.
> **3. Atla.** Tarif yok. Model kendisi uydurur.
>
> Bir karakter adı, `rastgele` veya `atla` yazın.

### Karakter yoksa

> Bu projede henüz karakter yok. Reklamlarda yüz tutarlılığı için önce `/reklam-fabrikasi:character` çalıştırmanız önerilir.
>
> Şimdilik seçenekler:
>
> **1. Dur, önce `/reklam-fabrikasi:character` çalıştır, sonra bu beceriyi yeniden çalıştır.**
> **2. Rastgele kişi.** Kişiyi tarif ediyorum, model yüzü kendisi üretir.
> **3. Atla.** Tarif yok.
>
> `1`, `rastgele` veya `atla` yazın.

### `$PERSON_SOURCE` olarak yakala

- Karakter adı: `$RFLAB/11_Characters/<ad>/character-spec.json` dosyasını oku. `characteristics` değerini `$PERSON_DESC` ve `$RFLAB/11_Characters/<ad>/fullbody.png` yolunu `$PERSON_REF` olarak yakala.
- `rastgele`: aşağıdaki takip sorusunu sor.
- `atla`: `$PERSON_DESC` boş, `$PERSON_REF` yok.

### Rastgele kişi takip sorusu

> Kişiyi tek satırda tarif edin. Örnekler:
>
> - `otuzlu yaşların ortası kadın, Akdenizli, bakımlı tırnaklar`
> - `yirmili yaşların başı erkek, atletik yapı`
> - `altmışlı yaşlarda yaşlı adam, yıpranmış eller`
>
> Tarifle yanıtlayın.

`$PERSON_DESC` olarak yakala.

---

## Adım 4, Etkileşim (Yalnızca Giyme modu)

**Mod Stüdyo veya Tutma ise bu adımı atla.**

> Etkileşim ne olsun? Vücut bölgesi ve eylem hakkında spesifik olun.
>
> Örnekler:
>
> - `tişörtü giyiyor`
> - `kolyeyi takıyor, kolye ucu köprücük kemiğinde`
> - `yüze serum sürüyor, parmak uçları elmacık kemiğinde`
> - `kutudan yudum içiyor, dudağa kaldırılmış`
> - `bileğe parfüm sıkıyor`
>
> Etkileşimi yazın.

`$INTERACTION` olarak yakala.

---

## Adım 5, Arka plan veya sahne

### Mod Stüdyo ise

> Arka plan ne olsun? Varsayılan temiz beyaz. Ya da bir renk veya yüzey tarifi seçin, örn. `yumuşak bej`, `soluk adaçayı yeşili`, `sıcak krem`, `mat siyah`, `açık gri mermer yüzey`.
>
> Bir tarif veya `varsayılan` yazın.

### Mod Tutma veya Giyme ise

> Sahne veya arka plan ne olsun? İki seçenek:
>
> **A. Düz arka plan.** Renk veya yüzey tarifi, örn. `soluk bej dikişsiz`, `açık gri beton duvar`. Ürün ön planda olacaksa iyi seçim.
> **B. Yaşam tarzı sahnesi.** Tek satırda gerçek bir ortam, örn. `aydınlık sabah mutfağı, mermer tezgah, yumuşak pencere ışığı`, `açık hava sokak, öğleden sonra, altın saat`.
>
> Bir tarif (A seçeneği) veya `sahne: <tarif>` (B seçeneği) yazın. Varsayılan `soluk bej dikişsiz` için `varsayılan` yazın.

`$BACKGROUND` olarak yakala.

---

## Adım 6, En-boy oranı

>   1:1   kare (varsayılan, reklam yerleşimi esnekliği için en iyisi)
>   9:16  dikey (Hikayeler, Reels, mobil)
>   4:5   portre (mobil feed için ideal)
>   16:9  yatay (açılış sayfaları, bannerlar)
>
> Birini veya `varsayılan` yazın.

`$ASPECT` olarak yakala.

---

## Adım 7, Model

> Hangi modeli kullanayım?
>
> **1. GPT Image 2** (önerilir). Yüksek kalite, en-boy oranına göre 4K eşdeğeri `image_size` (16:9 için 3840x2160, 9:16 için 2160x3840, 1:1 için 2880x2880, 4:5 için 2560x3200). Şu an mevcut en iyi görsel üretim modeli. Ürün detayı, metin rendering, yüz tutarlılığı ve karmaşık promptlarda Nano Banana 2 ve Nano Banana Pro'dan üstün.
> **2. Nano Banana 2.** Üretim başı maliyeti düşük tutmak isteyen kullanıcılar için daha ucuz alternatif. Tercih sebebi yalnızca fiyat; karakter referansı ekli olup olmaksızın GPT Image 2 tüm kalite eksenlerinde kazanır.
>
> `1`, `2` veya GPT Image 2 için `varsayılan` yazın.

`$MODEL` olarak yakala.

---

## Adım 8, Onay özeti

Her şeyi gerçek değerleri doldurarak tek mesajda göster:

```
Temel çekim üretmeye hazır:

  Mod:          <Stüdyo / Tutma / Giyme veya kullanma>
  Ürün:         <seçilen görselin göreli yolu>
  Kişi:         <karakter adı / tarifiyle rastgele / atlandı>
  Etkileşim:    <metin>      (yalnızca Giyme modunda)
  Arka plan:    <metin>
  En-boy:       <oran>
  Model:        <GPT Image 2 / Nano Banana 2>
  Çıktı:        $RFLAB/_assets/product-shots/<çıktı-adı>/

Devam etmek için onaylayın veya düzenleyin:
  "mod <stüdyo / tutma / giyme>"
  "kişi <karakter adı / rastgele / atla>"
  "etkileşim <metin>"
  "arka plan <metin>"
  "en-boy <oran>"
  "model <gpt-image-2 / nano-banana-2>"
```

`<çıktı-adı>` değerini kaynak dosya adından ve moddan türet, küçük harf, tire kullan.

Örnekler:
- `pynk-kutu-pembe.jpg` + Stüdyo = `pynk-kutu-pembe-studio`
- `pynk-kutu-pembe.jpg` + Tutma = `pynk-kutu-pembe-held`
- `serum-30ml.png` + Giyme = `serum-30ml-worn`

Mevcut bir klasörle çakışma varsa ayırt edici ekle (karakter adı veya kısa zaman damgası).

Kullanıcının onaylamasını veya düzenlemesini bekle.

---

## Adım 9, Spec dosyasını yaz

Çıktı klasörünü oluştur ve spec dosyasını yaz:

```
$RFLAB/_assets/product-shots/<çıktı-adı>/
  product-shot-spec.json
```

**product-shot-spec.json:**

```json
{
  "output_name": "<çıktı-adı>",
  "mode": "<studio | held | worn>",
  "source_image": "<ürün görselinin mutlak yolu>",
  "person_source": "<karakter adı | random | skip>",
  "person_description": "<özellikler veya tek satır tarif veya boş>",
  "person_reference_image": "<karakter fullbody.png mutlak yolu veya boş>",
  "interaction": "<metin veya boş>",
  "background": "<arka plan veya sahne metni>",
  "aspect_ratio": "<oran>",
  "model": "<gpt-image-2 | nano-banana-2>",
  "current_prompt": "<doldurulmuş prompt, aşağıdaki Promptlar bölümüne bak>",
  "history": []
}
```

`current_prompt` değerini bu dosyanın altındaki eşleşen şablona değişkenleri yerleştirerek doldur. `history` dizisi şimdilik boş kalır; Adım 11'deki v1 sonrası döngüde her sonraki üretimle birlikte ekleme yapılır.

---

## Adım 10, Üretim yolunu seç

> Temel çekim hazır. Nasıl üretmek istersiniz?
>
> **A. Manuel yapıştırma.** Ücretsiz. Promptu model arayüzüne yapıştır, referansları ekle, çıktıyı kaydet.
> **B. Higgsfield MCP.** İlk kullanımda tek seferlik OAuth girişi. Higgsfield kredileri kullanır. GPT Image 2 ve Nano Banana 2 için çalışır.
> **C. Fal.ai sonuç başı ödeme.** Görsel başı yaklaşık 0,10-0,20 dolar. `fal_api_key` gerektirir. Her iki model için çalışır.
> **D. Playwright ile web arayüzü otomasyonu.** B veya C'den yavaş. Claude, GPT Image 2 için chatgpt.com'u, Nano Banana 2 için aistudio.google.com'u kullanır.
>
> A, B, C veya D yazın.

Seçilen yolu `$PATH_CHOICE` olarak yakala. Beceri bunu v1 sonrası döngüdeki sonraki üretimler için hatırlar.

---

### Yol A, Manuel yapıştırma

Promptu yazdır. Kullanıcıya hangi arayüze yapıştıracağını söyle; uygulanabilir olduğunda her iki referans görsel için de açık talimat ver.

**Model GPT Image 2 ise:**

> GPT Image 2'de manuel çalıştırma:
>
> 1. https://chatgpt.com/ adresini açın ve görsel üretici ile yeni bir sohbet başlatın.
> 2. Ürün görselini ekleyin: `$SRC_IMG`
> [`person_reference_image` ayarlıysa]
> 3. Karakter referans görselini ekleyin: `<person_reference_image>`
> 4. Bu promptu yapıştırın:
>
> ```
> <doldurulmuş prompt>
> ```
>
> 5. Çıktıyı `$RFLAB/_assets/product-shots/<çıktı-adı>/` dizinine `<çıktı-adı>_v1.png` olarak kaydedin.
> 6. Kaydedilince söyleyin.

**Model Nano Banana 2 ise:**

> Nano Banana 2'de manuel çalıştırma:
>
> 1. https://aistudio.google.com/ adresini açın ve Gemini 3.1 Flash Image'ı seçin.
> 2. Ürün görselini ekleyin: `$SRC_IMG`
> [`person_reference_image` ayarlıysa]
> 3. Karakter referans görselini ekleyin: `<person_reference_image>`
> 4. Bu promptu yapıştırın:
>
> ```
> <doldurulmuş prompt>
> ```
>
> 5. `$RFLAB/_assets/product-shots/<çıktı-adı>/` dizinine `<çıktı-adı>_v1.png` olarak kaydedin.
> 6. Kaydedilince söyleyin.

Kaydedildiği onaylandığında Adım 11'e geç.

---

### Yol B, Higgsfield MCP

Yol B, ürün çekimini doğrudan Claude Code içinde Higgsfield CLI aracılığıyla üretir. Higgsfield aboneliği olan kullanıcılar için en iyisi. Kullanıcıya görünen etiket `Yol B, Higgsfield MCP` olarak kalır; deneyim kullanıcı tarafında değişmez (aynı krediler, aynı modeller, aynı Higgsfield hesabı). Higgsfield hem GPT Image 2 hem de Nano Banana 2'yi destekler.

`../_shared/path-b-cli-implementation.md` dosyasını yükle ve oradaki B.0'dan B.9'a kadar olan adımları izle. Beceriye özgü değişkenler:

- `{{SKILL_SLUG}}`: `product-shot`
- `{{MODEL_ID}}`: spec'in `model` alanı `gpt-image-2` ise `gpt_image_2`, `nano-banana-2` ise `nano_banana_flash`
- `{{ASPECT}}`: spec'in `aspect_ratio` alanından (`1:1`, `9:16`, `4:5` veya `16:9`)
- `{{QUALITY}}`: `high` (GPT Image 2 için)
- `{{RESOLUTION}}`: GPT Image 2 için `4k`, Nano Banana 2 için `2k`
- `{{OUTPUT_DIR}}`: `$RFLAB/_assets/product-shots/<çıktı-adı>`
- `{{OUTPUT_FILENAME}}`: `<çıktı-adı>_v<N>.png`, `<N>` aynı klasör içinde otomatik artar (`_v1`, `_v2`, `_v3`)
- Referans görseller: `source_image`'daki ürün görseli her zaman eklenir. `person_reference_image` ayarlıysa (kayıtlı karakterli Tutma veya Giyme), karakter `fullbody.png`'si ikinci referans olarak eklenir.

**Tek görsel üretimi.** Bu beceri her çağrıda bir görsel üretir (temel çekim veya Adım 11 döngüsünde bir varyasyon). Paylaşılan dokümanın paralel toplu iş rehberi bu beceri için geçerli değil; her çağrı tek bir üretimdir.

**Onay özeti ifadesi (B.5).**

> Üretim: 1 görsel.
> Model: <GPT Image 2 / Nano Banana 2>
> Mevcut Higgsfield bakiyesi: <B.3'ten kredi>
> Üretim başı maliyet: <B.4'ten kredi>
>
> Devam etmek için `evet` onaylayın.

**Referans sırası (B.6).** Önce ürün görselini, sonra spec'te `person_reference_image` ayarlıysa karakter `fullbody.png`'sini gönder. Önceki çıktı versiyonlarını (`_v1.png`, `_v2.png` vb.) referans olarak yükleme; becerinin giriş bölümündeki evrensel referans kuralı CLI altında da geçerlidir.

**Manifest (B.9).** Çıktılar toplu iş yerine tekil versiyonlanmış dosyalar olduğundan bu beceri için isteğe bağlı. Spec'in `history` dizisi zaten her versiyonun promptunu `$RFLAB/_assets/product-shots/<çıktı-adı>/product-shot-spec.json` altında izler (Adım 9'a bak). Paylaşılan manifest formatı yalnızca Adım 11 v1 sonrası döngüsünde tek oturumda 5 veya daha fazla varyasyon üretildiğinde zorunludur.

**V1 sonrası döngü yeniden kullanımı.** Paylaşılan dokümanın B.0 kurulum kontrolü ve B.1 kimlik doğrulama kontrolü oturum başına yalnızca bir kez çalışır. Adım 11 döngüsündeki sonraki varyasyonlar, kurulum veya giriş adımını yeniden yapmadan aynı `HIGGS_BIN` ve kimliği doğrulanmış oturumu kullanır.

Eski MCP araç adları (`mcp__higgsfield__balance`, `mcp__higgsfield__generate_image` vb.) artık kullanılmıyor. CLI aynı Higgsfield hesabını, aynı kredileri ve aynı modelleri, `/mcp` ile Clerk yerine `higgsfield auth login` üzerinden OAuth akışını kullanarak sunar.

---

### Yol C, Fal.ai direkt API

**Yol C.0, Ön çalışma kontrolü.** `fal-ai-prerun-check` koruma becerisini çalıştır. Başarısız olursa devam etme.

**Yol C.1, Maliyet onayı.**

GPT Image 2 ise: "Yol C maliyeti: yüksek kalitede ve 4K eşdeğerinde tek bir GPT Image 2 üretimi için yaklaşık 0,15-0,25 dolar. `evet` onaylayın."

Nano Banana 2 ise: "Yol C maliyeti: 2K'da tek bir Nano Banana 2 üretimi için yaklaşık 0,12 dolar. `evet` onaylayın."

**Yol C.2, Üret.**

1. Spec'i oku.
2. Görselleri fal-ai MCP'ye yükle:
   - `$SRC_IMG` ile `mcp__fal-ai__upload_file` çağır. `$SRC_URL` olarak yakala.
   - `person_reference_image` ayarlıysa, o yol ile `mcp__fal-ai__upload_file` çağır. `$PERSON_URL` olarak yakala.
   - `image_urls` oluştur: Stüdyo veya kişi referansı yoksa `[$SRC_URL]`, her ikisi varsa `[$SRC_URL, $PERSON_URL]`.

**`gpt-image-2` ise**, `mcp__fal-ai__run_model`'ı şu parametrelerle çağır:
- `model`: `"openai/gpt-image-2/edit"`
- `prompt`: `current_prompt`
- `image_urls`: oluşturulan dizi
- `image_size` (fal.ai GPT Image 2 sınırları dahilinde 4K eşdeğeri, max kenar 3840 px, max toplam 8.294.400 px, her iki boyut 16'nın katı):
  - `1:1` için `{"width": 2880, "height": 2880}`
  - `9:16` için `{"width": 2160, "height": 3840}`
  - `4:5` için `{"width": 2560, "height": 3200}`
  - `16:9` için `{"width": 3840, "height": 2160}`
- `num_images`: 1
- `quality`: `"high"`
- `output_format`: `"png"`

Not: `openai/gpt-image-2/edit` endpoint'i `safety_tolerance` parametresini kabul etmez. Çağrıya ekleme.

**`nano-banana-2` ise**, `mcp__fal-ai__run_model`'ı şu parametrelerle çağır:
- `model`: `"fal-ai/nano-banana-2/edit"`
- `prompt`: `current_prompt`
- `image_urls`: oluşturulan dizi
- `aspect_ratio`: spec'ten
- `resolution`: `"2K"`
- `num_images`: 1
- `output_format`: `"png"`
- `safety_tolerance`: `"4"`

3. Dönen görsel URL'yi indir ve `$RFLAB/_assets/product-shots/<çıktı-adı>/<çıktı-adı>_v1.png` olarak kaydet (varsa otomatik artış).
4. Kullanıcıya söyle: "`<çıktı-adı>_v1.png` olarak kaydedildi."

---

### Yol D, Playwright web arayüzü

**Katı kurallar:**

1. Otomatik yükleme yapma. Her yükleme için açık onay gerekir.
2. `evet` olmadan Üret'e tıklama.

**Yol D.1, İlk kullanım kontrolü.** `mcp__playwright__*` araçlarını ara. Yoksa dur.

**Yol D.2, Arayüzü aç.** GPT Image 2 için chatgpt.com'u, Nano Banana 2 için aistudio.google.com'u açmak üzere `mcp__playwright__browser_navigate` kullan. Girişi onayla. Sor: "Başlamaya hazır mısınız? (evet / hayır)"

**Yol D.3, Üretimi çalıştır.**

1. `evet`te ürün görselini ekle. Onayla: "Ürün görseli eklendi. Devam edilsin mi? (evet / hayır)"
2. `person_reference_image` ayarlıysa ekle. Onayla: "Karakter referansı eklendi. Devam edilsin mi? (evet / hayır)"
3. `current_prompt`'ı yapıştır. Onayla: "Prompt yapıştırıldı. Üret'e tıklansın mı? (evet / hayır)"
4. `evet`te Üret'e tıkla. Bekle.
5. Playwright ile indir. `<çıktı-adı>_v1.png` olarak kaydet (varsa otomatik artış).
6. Kullanıcıya söyle: "`<çıktı-adı>_v1.png` olarak kaydedildi."

---

## Adım 11, V1 sonrası döngü

V1 (veya sonraki herhangi bir versiyon) kaydedildikten sonra döngüyü sun:

> Kaydedildi: `<yol>/<çıktı-adı>_vN.png`
>
> Sırada ne var? Bir numara seçin veya değiştirmek istediğinizi tarif edin.
>
> **1. Farklı açı.** Aynı çekim, yeni kamera açısı, örn. "yukarıdan", "yan profil", "elde daha yakın", "45 derece eğimli".
> **2. Karakter değiştir.** [Yalnızca Tutma / Giyme] Farklı bir kayıtlı karakter seç, rastgeleye geç veya yeni kişi tarif et.
> **3. Arka plan veya sahne değiştir.** Yeni arka plan veya sahne tarifi.
> **4. Etkileşimi ayarla.** [Yalnızca Giyme] Yapılan eylemi değiştir.
> **5. Yeniden üret.** Aynı prompt, yeni varyasyon (aynı girdiden farklı sonuç).
> **6. Bitti.** Tamamla ve sıradakini öner.

Yanıtı bekle. Ardından seçilen seçeneği işle.

### Seçenek 1, Farklı açı

Sor: "Açıyı tek satırda tarif edin."

`$ANGLE_CHANGE` olarak yakala. Spec'i güncelle:

1. Önceki `current_prompt`'u `history`'ye ekle; `version`, `timestamp` ve `change` alanlarını doldur (ilk varyasyonsa "temel çekim", aksi halde son değişikliğin açıklaması).
2. Mod şablonundan (Promptlar bölümü) `current_prompt`'u yeniden oluştur; diğer tüm değişkenleri aynı bırak, yalnızca açı satırını değiştir veya ekle. Açı açıklamasını prompttaki "Format:" satırından hemen önce yeni bir satır olarak ekle, örn. `Camera angle: <angle_change>.`
3. Güncellenmiş spec'i kaydet.

Aynı yolu (`$PATH_CHOICE`) aynı referans görsellerle (ürün + isteğe bağlı karakter) çalıştır. Çıktı `_v2`, `_v3` vb. olarak kaydedilir.

Üretim sonrası Adım 11'e dön.

### Seçenek 2, Karakter değiştir (Yalnızca Tutma / Giyme)

Mevcut duruma göre şunlardan birini sor:

Kayıtlı karakter varsa:

> Farklı bir karakter seçin. Mevcut: <mevcut hariç isimler listesi>. Anında yeni kişi tarif etmek için `rastgele`, karakter referansını kaldırmak için `atla` yazın.

Kayıtlı karakter yoksa:

> Yeni kişi tarif etmek için `rastgele`, karakter referansını kaldırmak için `atla` yazın.

Spec'i güncelle:

1. Önceki `current_prompt`'u `history`'ye ekle.
2. Yeni seçime göre `person_source`, `person_description`, `person_reference_image` alanlarını güncelle.
3. Yeni kişi değerleriyle mod şablonundan `current_prompt`'u yeniden oluştur.
4. Güncellenmiş spec'i kaydet.

**Referans yükleme kuralı:** Yeni üretimde ürün görseli ve (uygulanabilirse) yeni karakter `fullbody.png`'si yüklenir. Beceri önceki çıktı versiyonlarını referans olarak yüklemez.

Aynı yolu çalıştır. Çıktı artar. Adım 11'e dön.

### Seçenek 3, Arka plan veya sahne değiştir

Sor: "Yeni arka plan veya sahne ne olsun?"

Yeni `$BACKGROUND` olarak yakala. Spec'i güncelle:

1. Önceki `current_prompt`'u `history`'ye ekle.
2. `background`'u güncelle.
3. `current_prompt`'u yeniden oluştur.
4. Güncellenmiş spec'i kaydet.

Aynı yolu çalıştır. Çıktı artar. Adım 11'e dön.

### Seçenek 4, Etkileşimi ayarla (Yalnızca Giyme)

Sor: "Yeni etkileşim ne olsun?"

Yeni `$INTERACTION` olarak yakala. Spec'i güncelle, promptu yeniden oluştur, kaydet, çalıştır, artır, geri dön.

### Seçenek 5, Yeniden üret

Spec değişmeden aynı yolu çalıştır. Model aynı girdiden farklı bir sonuç üretir. Çıktı artar. Adım 11'e dön.

### Seçenek 6, Bitti

Onayla ve bir sonraki aşamanın becerisini öner:

> Tamamlandı. `<çıktı-adı>` için çekim serisi `$RFLAB/_assets/product-shots/<çıktı-adı>/` dizininde. N versiyon kaydedildi.
>
> Sırada ne var?
>
> - Bu çekimlerden birini ürün görseli olarak kullanarak reklam üretmek için `/reklam-fabrikasi:static` çalıştırın
> - Bunlardan biri kazanan bir kreatifse ölçeklendirmek için `/reklam-fabrikasi:multiplier` çalıştırın
> - Bu ürünü içeren UGC video senaryoları için `/reklam-fabrikasi:ugc-prompt` çalıştırın
> - Ya da burada bitirin

Beceri çalışmasını sonlandır.

---

## Promptlar

Her mod için üç şablon. Değişkenleri yerleştir. Yapıyı yerleştirmenin ötesinde değiştirme.

### Stüdyo modu promptu

```
The reference image defines every detail of the product. Reproduce it without alteration. Every colour, every surface, every text element, and every proportion must match the reference exactly as photographed. Do not alter any element of the product. Reproduce all text as written: same spelling, same weight, same position on the product.

Light the product with a single soft overhead source. Even coverage, no hard shadows.

Background: <background>. Flat solid colour, no gradient, no texture, nothing bleeding in from the product.

Product centred and upright in the frame, with even space around it. No hands, no props, no studio equipment.

Format: <orientation> framing for <aspect> output.
```

### Tutma modu promptu

```
The first reference image defines every detail of the product. Reproduce the product without alteration. Every colour, every surface, every text element, and every proportion must match the reference exactly. Reproduce all text on the product as written: same spelling, same weight, same position.

<person_block>

The person holds the product naturally in their hand or hands, product clearly visible to the camera with the label and branding fully readable. Natural hand to product interaction, no awkward finger positioning, no warping or distortion of the product or the hand. The product is the visual hero of the shot.

Scene: <background>.

Light: Natural even daylight, soft directional, no harsh shadows. Colour grade clean and neutral, no heavy filter.

Camera: 50mm lens equivalent, f/2.8, shot from a natural eye level perspective. Sharp focus on the product, gentle background separation.

Format: <orientation> framing for <aspect> output.
```

### Giyme veya kullanma modu promptu

```
The first reference image defines every detail of the product. Reproduce the product without alteration. Every colour, every surface, every text element, and every proportion must match the reference exactly. Reproduce all text on the product as written: same spelling, same weight, same position.

<person_block>

Interaction: <interaction>. The action looks natural and unforced, no posed or stiff feel. The product is fully visible and clearly identifiable, label readable wherever applicable. Realistic body proportions, no warping or distortion.

Scene: <background>.

Light: Natural even daylight, soft directional, no harsh shadows. Colour grade clean and neutral.

Camera: 50mm lens equivalent, f/2.8, shot from a natural eye level perspective. Sharp focus on the interaction zone (the part of the body where the product is being worn or used).

Format: <orientation> framing for <aspect> output.
```

### `<person_block>` yerleştirme kuralı

- Karakter seçildi: "The person in the shot must exactly match the second reference image. Maintain face consistency, skin tone, hair, facial features, body proportions. Characteristics: <person_description>."
- Rastgele: "The person is <person_description>."
- Atla: "A person is in the shot."

### `<orientation>` yerleştirme kuralı

- `1:1` için "square"
- `9:16` için "vertical portrait"
- `4:5` için "portrait"
- `16:9` için "horizontal landscape"

### Kamera açısı ekleme (v1 sonrası döngü, Seçenek 1)

Döngüde kullanıcı bir açı değişikliği tarif ettiğinde, yeniden oluşturulan prompttaki `Format:` satırından hemen önce şu satırı ekle:

```
Camera angle: <angle_change>.
```

Açı değişikliği mevcut `Camera:` satırıyla çelişiyorsa (örn. "yukarıdan" ile "natural eye level perspective" çelişirse), tüm `Camera:` satırını yeni açı ve teknik özelliklerle değiştir:

```
Camera: <angle_change>. 50mm lens equivalent, f/2.8.
```

---

## Katı kurallar

1. **Fal çağrısı başına bir görsel.** Varyasyonlar v1 sonrası döngüden (Adım 11) veya becerinin yeniden çalıştırılmasından gelir.
2. **Otomatik üretim yapma.** V1 sonrası varyasyonlar dahil her üretim, ücretli yollar için açık `evet` gerektirir.
3. **Üzerine yazma.** Çıktılar aynı klasör içinde `_v1`, `_v2`, `_v3` olarak otomatik artar.
4. **Referans yükleme kuralı, evrensel.** Her üretimde şunlar yüklenir: ürün görseli ve (uygulanabilirse) karakter `fullbody.png`'si. Önceki çıktı versiyonlarını (v1, v2 vb.) referans olarak yükleme.
5. **Yol C için fal-ai-prerun-check korumasının geçmesi gerekir.**
6. **Ürün koruması tartışılmaz.** "Reproduce all text as written" satırı üç promptta da zorunludur. Yumuşatma veya kaldırma.
7. **Karakter modunda her iki referans da yüklenir.** `person_reference_image` ayarlıysa üretim aracına hem ürün hem de karakter referansı gönderilir. Karakter ayarlıyken yalnızca ürün görseli ile üretim çağrısı yapma.
8. **V1 sonrası döngü aynı yolu kullanır.** Adım 10'da seçilen yol (`$PATH_CHOICE`) döngüdeki her varyasyon için kullanılır. Kullanıcıdan varyasyon başına yol seçimi isteme.
9. **`openai/gpt-image-2/edit` endpoint'i `safety_tolerance` kabul etmez.** Yalnızca `fal-ai/nano-banana-2/edit` kabul eder. GPT Image 2 endpoint'ine `safety_tolerance` gönderme.
10. **Beceri çıktısında hiçbir yerde cümle duraklaması olarak tire veya kısa çizgi kullanma.** Virgül, "ve" kullan ya da cümleyi böl.

---

## Notlar

- Bu beceri üç ayrı becerinin (stüdyo çekimi, tutma çekimi, giyim çekimi) yerine geçer. Adım 2'deki mod seçici yüzey alanını küçük tutar.
- Adım 11'deki v1 sonrası döngü bu beceriyi verimli kılar. Kullanıcılar temel çekimi üretir, ardından tam akışı yeniden başlatmadan açıları, karakterleri ve arka planları hızla keşfeder.
- Varyasyonlar prompt değişiklikleriyle elde edilir, çıktılar girdi olarak zincire bağlanmaz. Beceri önceki bir üretimi referans görsel olarak beslemez. Bu, her üretimi deterministik tutar ve versiyonlar arasında sürüklenmeyi önler.
- Kullanıcının bıraktığı görseller `_assets/product-images/` altında yaşar. Tüm ürün çekimi çıktıları `_assets/product-shots/<çıktı-adı>/` altındadır. Her ikisi de proje kapsamlıdır.
- Stüdyo modu varlık hazırlama katmanıdır. Kaynak ürün görseli temiz değilse önce çalıştır, ardından temizlenmiş stüdyo çıktısını Tutma veya Giyme modları için ürün kaynağı olarak kullan.
- Tutma ve Giyme modlarındaki karakter entegrasyonu, marka UGC'sinin reklamlar arasında tutarlı olmasını sağlar. `/reklam-fabrikasi:character` ile kadro oluşturan kullanıcılar burada varsayılan olarak onu kullanmalıdır. Rastgele, yüz tutarlılığının önemli olmadığı tek seferlik çekimler içindir.
- GPT Image 2 eklenti genelinde önerilen modeldir. Yüksek kalite, 4K eşdeğeri `image_size`. Şu an mevcut en iyi görsel üretim modeli; ürün detayı, metin rendering, yüz tutarlılığı ve karmaşık promptlarda Nano Banana 2 ve Nano Banana Pro'dan üstündür. Karakter referansı ekli olduğunda Nano Banana 2'yi öneren eski yumuşak yönlendirme v1.5.0'da kaldırıldı; karakter ekli olup olmaksızın GPT Image 2 doğru seçimdir.
- Nano Banana 2, üretim başı maliyeti düşük tutmak isteyen kullanıcılar için daha ucuz alternatif olarak mevcut kalmaya devam eder. Tercih sebebi yalnızca fiyat.
- Higgsfield, Mayıs 2026 katalog güncellemesiyle hem GPT Image 2 hem de Nano Banana 2'yi destekler; Yol B hangi model seçilirse seçilsin çalışır.
- Çalışma ortasında Fal veya Higgsfield hatası neredeyse her zaman kimlik bilgisi katmanına işaret eder. Kesin hatayı ortaya çıkarmak için `/reklam-fabrikasi:doctor` çalıştır.
- Ürün metni yanlış render olursa Adım 11'deki Seçenek 5 (Yeniden üret) ile yeniden üret. Her iki model de zaman zaman metinde kayar. Ucuz çözüm yeniden çalıştırmaktır, prompt mühendisliği değil.
- Yaşam tarzı sahnesi arka planları için açıklamaları tek kısa satırda tut. Uzun sahne açıklamaları ürünle prompt dikkatini paylaşır ve ürün doğruluğunu olumsuz etkiler.
