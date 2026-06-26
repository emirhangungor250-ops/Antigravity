---
name: reklam-fabrikasi-character
description: "Kullanıcı UGC, reklam veya içerik için bir veya birden fazla marka karakteri oluşturmak istediğinde bu beceriyi kullan. Şu komutlarda tetikle: /character, /create character, /brand character, /casting digital, /character creator, /build character, ya da doğal dil ifadelerinde: 'marka karakteri oluşturmak istiyorum', 'bana bir karakter yap', 'casting digital yap', 'UGC karakterine ihtiyacım var', 'marka kadrosu oluştur', 'markam için 5 karakter üret'. Çalıştırma başına 1-10 arası toplu işi her zaman destekler, tam marka kadrosu için varsayılan 5. Her karakter, karakter başına bir alt klasörde 3:4 oranında eşleşen vesikalık artı tam boy çifti olarak çıktı verir. Model seçici: GPT Image 2 (önerilir, yüksek kalite, fal.ai GPT Image 2 8,3 megapiksel sınırı altındaki en büyük 3:4 boyutu olan 2400x3200 image_size) veya daha ucuz alternatif olarak 3:4 2K Nano Banana 2. Yol A (manuel yapıştırma), Yol B (Higgsfield MCP, her iki model), Yol C (fal.ai direkt, fal-ai-prerun-check ile korumalı, her iki model), Yol D (Playwright GPT Image 2 için chatgpt.com'u, Nano Banana 2 için aistudio.google.com'u kullanır) seçeneklerini içerir."
---

# Reklam Fabrikası, Marka Karakteri Oluşturucu

Bu beceri bir marka kadrosu oluşturur. Her karakter, eşleşen vesikalık artı tam boy kadro dijitali olarak `11_Characters/<karakter-adı>/` altına kaydedilir; aşağı akış UGC, ürün UGC ve içerik becerilerine hazır şekilde.

Varsayılan toplu iş çalıştırma başına 5 karakterdir. Kullanıcı 1 ile 10 arasında istediğini seçebilir.

Karakter başına iki görsel:

1. **Vesikalık.** Sıkı kadro portresi, düz karşıdan, klinik stüdyo aydınlatması, 3:4
2. **Tam boy.** Vesikalık yüz referans olarak kullanılarak oluşturulan tam uzunluk kadro dijitali, 3:4

Varsayılan görsel modeli GPT Image 2'dir (`openai/gpt-image-2/edit` fal.ai üzerinde) ve `quality: "high"` ile `image_size: {"width": 2400, "height": 3200}` parametreleri kullanılır. Bu, fal.ai GPT Image 2 kısıtlarını (max kenar 3840 px, max toplam 8.294.400 px, her iki boyut 16'nın katı) karşılayan en büyük 3:4 boyutudur. Nano Banana 2, `aspect_ratio: "3:4"` ve `resolution: "2K"` ile daha ucuz alternatif olarak kullanılabilir.

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
  mkdir -p "$TARGET/11_Characters" "$TARGET/_meta"
  echo "READY:$TARGET"
fi

# Marka belleğini (CLAUDE.md) oluştur. Marka klasörü varsa ve dosya
# eksikse çalışır. Yapacak bir şey yoksa sessiz ve tekrarsız çalışır.
if [ -d "$TARGET" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" ]; then
  bash "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi
```

- `PROTECTED:<path>`: Reddet ve kullanıcıya markaya özel bir alt klasörde Claude Code'u açmasını söyle. Dur.
- `FIRSTRUN:<path>`: "Karakterleri `<path>/11_Characters/` dizinine kaydedeceğim. Bu klasöre ilk kez kaydediyorum, doğru mu? (evet/hayır)" diye sor. Evet'te klasörleri oluştur ve `<path>/_meta/folder-confirmed.flag` yaz. Hayır'da dur.
- `READY:<path>`: Sessizce devam et.

Belirlenen yolu `$RFLAB` olarak yakala. Her karakteri şuraya kaydet:

```
$RFLAB/11_Characters/<karakter-adı>/
```

## Adım 0b, Mevcut proje bağlamını otomatik keşfet

Bu proje klasöründe mevcut marka bağlamını taramak için `ls` ve Read aracını kullan:

- `$RFLAB/02_Brand_DNA/` içinde en güncel Marka DNA'sı belgesi (markdown veya HTML)
- `$RFLAB/01_VOC_Research/` içinde en güncel VOC araştırma çıktısı
- `$RFLAB/11_Characters/` içinde mevcut karakterler (ad çakışmalarını önlemek için)

Güncel bir Marka DNA'sı dosyası varsa oku ve kullanıcıya şunu söyle: "Bu proje klasöründen Marka DNA'sı olarak `<dosyaadı>` kullanılıyor." Bu, Adım 3'teki otomatik yolu açar.

Marka DNA'sı dosyası yoksa otomatik yol kullanılamaz; kullanıcı doğrudan manuel forma geçer.

`11_Characters/` altında mevcut karakter klasörleri varsa, kullanıcının zaten ne olduğunu görmesi ve yinelenen adlardan kaçınabilmesi için listele.

---

## Adım 1, Kaç karakter

Kullanıcıya sor:

> Kaç karakter oluşturmak istiyorsunuz? Tam marka kadrosu için varsayılan 5, 1 ile 10 arasında istediğinizi seçebilirsiniz.
>
> Bir sayı yazın veya 5 için "varsayılan" deyin.

1 ile 10 arasında bir tamsayı bekle. Kullanıcı bu aralık dışında bir şey yazarsa geçerli aralığı belirterek tekrar sor. Cevabı `N` olarak yakala.

---

## Adım 2, Otomatik veya manuel

Bu soruyu yalnızca Adım 0b'de Marka DNA'sı dosyası bulunduysa sor. Marka DNA'sı yoksa doğrudan Adım 3 manüele geç.

> Marka DNA'nızı buldum. Kadro oluşturmak için iki seçenek:
>
> 1. **Otomatik.** Marka DNA'sını okuyorum, markanın hedef kitlesini, konumlandırmasını ve atmosferini analiz ediyorum, ardından markaya uyan N farklı karakter öneriyorum. Üretmeden önce önerilen kadroyu inceleyip düzeltebilirsiniz.
> 2. **Manuel.** Her karakter için ayrıntıları kendiniz doldurursunuz.
>
> `1` veya `2` yazın.

Yanıtı bekle. `MOD` olarak yakala.

---

## Adım 3, Özellikleri topla

### MOD otomatik ise

Marka DNA'sı belgesini tam olarak oku. Özellikle şunlara odaklan:

- Hedef kitle (yaş aralığı, yaşam tarzı, zihniyet)
- Ses sıfatları (kadronun görünümünü ve tonunu ayarlar)
- Fotoğrafçılık stili ve atmosfer
- Katı kurallar (herhangi bir görsel kısıt)

N farklı karakter profili oluştur. Kadro uyumlu hissettirmeli (hepsi makul biçimde aynı marka dünyasında yer alabilmeli) ama görsel olarak çeşitli olmalı (farklı yaşlar, etnik kökenler, vücut tipleri ve görünümler; böylece markanın UGC'si tek bir yüz gibi görünmez). Genel tanımlamalardan kaçın. Spesifik ol.

Her karakter için bu tam spec'i içten doldur:

```
KİMLİK
Yaş:
Cinsiyet:
Milliyet:

YÜZ
Cilt tonu:
Çene hattı:
Yüz şekli:
Göz şekli:
Göz rengi:
Kaşlar:
Burun:
Dudaklar:
Yüz kılı:
Çil / cilt detayları:
Elmacık kemikleri:

SAÇ
Renk:
Stil:

YAPIYA
Boy:
Vücut tipi:

GİYİM
Üst:
Alt:
Ayakkabı:
Aksesuar:

GÖRÜNÜM
Ton:
```

Önerilen tüm N karakteri tek bir mesajda numaralı liste olarak sun; her karakter için temel alanları görünür hale getir. Sor:

> N karakterlik önerilen kadro burada. Üretmeden önce herhangi birini düzenlemek ister misiniz? "3'ü ayarla" diyerek 3. karakteri değiştirebilir, "2'yi Sofia olarak yeniden adlandır" diyerek adı güncelleyebilir, "4'ü daha yaşlı biriyle değiştir" diyebilir veya kadroyu olduğu gibi kabul etmek için "devam" diyebilirsiniz.

Kullanıcı `devam` veya eşdeğeri söyleyene kadar düzenlemeler üzerinde döngü yap. Her karakter için tam spec'i bellekte tut.

### MOD manuel ise

N karakter boyunca döngü yap. Her karakter için aşağıdaki formu tek bir gruplandırılmış mesaj olarak göster. Birincisini "N içinde Karakter 1" olarak çerçevele; böylece kullanıcı toplu işte nerede olduğunu bilir.

Aşağıdaki formu tam olarak yazıldığı gibi kopyala. Yeniden biçimlendirme, yeniden ifade etme veya örnekleri kaldırma.

```
[N] içinde Karakter [I], uygun olan her şeyi doldurun. Uymayan yerleri boş bırakın:

KİMLİK
Yaş:
Cinsiyet:
Milliyet:

YÜZ
Cilt tonu:
Çene hattı:
Yüz şekli:
Göz şekli:
Göz rengi:
Kaşlar:
Burun:
Dudaklar:
Yüz kılı:
Çil / cilt detayları:
Elmacık kemikleri:

SAÇ
Renk:
Stil:

YAPIYA
Boy:
Vücut tipi:

GİYİM
Üst:         (örn. Beyaz oversize hoodie)
Alt:         (örn. Mavi kot)
Ayakkabı:    (örn. Beyaz Air Force 1)
Aksesuar:    (örn. Altın zincir, siyah kep)

GÖRÜNÜM
Ton:         (örn. Ham ve özgün, cilalı editoryal, sportif, lüks, sokak)
```

Kullanıcı her formu gönderdikten sonra tam listeyi geri onayla; bir sonraki karaktere geçmeden önce değiştirmek isteyip istemediklerini sor. Boş giyim alanları belgelenmiş varsayılanlara (beyaz tişört, mavi kot, beyaz spor ayakkabı) sessizce döner. Kimlik, yüz, saç, yapı ve görünüm alanları asla varsayılanlarla doldurulmaz; boş demek boş demektir.

Tüm N form doldurulduktan sonra Adım 4'e geç.

---

## Adım 4, Karakterleri adlandır

Kullanıcıya tek bir mesajda sor:

> Tüm N karakteri adlandırın. Bunlar klasör adları olacak, bu yüzden her biri tek kelime olsun, örn. `sofia`, `kai`, `marka-kahramani`, `marcus`, `jade`.
>
> Yukarıdaki kadroyla aynı sırada, N adı virgülle ayırarak yazın.

Her adı kısaltın: küçük harf, tireler, boşluk veya özel karakter yok. Kısaltmaların `$RFLAB/11_Characters/` altındaki mevcut klasörlerle çakışmadığını doğrula. Çakışma bulunursa hangi adın alındığını kullanıcıya söyle ve bir yedek iste.

---

## Adım 5, Toplu iş onay özeti

Tam kadroyu kullanıcıya tek bir mesajda göster:

```
N karakter üretmeye hazır:

1. <ad-1>, <yaş>, <cinsiyet>, <milliyet>, <tek satır görünüm özeti>
2. <ad-2>, <yaş>, <cinsiyet>, <milliyet>, <tek satır görünüm özeti>
...
N. <ad-N>, <yaş>, <cinsiyet>, <milliyet>, <tek satır görünüm özeti>

Çıktı: $RFLAB/11_Characters/<her-ad>/headshot.png + fullbody.png

Her karakter iki görsel çağrısı olarak çalışır (önce vesikalık, sonra tam boy); toplam N çarpı 2 üretim.

Üretim yolunu seçmek için onaylayın.
```

Onay bekle. Kullanıcı bir şeyi değiştirmek isterse ilgili adıma geri dön.

---

## Adım 6, Spec dosyalarını yaz

Her karakter için çıktı klasörünü oluştur ve iki dosyayı yaz:

```
$RFLAB/11_Characters/<karakter-adı>/
  character-spec.json
  characteristics.md
```

**character-spec.json**, tam olarak bu formatı kullan:

```json
{
  "character_name": "<karakter-adı>",
  "brand": "<marka-dna'sından-marka-adı-veya-boş>",
  "model": "gpt-image-2",
  "characteristics": "Age: 28\nGender: Male\nNationality: Brazilian\nSkin tone: Deep warm brown\nFace shape: Square\nJawline: Strong\nEye shape: Deep-set\nEye colour: Dark brown\nEyebrows: Thick, natural\nNose: Broad, straight\nLips: Medium, defined\nHair colour: Black\nHair style: Short, low fade\nHeight: Tall\nBody type: Athletic\nTone: Raw and authentic",
  "top": "Black heavyweight tee",
  "bottom": "Cargo trousers, olive",
  "shoes": "Chunky white trainers",
  "accessories": "Silver ring"
}
```

`model` alanı aşağıdaki Adım 6.5'ten doldurulur. Varsayılan değer `gpt-image-2`; tek geçerli diğer değer `nano-banana-2`.

`characteristics` değerini satır başına bir `Anahtar: Değer` girişiyle tek bir string olarak yaz. Yalnızca doldurulan kimlik, yüz, saç, yapı ve görünüm alanlarını ekle. Boş kimlik alanları için değer icat etme. Kullanıcının boş bıraktığı giyim alanları Adım 3'teki varsayılanlara döner.

**characteristics.md**, aynı verinin okunabilir referans versiyonu:

```markdown
# <Karakter Adı>, Özellikler

## Kimlik
Yaş:
Cinsiyet:
Milliyet:

## Yüz
Cilt tonu:
Yüz şekli:
...

## Saç
Renk:
Stil:

## Yapı
Boy:
Vücut tipi:

## Giyim
Üst:
Alt:
Ayakkabı:
Aksesuar:

## Estetik
Ton:
```

---

## Adım 6.5, Görsel modeli seç

Kullanıcıya sor:

> Kadro için hangi görsel modeli kullanayım?
>
> **1. GPT Image 2** (önerilir). Yüksek kalite, fal.ai GPT Image 2 endpoint'inin 8,3 megapiksel sınırı ve 16 piksel çarpan kısıtı dahilindeki en büyük 3:4 boyutu olan 2400x3200 image_size. Şu an mevcut en iyi görsel üretim modeli. Ürün detayı, metin rendering, yüz tutarlılığı ve karmaşık promptlarda Nano Banana 2 ve Nano Banana Pro'dan üstün.
> **2. Nano Banana 2.** Üretim başı maliyeti düşük tutmak isteyen kullanıcılar için daha ucuz alternatif. Tercih sebebi yalnızca fiyat; GPT Image 2 tüm kalite eksenlerinde kazanır.
>
> `1`, `2` veya GPT Image 2 için `varsayılan` yazın.

Cevabı `$MODEL` olarak yakala. Adım 7'den önce her karakterin `character-spec.json` dosyasındaki `model` alanına değeri (`gpt-image-2` veya `nano-banana-2`) yaz.

---

## Adım 7, Üretim yolunu seç

Tüm spec dosyaları kaydedildikten sonra kullanıcıya hangi yolu kullanacağını sor. Higgsfield aboneliği olan kullanıcılara Yol B'yi öner; üretim başı muhasebe gerektirmez. Aboneliği olmayan kullanıcılar için Yol C sonraki en iyi seçimdir.

Bu mesajı gönder:

> N karakter `$MODEL` ile üretilmeye hazır. Görselleri gerçekte nasıl üretmek istersiniz?
>
> **A. Manuel yapıştırma.** Ücretsiz. Karakter başına iki promptu kopyalayın, seçtiğiniz modelin web arayüzüne kendiniz yapıştırın, çıktıları kaydedin.
> **B. Higgsfield MCP.** Higgsfield aboneliği olan kullanıcılar için en iyisi. GPT Image 2 ve Nano Banana 2 için çalışır. `/mcp` üzerinden ilk kullanımda tek seferlik OAuth girişi gerekir. Higgsfield kredilerinizi kullanır.
> **C. Fal.ai sonuç başı ödeme.** Abonelik gerekmez. Üretim başı ödeme. `fal_api_key` gerektirir. GPT Image 2 yüksek kalitede karakter başına yaklaşık 0,30 dolar, Nano Banana 2'de karakter başına yaklaşık 0,24 dolar.
> **D. Playwright ile web arayüzü otomasyonu.** B veya C'den yavaş, Higgsfield veya fal kredisi gerekmez. GPT Image 2 için chatgpt.com'u, Nano Banana 2 için aistudio.google.com'u kullanır.
>
> A, B, C veya D yazın.

Açık seçim bekle. Ardından yalnızca o yolu çalıştır. Aynı karakter için asla iki yolu paralel çalıştırma.

---

### Yol A, Manuel yapıştırma

Kullanıcı A'yı seçerse hiçbir şey otomatikleştirme. Her karakter için kullanıcının kopyalayabileceği iki net etiketlenmiş prompt yazdır. Aşağıdaki vesikalık ve tam boy promptları spec'ten her karakter için `{characteristics}` ve `{clothing}` yerleştirerek yaz.

**`$MODEL` `gpt-image-2` ise**, kullanıcıya şunu söyle:

> Her karakter için bu iki adımı sırayla yapın:
>
> 1. https://chatgpt.com/ adresini açın ve görsel üretici ile yeni bir sohbet başlatın. Modeli yüksek kaliteli GPT Image 2 olarak ayarlayın.
> 2. Karakter 1 için **vesikalık promptu** yapıştırın. Mevcut en büyük 3:4 boyutunda üretin. Görseli `$RFLAB/11_Characters/<karakter-1-adı>/` dizinine `headshot.png` olarak kaydedin.
> 3. Karakter 1 için **tam boy promptu** yapıştırın. Kaydedilen `headshot.png`'i görsel referans olarak yükleyin. Üretin. Aynı klasöre `fullbody.png` olarak kaydedin.
> 4. Her sonraki karakter için tekrarlayın. Tam boy her zaman aynı karakterin vesikalığına yüz referansı olarak ihtiyaç duyar.

**`$MODEL` `nano-banana-2` ise**, kullanıcıya şunu söyle:

> Her karakter için bu iki adımı sırayla yapın:
>
> 1. https://aistudio.google.com/ adresini açın ve Gemini 3.1 Flash Image'ı seçin.
> 2. Karakter 1 için **vesikalık promptu** yapıştırın. 3:4 2K'da üretin. Görseli `$RFLAB/11_Characters/<karakter-1-adı>/` dizinine `headshot.png` olarak kaydedin.
> 3. Karakter 1 için **tam boy promptu** yapıştırın. Kaydedilen `headshot.png`'i görsel referans olarak yükleyin. Üretin. Aynı klasöre `fullbody.png` olarak kaydedin.
> 4. Her sonraki karakter için tekrarlayın. Tam boy her zaman aynı karakterin vesikalığına yüz referansı olarak ihtiyaç duyar.

Bu dosyanın sonundaki Promptlar bölümündeki şablonları kullanarak promptları yazdır.

Kullanıcı tüm karakterlerin kaydedildiğini onayladığında tamamlanmayı onayla.

---

### Yol B, Higgsfield MCP

Yol B, karakter kadrosunu doğrudan Claude Code içinde Higgsfield CLI aracılığıyla üretir. Higgsfield aboneliği olan kullanıcılar için en iyisi. Kullanıcıya görünen etiket `Yol B, Higgsfield MCP` olarak kalır; deneyim kullanıcı tarafında değişmez (aynı krediler, aynı modeller, aynı Higgsfield hesabı). GPT Image 2 ve Nano Banana 2 için çalışır.

`../_shared/path-b-cli-implementation.md` dosyasını yükle ve oradaki B.0'dan B.9'a kadar olan adımları izle. Beceriye özgü değişkenler:

- `{{SKILL_SLUG}}`: `character`
- `{{MODEL_ID}}`: spec'in `model` alanı `gpt-image-2` ise `gpt_image_2`, `nano-banana-2` ise `nano_banana_flash`
- `{{ASPECT}}`: `3:4` (her karakter için sabit, portre)
- `{{QUALITY}}`: `high` (GPT Image 2 için)
- `{{RESOLUTION}}`: GPT Image 2 için `4k`, Nano Banana 2 için `2k`
- `{{OUTPUT_DIR}}`: `$RFLAB/11_Characters/<karakter-adı>` (karakter başına alt klasör)
- `{{OUTPUT_FILENAME}}`: karakter başına ilk üretim için `headshot.png`, ikincisi için `fullbody.png`

**Katı kural, karakter başına sıralı.** Her karakter kesin sırayla iki üretim gerektirir. Vesikalık önce üretilir, referans görsel olmadan (metin'den görsel). Tam boy ikinci üretilir; yüz tutarlılığı için az önce kaydedilen `headshot.png`'i yerel `--image` referansı olarak kullanır. Farklı karakterler paralel çalışabilir ama tek bir karakter içinde sıra sabittir.

**Onay özeti ifadesi (B.5).**

> Kadro: N karakter, her birinde 2 görsel, toplam N çarpı 2 üretim.
> Üretim başı maliyet: <B.4'ten kredi>
> Toplam: <N çarpı 2 çarpı üretim başı> kredi.
> Mevcut bakiye: <B.3'ten kredi>
>
> Devam etmek için `evet` onaylayın.

**Karakter başına üretim akışı (B.7, paylaşılan dokümandaki tek görsel şablonun yerini alır).** Kadrodaki her karakter için sırayla:

1. O karakter için `character-spec.json`'ı oku. Bu dosyanın sonundaki vesikalık şablonuna `{characteristics}` ve `{clothing}` yerleştirerek vesikalık promptu oluştur. Paylaşılan B.7'de belgelendiği şekilde doldurulmuş promptu geçici bir dosyaya yaz.
2. Üret komutunu `--image` bayrağı olmadan çalıştır (metin'den görsel):
   ```
   "$HIGGS_BIN" generate create gpt_image_2 \
     --prompt "$(cat /tmp/character-headshot-<ad>-$$.txt)" \
     --aspect_ratio "3:4" \
     --quality "high" \
     --resolution "4k" \
     --wait --wait-timeout 5m --json \
     > /tmp/character-headshot-<ad>-result-$$.json
   ```
3. Sonucu paylaşılan B.8'deki gibi çözümle. Dönen `result_url`'i `$RFLAB/11_Characters/<karakter-adı>/headshot.png` olarak indir.
4. Bu dosyanın sonundaki tam boy şablonuna `{characteristics}` ve `{clothing}` yerleştirerek tam boy promptu oluştur. Geçici dosyaya yaz.
5. Üret komutunu yeni kaydedilen vesikalığı yerel `--image` referansı olarak kullanarak çalıştır:
   ```
   "$HIGGS_BIN" generate create gpt_image_2 \
     --prompt "$(cat /tmp/character-fullbody-<ad>-$$.txt)" \
     --aspect_ratio "3:4" \
     --quality "high" \
     --resolution "4k" \
     --image "$RFLAB/11_Characters/<karakter-adı>/headshot.png" \
     --wait --wait-timeout 5m --json \
     > /tmp/character-fullbody-<ad>-result-$$.json
   ```
6. Paylaşılan B.8'deki gibi çözümle ve indir; `$RFLAB/11_Characters/<karakter-adı>/fullbody.png` olarak kaydet.
7. Kullanıcıya hangi karakterin tamamlandığını söyle, örn. "N içinde 1 bitti, sofia: headshot.png + fullbody.png kaydedildi."

Nano Banana 2 için model id'yi `nano_banana_flash` ve çözünürlüğü `2k` olarak değiştir. Diğer her şey aynı.

**Karakterler arası paralel toplu işler.** 3 veya daha fazla karakterlik kadrolarda karakter başına pipeline (vesikalık, ardından tam boy), Bash aracının `run_in_background` parametresi üzerinden karakterler arasında paralel çalışabilir. Her karakterin vesikalık+tam boy çifti kendi içinde kesinlikle sıralı kalır. 5'ten fazla karakteri paralel çalıştırma; bu Higgsfield çalışma alanı hız sınırını aşar.

**Herhangi bir karakter toplu iş ortasında başarısız olursa**, başarılı olanları kaydet, hatayı karakter adıyla birlikte göster ve yalnızca o karakteri yeniden denemek ya da atlayıp devam etmek isteyip istemediklerini sor.

**Son özet (B.9).**

> Toplu iş tamamlandı. N karakter üretildi, tümü `$RFLAB/11_Characters/<her-ad>/` dizinine kaydedildi.
> Son Higgsfield bakiyesi: <güncel `higgsfield account status` okuma>

Karakter başına `manifest.json` bu beceri için isteğe bağlıdır; karakter başına mevcut `character-spec.json` zaten promptu ve meta veriyi yakalar. Paylaşılan dokümanın manifest şeması yalnızca gelecekteki bir iş akışının tüm kadro genelinde tek bir toplamlı dosyaya ihtiyaç duyması durumunda gereklidir.

Eski MCP araç adları (`mcp__higgsfield__balance`, `mcp__higgsfield__generate_image` vb.) artık kullanılmıyor. CLI aynı Higgsfield hesabını, aynı kredileri ve aynı modelleri, `/mcp` ile Clerk yerine `higgsfield auth login` üzerinden OAuth akışını kullanarak sunar.

---

### Yol C, Fal.ai direkt API

Yol C, Fal endpoint'lerini doğrudan çağırmak için `fal-ai` MCP sunucusunu kullanır. Sonuç başı ödeme, abonelik gerekmez.

**Yol C.0, Ön çalışma kontrolü.** Başka bir şey yapmadan önce `fal-ai-prerun-check` koruma becerisini çalıştır. `fal_api_key`'in `pluginConfigs["reklam-fabrikasi"]` içinde ayarlı olduğunu ve fal-ai MCP'nin yanıt verdiğini doğrular. Kontrol başarısız olursa, koruma kullanıcıyı `/reklam-fabrikasi:setup-fal-ai`'ye yönlendiren net bir mesaj döndürür. Koruma başarısız olursa devam etme.

**Yol C.1, Maliyet onayı.** Kullanıcıya spec'in `model` alanından alınan değerlerle söyle:

> `$MODEL` için Yol C maliyeti:
> - Yüksek kalitede GPT Image 2: görsel başı yaklaşık 0,15 dolar, karakter başına yaklaşık 0,30 dolar, N karakter için toplam yaklaşık 0,30 çarpı N dolar.
> - 2K'da Nano Banana 2: görsel başı yaklaşık 0,12 dolar, karakter başına yaklaşık 0,24 dolar, N karakter için toplam yaklaşık 0,24 çarpı N dolar.
>
> Devam etmek için `evet` onaylayın.

Açık `evet` bekle.

**Yol C.2, Karakter karakter üret.**

Kadrodaki her karakter için sırayla:

1. `character-spec.json`'ı oku. `{characteristics}` ve `{clothing}` yerleştirerek vesikalık promptu oluştur.

2. **`model` `gpt-image-2` ise**, `mcp__fal-ai__run_model`'ı şu parametrelerle çağır:
   - `model`: `"openai/gpt-image-2"`
   - `prompt`: doldurulmuş vesikalık promptu
   - `image_size`: `{"width": 2400, "height": 3200}`
   - `quality`: `"high"`
   - `num_images`: 1
   - `output_format`: `"png"`
   (`safety_tolerance` ekleme. Endpoint reddeder.)

   **`model` `nano-banana-2` ise**, `mcp__fal-ai__run_model`'ı şu parametrelerle çağır:
   - `model`: `"fal-ai/nano-banana-2"`
   - `prompt`: doldurulmuş vesikalık promptu
   - `aspect_ratio`: `"3:4"`
   - `resolution`: `"2K"`
   - `num_images`: 1
   - `output_format`: `"png"`
   - `safety_tolerance`: `"4"`

3. Yanıt döndüğünde görsel URL'yi `$HEADSHOT_URL` olarak yakala. İndir ve `$RFLAB/11_Characters/<karakter-adı>/headshot.png` olarak kaydet.

4. `{characteristics}` ve `{clothing}` yerleştirerek tam boy promptu oluştur.

5. **`model` `gpt-image-2` ise**, `mcp__fal-ai__run_model`'ı şu parametrelerle çağır:
   - `model`: `"openai/gpt-image-2/edit"`
   - `prompt`: doldurulmuş tam boy promptu
   - `image_urls`: `[$HEADSHOT_URL]`
   - `image_size`: `{"width": 2400, "height": 3200}`
   - `quality`: `"high"`
   - `num_images`: 1
   - `output_format`: `"png"`
   (`safety_tolerance` ekleme.)

   **`model` `nano-banana-2` ise**, `mcp__fal-ai__run_model`'ı şu parametrelerle çağır:
   - `model`: `"fal-ai/nano-banana-2/edit"`
   - `prompt`: doldurulmuş tam boy promptu
   - `image_urls`: `[$HEADSHOT_URL]`
   - `aspect_ratio`: `"3:4"`
   - `resolution`: `"2K"`
   - `num_images`: 1
   - `output_format`: `"png"`
   - `safety_tolerance`: `"4"`

6. İndir ve `$RFLAB/11_Characters/<karakter-adı>/fullbody.png` olarak kaydet.
7. Kullanıcıya söyle: "N içinde <i> bitti, <karakter-adı>: headshot.png + fullbody.png kaydedildi."

Herhangi bir üretim toplu iş ortasında başarısız olursa, başarılı olanları kaydet, hatayı karakter adıyla birlikte göster ve yalnızca o karakteri yeniden denemek ya da atlayıp devam etmek isteyip istemediklerini sor.

**Yol C.3, Son özet.**

> Toplu iş tamamlandı. `$MODEL` ile N karakter üretildi, tümü `$RFLAB/11_Characters/<her-ad>/` dizinine kaydedildi.

---

### Yol D, Playwright web arayüzü

Yol D, seçilen modelin web arayüzünü gerçek bir tarayıcıda kullanmak için Playwright MCP'yi kullanır. B veya C'den yavaş, fal veya Higgsfield kredisi gerekmez. Üretim başı sıfır maliyet isteyen kullanıcılar için kullanışlı.

`gpt-image-2` için Yol D `https://chatgpt.com/` ve GPT Image 2 görsel üreticiyi kullanır. `nano-banana-2` için Yol D, Gemini 3.1 Flash Image seçili şekilde `https://aistudio.google.com/`'ı kullanır.

**Katı kurallar:**

1. **Otomatik yükleme yapma.** Her dosya yüklemesi için açık kullanıcı onayı gerekir.
2. **`evet` olmadan Üret'e tıklama.** Prompt yapıştırıldıktan sonra bile kullanıcının "devam" demesini bekle.
3. **Karakter karakter.** Tarayıcı oturumu aynı anda yalnızca bir üretim çalıştırabilir. Paralelleştirme deneme.

**Yol D.1, İlk kullanım kontrolü.** `mcp__playwright__*` araçlarını ara. Hiçbiri yoksa Playwright MCP bağlı değil. Dur ve kullanıcıya şunu söyle: "Playwright MCP bağlı değil. Playwright Chromium'u kurmak ve yeniden yüklemek için `/setup` çalıştırın, ardından bu beceriyi yeniden çalıştırın."

**Yol D.2, Model arayüzünü aç.** Spec'in `model` alanı için doğru URL'ye gitmek üzere `mcp__playwright__browser_navigate` kullan:
- `gpt-image-2`: https://chatgpt.com/ adresine git, kullanıcının ChatGPT'ye giriş yaptığını ve yüksek kaliteli GPT Image 2'nin seçili olduğunu onayla.
- `nano-banana-2`: https://aistudio.google.com/ adresine git, kullanıcının Google'a giriş yaptığını onayla ve Gemini 3.1 Flash Image'ı seç.

Kullanıcı giriş yapmamışsa dur ve manuel giriş yapmalarını iste, ardından devam et.

**Yol D.3, Her karakter için sırayla:**

1. Kullanıcıya onayla: "N içinde karakter <i>'ye başlamak üzereyim: <karakter-adı>. Devam edilsin mi? (evet / atla / dur)"
2. `evet`te vesikalık promptu modelin girişine yapıştır. Kullanıcıya onayla: "<karakter-adı> için vesikalık promptu yapıştırıldı. Üret'e tıklansın mı? (evet / hayır)"
3. `evet`te Üret'e tıkla. Görsel render olana kadar bekle. Sonucu Playwright MCP dosya indirme aracı ile `$RFLAB/11_Characters/<karakter-adı>/headshot.png` dizinine kaydet.
4. Onayla: "headshot.png kaydedildi. Şimdi tam boy promptunu yapıştırıp vesikalığı referans olarak ekleyeceğim. Devam edilsin mi? (evet / hayır)"
5. `evet`te tam boy promptunu yapıştır ve kaydedilen `headshot.png`'i görsel referans olarak ekle. Onayla: "Referanslı tam boy promptu yapıştırıldı. Üret'e tıklansın mı? (evet / hayır)"
6. `evet`te Üret'e tıkla. Bekle. `$RFLAB/11_Characters/<karakter-adı>/fullbody.png` dizinine indir.
7. Kullanıcıya söyle: "N içinde <i> bitti, <karakter-adı>: headshot.png + fullbody.png kaydedildi."

**Yol D.4, Son özet.**

> Toplu iş tamamlandı. N karakter üretildi, tümü `$RFLAB/11_Characters/<her-ad>/` dizinine kaydedildi.

---

## Adım 8, Sonuçları sun

Toplu iş tamamlandığında, hangi yol kullanılırsa kullanılsın sonuçları sun. Her karakterin klasör yolunu ve iki PNG dosyasını listele. Sor:

> Kadro yeterli mi? Yoksa herhangi bir karakteri yeniden üretmek, özellikleri ayarlamak veya daha fazla karakter eklemek ister misiniz?

Kullanıcının seçebileceği seçenekler:

- **Hepsi tamam.** Tamamlanmayı onayla. Flywheel'deki bir sonraki adımı öner, örn. "Bu karakterlerden birini ürününüzle birlikte görmek için `/reklam-fabrikasi:product-shot` çalıştırmak ister misiniz, yoksa aynı yüzü 6 video varyantına sabitlemek için `/reklam-fabrikasi:ugc-prompt` mu?"
- **Bir karakteri yeniden üret.** Hangi karakteri olduğunu sor, ardından yalnızca o karakteri aynı yoldan yeniden çalıştır. Çıktılar mevcut `headshot.png` ve `fullbody.png` dosyalarının üzerine yazar.
- **Bir karakteri ayarla.** Hangi karakteri ve hangi alanları değiştireceğini sor. Spec dosyalarını güncelle, ardından yalnızca o karakteri yeniden çalıştır.
- **Daha fazla karakter ekle.** Kaç tane daha olduğunu sor, ardından yalnızca yeni karakterler için Adım 3'e geri dön. Eklenen karakterlerin adları, Adım 4 ile aynı çakışma kuralı uygulanarak üretimden önce mevcut `11_Characters/` klasörüne karşı doğrulanmalıdır.

---

## Yineleme

**Aynı spec ile bir karakteri yeniden üret.** Yalnızca o karakter için aynı yolu yeniden çalıştır. `headshot.png` ve `fullbody.png` dosyalarının üzerine yazar.

**Özellikleri ayarla ve yeniden üret.** O karakter için `character-spec.json` ve `characteristics.md` dosyalarını güncelle, ardından yolu yeniden çalıştır. Tam boy vesikalığı yüz referansı olarak kullandığından her iki görsel de birlikte yeniden üretilmelidir; yeni bir vesikalık, eşleşmeyi korumak için yeni bir tam boy gerektirir.

**Tüm kadroyu yeniden üret.** Beceriyi yeniden çalıştır. Yeni çalıştırma mevcut klasörleri görecek ve üzerine yazılıp yazılmayacağını ya da yeni adlar seçilip seçilmeyeceğini soracak.

---

## Promptlar

İki prompt şablonu. Her karaktere göndermeden önce karakter başına `{characteristics}` ve `{clothing}` yerleştir. Prompt yapısını değiştirme.

### Vesikalık promptu

```
Clean front facing studio portrait. Figure looking straight into the lens.

Character: {characteristics}

Clothing: {clothing}

Facial features and skin texture: Clean natural skin, no makeup, no retouching. Natural skin captured at full detail, slightly visible pores, minimal freckling, minimal natural skin irregularities, realistic skin texture. Skin completely unedited, no smoothing, no corrections. Keep natural facial asymmetry intact. Groomed but natural brows and lashes. Minimal flyaway hairs. Subtle realistic under eye texture.

Pose and shot framing: Upright posture, head held straight. Tight vertical headshot framing, from just above the head down to the chin line. Eyes looking straight into the camera. Neutral facial expression, no smile. Neck straight and relaxed. Keep clothing out of the frame.

Light: Direct on camera flash, aimed straight at the model. Every skin detail clearly visible. Subtle specular highlights across the T zone. Minimal shadow behind the model, flat on the backdrop. No softbox or beauty lighting.

Camera specs: Full frame camera, 75 to 85mm lens, f/8 aperture. Full frame sharp, no blurring. 3:4 vertical format, minimal natural grain. 5750 to 5800K white balance, daylight neutral. No colour grading.

Environment: Clean pale grey background, no texture.
```

### Tam boy promptu

```
Full body studio shot. Face and full anatomical structure matched exactly to the reference image. Bone structure, body proportions and gender alignment preserved throughout.

Character: {characteristics}

Facial reference: Maintain exact face consistency with the reference image. Groomed but natural brows and lashes, minimal flyaway hairs, subtle realistic under eye texture. Skin completely unedited, slightly visible pores, minimal freckling, natural facial asymmetry intact. Matching the reference throughout.

Pose and framing: Full body visible, small gap at top and bottom. Upright relaxed stance, arms at sides, chest parallel to the lens. Eyes looking straight into the camera, neutral facial expression.

Clothing: {clothing}

Camera specs: Full frame camera, 75 to 85mm lens, f/8 aperture. Sharp from head to feet, no blurring. 3:4 vertical format, minimal natural grain. 5750 to 5800K white balance, daylight neutral. No colour grading.

Environment: Same pale grey background as the reference image, no texture.
```

---

## Katı kurallar

1. **Üretmeden önce her zaman kadroyu onayla.** Adım 5 toplu iş özeti zorunludur, istisna yok.
2. **Otomatik üretim yapma.** Her yol, ilk görsel ateşlenmeden önce kullanıcıdan açık `evet` gerektirir.
3. **Önce vesikalık, sonra tam boy, karakter başına.** O karakter için vesikalıktan önce tam boyu üretme. Tam boy, yüz tutarlılığı için vesikalık URL'sine referans olarak ihtiyaç duyar; aksi halde iki görsel arasındaki yüz tutarlılığı kaybolur.
4. **Kimlik veya yüz özelliklerini icat etme.** Manuel formda kimlik, yüz, saç, yapı veya görünüm alanı boşsa spec'te dışarıda bırak. Kategoriye özgü varsayılanlarla doldurma. Giyim alanları tek istisnadır; boş giyim alanları Adım 3'teki belgelenmiş varsayılanlara döner (beyaz tişört, mavi kot, beyaz spor ayakkabı).
5. **Tüm adları kısalt.** Küçük harf, tireler, boşluk veya özel karakter yok. Adım 4'te ve Adım 8'deki daha fazla karakter ekle bölümünde, yazmadan önce mevcut klasörlere karşı doğrula.
6. **Diskte karakter başına spec.** Herhangi bir görsel üretim çalışmadan önce hem `character-spec.json` hem de `characteristics.md` mevcut olmalıdır. Bunlar olmadan yeniden üretim ve ayarlama iş akışları bozulur.
7. **İzin almadan üzerine yazma.** Bir karakter klasörü zaten `headshot.png` veya `fullbody.png` içeriyorsa üzerine yazmadan önce sor.
8. **`openai/gpt-image-2` ve `openai/gpt-image-2/edit` endpoint'leri `safety_tolerance` kabul etmez.** Yalnızca Nano Banana ailesi kabul eder. Yol C bağlantısı her GPT Image 2 çağrısında `safety_tolerance`'ı atlamalıdır. Alan mevcut olursa endpoint isteği reddeder.
9. **Beceri çıktısında hiçbir yerde cümle duraklaması olarak tire veya kısa çizgi kullanma.** Virgül, "ve" kullan ya da cümleyi böl.

---

## Notlar

- Karakterler proje kapsamlıdır. Her proje klasörünün kendi `11_Characters/` alt klasörü vardır. Farklı markaların ayrı kadrolar tutması için Claude Code'u markaya özgü klasörde aç.
- Proje başına birden fazla karakter kabul edilebilir. Varsayılan kadro 5'tir, toplu iş başına üst sınır 10'dur. Daha sonra eklemek için beceriyi yeniden çalıştır.
- Karakterler aşağı akış becerilerini besler. Ürün çekimi becerisi, UGC prompt becerisi ve tekrar eden bir yüze ihtiyaç duyan gelecekteki içerik iş akışları burada kaydedilen vesikalık ve tam boya başvurur.
- Toplu iş ortasında Fal veya Higgsfield hatası neredeyse her zaman kimlik bilgisi katmanına işaret eder. Kesin hatayı ortaya çıkarmak için `/reklam-fabrikasi:doctor` çalıştır.
- Varsayılan model, yüksek kalitede ve 2400x3200 `image_size` ile GPT Image 2'dir. Bu, fal.ai GPT Image 2 endpoint'inin katı sınırlarına (max kenar 3840 px, max toplam 8.294.400 px, her iki boyut 16'nın katı) uyan en büyük 3:4 boyutudur. Nano Banana 2, 3:4 2K'da daha ucuz alternatif olarak kullanılabilir; tercih sebebi yalnızca fiyat.
- Higgsfield hem GPT Image 2 hem de Nano Banana 2'yi sunduğundan, hangi model seçilirse seçilsin Higgsfield aboneliği olan kullanıcılar için Yol B doğru seçimdir. Abonelik istemeyip üretim başı faturalandırmayı kabul eden kullanıcılar için Yol C doğru seçimdir.
