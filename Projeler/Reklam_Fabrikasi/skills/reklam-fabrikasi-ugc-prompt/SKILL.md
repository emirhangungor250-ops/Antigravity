---
name: reklam-fabrikasi-ugc-prompt
description: "Yazılı bir UGC reklam senaryosunu 6 üretime hazır Seedance 2.0 video promptuna dönüştürür ve isteğe bağlı olarak videoları üretir. /ugc-prompt, /seedance prompts, /generate ugc prompts, /higgsfield prompts, /fal ugc komutlarında veya 'UGC senaryomdan video promptu çıkar', 'bu senaryodan Seedance promptu yap', 'Higgsfield promptu oluştur', 'senaryomdan UGC videosu üret' gibi doğal dil isteklerinde tetiklenir. Kullanıcı /ugc sonrasında senaryoları video olarak istendiğinde de tetiklenir. Girdiler: UGC senaryosu, VOC belgesi, Marka DNA belgesi. Çıktı: her biri farklı hook arketipi ve farkındalık aşamasına sahip 6 prompt (gerçek A/B testi için). 11_Characters/ altında kayıtlı karakterler bulunan bir projede çalıştırıldığında, beceri kullanıcıdan tüm 6 video varyantında tek bir karakter seçmesini ister; böylece her video ücretli trafikte aynı kreatifte yüz eşleşmeli varyant gibi görünür. Promptlardan sonra dört yol: (A) kullanıcı Higgsfield'e kendisi yapıştırır, (B) Claude videoları resmi Higgsfield CLI üzerinden üretir (ilk kullanımda @higgsfield/cli kurar ve tarayıcı tabanlı cihaz girişi çalıştırır), (C) Higgsfield aboneliği yoksa Claude videoları fal.ai üzerinden video başına ücretle üretir, (D) Claude Playwright MCP ile Higgsfield arayüzünü tarayıcı üzerinden yönetir (eski Yol B). UGC senaryosunun video promptuna veya videoya dönüştürülmesi gerektiğinde DAIMA bu beceriyi kullan, satır içi prompt yazma."
---

# Reklam Fabrikası UGC Prompt Üretici

Yazılı bir UGC senaryosunu 6 üretime hazır Seedance 2.0 video promptuna dönüştürür. Her prompt 15 saniyeye sıkıştırılmış, farklı bir hook arketipi kullanıyor ve kullanıcının marka sesi ile müşteri diline dayanıyor.

Bu beceri, `/ugc` (konuşma metni yazan) ile gerçek video arasındaki köprüdür. /ugc senaryoları genellikle 30 ila 60 saniyelik konuşmadır; Seedance en fazla 15 saniyeyle sınırlıdır. Buradaki iş iki yönlüdür: senaryoyu yoğunlaştırmak ve Seedance'ın akıcı düzyazı prompt formatına uyarlamak.

Promptlar yazıldıktan sonra kullanıcının gerçek videoya giden dört yolu vardır:

1. **Yol A, Higgsfield'e manuel yapıştırma.** Promptları ücretsiz kopyala. Higgsfield AI'ya kendin yapıştır, karakter ve ürün görselini yükle, üret.
2. **Yol B, Higgsfield MCP.** Claude videoları resmi Higgsfield MCP sunucusu üzerinden üretir. Higgsfield aboneliğin varsa en iyi seçenek. İlk kullanımda `/mcp` ile tek seferlik OAuth girişi, yapıştırılacak anahtar yok.
3. **Yol C, fal.ai video başına ödeme.** Abonelik gerekmez. Higgsfield aboneliği olmayan veya istemeyenler için Claude, fal'ın `bytedance/seedance-2.0/reference-to-video` modeline karşı video başına ödeme ile üretir.
4. **Yol D, Playwright ile Higgsfield web arayüzü otomasyonu.** Eski sürümlerde Yol B'ydi. Claude, Higgsfield'i tarayıcıda açar ve arayüzü senin için yönetir. Yol B'den daha yavaştır ama Higgsfield MCP bağlı değilse kullanışlıdır.

---

## Adım 0.5, Proje çıktı klasörünü belirle

Çıktılar, Claude Code'un açık olduğu çalışma klasörüne kaydedilir. Girdileri toplamadan önce bu Bash bloğunu çalıştır:

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
  mkdir -p "$TARGET/05_UGC/prompts" "$TARGET/05_UGC/videos/path_b_outputs" "$TARGET/_meta"
  echo "READY:$TARGET"
fi

# Marka klasörü varsa ve dosya eksikse marka belleğini (CLAUDE.md) başlat.
# Yapacak bir şey olmadığında sessizce ve tekrar çalıştırılabilir biçimde çalışır.
if [ -d "$TARGET" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" ]; then
  bash "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi
```

- `PROTECTED:<path>`: reddet ve kullanıcıya Claude Code'u markaya özel bir alt klasörde açmasını söyle. Dur.
- `FIRSTRUN:<path>`: "Çıktıları `<path>/` konumuna kaydedeceğim. Bu klasöre ilk kez kaydediliyor, doğru mu? (evet/hayır)" diye sor. Evet'e klasörleri oluştur ve `<path>/_meta/folder-confirmed.flag` dosyasını yaz. Hayır'a dur.
- `READY:<path>`: sessizce devam et.

Çözümlenen yolu `$RFLAB` olarak kaydet. Ardından mevcut çalışmaları otomatik bul:

```
ls -t "$RFLAB/01_VOC_Research/"*.html "$RFLAB/01_VOC_Research/"*.md 2>/dev/null | head -n 1
ls -t "$RFLAB/02_Brand_DNA/"*.html "$RFLAB/02_Brand_DNA/"*.md 2>/dev/null | head -n 1
```

Son dosyalar varsa kullanıcıya şunu söyle: "Bu proje klasöründen VOC için `<voc-dosyası>` ve Marka DNA için `<bdna-dosyası>` kullanılıyor." İkisi de yoksa kullanıcıdan dosyaları yüklemesini iste.

## Adım 0.7, Marka karakterlerini kontrol et

UGC girdilerini toplamadan önce, `/reklam-fabrikasi:character` ile oluşturulmuş mevcut karakter klasörleri için `$RFLAB/11_Characters/` dizinini tara. Üç dal:

### Dal 1, bir veya daha fazla karakter mevcut

Karakterleri listele ve sor:

> Bu projede N karakter görüyorum (<virgülle ayrılmış isimler>). Tüm 6 video varyantında oyuncu olarak birini kullanmak ister misin? Aynı yüz, her videonun Meta'da aynı kreatifte yüz eşleşmeli varyant gibi görünmesini sağlar; bu da ücretli trafik için doğru yapıdır. Bir karakter adı yaz ya da modelin her video için yeni yüz üretmesini istiyorsan `atla` yaz.

Kullanıcı karakter adıyla yanıt verirse şunları kaydet:
- `$CHARACTER_NAME`: slug
- `$CHARACTER_REF`: `$RFLAB/11_Characters/<ad>/fullbody.png` mutlak yolu

`atla` yanıtı gelirse `$CHARACTER_REF` boş bırak.

### Dal 2, karakter yok ama Marka DNA mevcut

`$RFLAB/11_Characters/` boşsa veya yoksa ama `$RFLAB/02_Brand_DNA/` altında son dosya varsa şunu söyle:

> Bu projede henüz karakter yok. Ücretli trafik için önce `/reklam-fabrikasi:character` çalıştırarak marka kadrosu oluşturmak önerilir; böylece tüm 6 video varyantı aynı yüzü paylaşır. Seçenekler:
>
> A. Dur, önce `/reklam-fabrikasi:character` çalıştır, sonra bu beceriyi yeniden çalıştır.
> B. Atla ve modelin her video için yeni yüz üretmesine izin ver.
>
> A veya B yaz.

`A` gelirse beceriyi durdur ve kullanıcıya `/reklam-fabrikasi:character` çalıştırmasını söyle. `B` gelirse `$CHARACTER_REF` boş bırakarak devam et.

### Dal 3, ne karakter ne Marka DNA var

Tek satır notla devam et:

> Bu projede karakter yok. Yüz tutarlılığının önemli olduğu ücretli trafik için önce `/reklam-fabrikasi:brand-dna` sonra `/reklam-fabrikasi:character` çalıştırmayı düşün.

`$CHARACTER_REF` boş bırak.

### Sonraki adımlara etkisi

`$CHARACTER_REF` ayarlıysa:
- Yol B.6, Yol C yükleme adımı ve Yol D yükleme adımı karakter referans görseli olarak `$CHARACTER_REF` kullanır. Kullanıcıdan ayrı karakter dosyası yüklemesi istenmez.
- Yol B, C veya D'ye gönderilen her üretim promptunun başına tam olarak şu satır eklenir: `The person in this video must exactly match the reference image, face, hair, body, clothing.` Kaydedilen seedance promptları belgesi değişmez; önek yalnızca üretim sırasında uygulanır.

`$CHARACTER_REF` boşsa beceri tamamen önceki gibi davranır. Önek yok, tam boy referans eklenmez; kullanıcı orijinal akışa göre karakter dosyası sağlar (veya atlar).

## Adım 1, Girdileri topla

Kullanıcıya tam olarak şu mesajı gönder:

> **UGC Prompt Üretici kurulumu**
>
> UGC senaryondan Higgsfield AI için 6 farklı Seedance 2.0 video promptu üreteceğim. Her prompt farklı bir hook açısı kullanır; böylece hangi stilin izleyicinden tepki aldığını A/B testi ile ölçebilirsin.
>
> **Zorunlu:**
> 1. **UGC senaryosu,** `/ugc` çıktısı (veya herhangi bir yazılı UGC senaryosu). Yükle, yapıştır ya da dosyayı göster.
> 2. **VOC araştırma belgesi,** müşteri dil kalıpları için. Yükle ya da dosyayı göster.
> 3. **Marka DNA belgesi,** ton, ses, yapılacaklar ve yapılmayacaklar için.
>
> **İsteğe bağlı ama önerilen (Higgsfield'in görselleri kilitlemesine yardımcı olur):**
> 4. **Karakter görseli VEYA karakter videosu,** içerik üreticisinin görünüşünü kilitler. Video ise en fazla 15s.
> 5. **Ürün görseli VEYA ürün videosu,** ürünün görünüşünü kilitler. Video ise en fazla 15s.
> 6. **Ses klibi,** en fazla 15s. Yüklersen üretilen videolarda bu ses kullanılır.
>
> **Bir kerelik bilmen gereken matematik:** karakter videosu VE ses klibi yüklersen, toplam süreleri 15 saniyeyi geçemez. 5s karakter videosu demek en fazla 10s ses demektir. Herhangi bir işlem yapmadan önce bunu kontrol ederim.
>
> **Promptlar yazıldıktan sonra üç seçeneğin var:**
> - Promptları Higgsfield'e kendin yapıştır, karakter ve ürün görselini yükle, üret.
> - Playwright MCP aracılığıyla tarayıcı otomasyonuyla Higgsfield arayüzünü senin için yöneteyim.
> - Higgsfield aboneliğin yok mu? fal.ai MCP'yi kurayım ve videoları doğrudan API çağrılarıyla üreteyim; aylık abonelik gerekmez, video başına ödeme.
>
> Şimdi karar vermene gerek yok; promptlar yazıldıktan sonra hangi yolu istediğini sorarım.
>
> **Önemli:** Medya dosyalarını hiçbir zaman otomatik olarak yüklemem. Otomatik üretimi seçsen bile, her dosya yüklemesi ve her "üret" adımı için açık onayın gerekir.

Kullanıcının zorunlu belgeleri sağlamasını bekle. İsteğe bağlı yüklemeleri atlarsa sorun yok; Seedance yine de iyi çıktı üretebilir, sadece görseller belirli bir karakter/ürün görünümüne kilitlenmez.

### Girdi matematik doğrulaması

Kullanıcı hem **karakter videosu** hem de **ses klibi** yüklerse, devam etmeden önce şu kontrolü çalıştır:

```
character_video_seconds + voice_clip_seconds <= 15
```

15'i geçerlerse kullanıcıya tam sayıları söyle ve birini kısaltmasını iste. Devam etme.

Ürün videosu bu bütçeyi paylaşmaz; ayrı bir görsel referanstır. Ancak bağımsız olarak 15 saniyeyle sınırlıdır.

---

## Adım 2, Tüm referans dosyaları oku

Herhangi bir prompt yazmadan önce şu üç dosyayı tamamen oku:

| Dosya | Neden |
|---|---|
| `references/seedance-2-capabilities.md` | Platform özellikleri: çok çekimli sözdizimi, diyalog kuralları, tutarlılık kuralları, negatif prompt zorunluluğu |
| `references/ugc-prompt-examples.md` | Tam yazılmış 7 örnek prompt. Beceri çıktısının stil açısından eşleşmesi gereken altın standart |
| `references/Hook_Archetype_Guide.md` | Farkındalık aşamalarına eşlenmiş 8 hook arketipi ve standart 6 promptluk karışım |

Ardından kullanıcının üç belgesini oku:
- UGC senaryosu (hook satırları, diyalog, yapı için tara)
- VOC belgesi (dil kalıpları, acı ifadeleri, kimlik dili için tara)
- Marka DNA belgesi (ton, ses, yapılacaklar ve yapılmayacaklar için kullan)

---

## Adım 3, Tanımlayıcıları kilitle

Herhangi bir prompt yazmadan önce bu dizeleri kilitle. Her prompta **birebir** girerler; eş anlamlı kelime kullanma, başka bir ifadeyle yazma, promptlar arasında "geliştirme". Seedance'ın tutarlılık kuralı buna bağlıdır.

### Karakter tanımlayıcısı
İçerik üreticisini tanımlayan bir cümle yaz. Karakter görseli yüklendiyse görseldekini tanımla. Yoksa UGC senaryosu ve VOC'dan çıkar.

Örnek: "omuz hizasında kahverengi saçlı, krem rengi örgü kazak giyen, makyajsız, doğal görünümlü yirmi ortalarında genç bir kadın"

### Ürün tanımlayıcısı
Ürünü tanımlayan bir cümle yaz. Ürün görseli yüklendiyse onu tanımla. Yoksa senaryodan ve kullanıcının sağladığı ürün bağlamından çıkar.

Örnek: "AURA Tumbler 40oz, mat adaçayı yeşili paslanmaz çelik gövde, yerleşik pipetli beyaz vidalı kapak, kavisli siyah sap, önde kabartma AURA logosu"

### Işık ifadesi
Niş için uygun bir ışık ifadesi seç. Tüm 6 promptta birebir kullan.

Örnekler:
- "pencereden gelen yumuşak doğal gün ışığı"
- "şeffaf perdelerden geçen sıcak altın saat ışığı"
- "temiz beyaz yüzeyde parlak tepeden gün ışığı"
- "sıcak yan lambası olan loş yatak odası ışığı"

Bu üç kilitli dize tutarlılık çapasıdır. 6 prompt ortam, eylem, hook ve diyalog açısından değişir; ancak karakter, ürün ve ışık 6 promptta aynı çekimden geliyormuş gibi hissettirir.

---

## Adım 4, 6 hook arketipi seç

8 arketype için `references/Hook_Archetype_Guide.md` dosyasını oku. 6 prompt için varsayılan karışım:

| Prompt # | Arketip | Farkındalık | Format |
|---|---|---|---|
| 1 | Görsel açılış | farkında değil - problemi fark ediyor | ön kamera yakın çekim |
| 2 | Gerçek tepki | farkında değil | ön kamera, sürpriz |
| 3 | Problemi bilen serzenişi | problemi biliyor | orta çekim konuşma |
| 4 | Duyusal yakın çekim | çözümü biliyor | aşırı yakın çekim |
| 5 | Demo / kanıt | ürünü biliyor | arka kamera, hareket halinde ürün |
| 6 | Doğrudan iddia | en bilinçli | ön kamera, sakin inanç |

Ürün türü bunlardan birine uymuyorsa karışımı ayarla (örn. dijital ürün için "Demo / kanıt" yerine "Kutu açma veya keşif" koy). 6 prompt arasında her zaman en az 4 farklı farkındalık aşamasını kapsa.

### Birebir hook politikası

Her prompt için UGC senaryosunun hooklarına bak. Bir hook satırı:
1. Marka DNA belgesindeki marka sesiyle eşleşiyorsa
2. Gerçek konuşma gibi geliyorsa (kısaltmalar, yarım cümleler, ünlemler)
3. O prompt slotunun arketipiyle doğal uyum sağlıyorsa
4. Müşteri dilini kullanıyorsa (jargon veya reklam metni değil)

o zaman o promptun diyaloguna **birebir** gir. Yeniden yazma. Onaylanmış UGC senaryosundan alınan birebir hooklar, yeni üretilenlerden daha yüksek sinyaldir.

Senaryodaki hiçbir hook uymayan promptlar için VOC dili ve Marka DNA tonu kullanarak doğru arketipte yeni bir hook üret.

---

## Adım 5, Her promptu yaz

Her prompt şu yapıyı izler (`references/ugc-prompt-examples.md` formatıyla eşleşir):

```
## Prompt N, [Niş veya açı] ([süre]s)

[Format satırı: en-boy oranı, cihaz referansı, ışık, enerji, filtre yok]

[Ortam paragrafı: konum, birebir tanımlayıcılı karakter, birebir tanımlayıcılı ürün]

[Akıcı düzyazı olarak eylem ve diyalog: "arka kameraya geçiyor", "telefonu yere koyuyor", "hızlı kesme" gibi eylem fiilleriyle çok çekim; sahne etiketi veya zaman damgası yok]

[Gerekirse son stil veya ses notu]

Negative prompt: no captions, no background music
```

### Her prompt için katı kurallar

1. **Maksimum 15 saniye süre,** önerilen 15. Başlıkta belirt.
2. **Kilitli karakter tanımlayıcısını** ortam paragrafında birebir kullan.
3. **Kilitli ürün tanımlayıcısını** ortam paragrafında birebir kullan.
4. **Kilitli ışık ifadesini** promptun bir yerinde birebir kullan.
5. **Negatif prompt satırıyla bitir:** `no captions, no background music`.
6. **Çift tırnak içindeki diyalog** Seedance'ın dudak senkronizasyonunu tetikler. Çift tırnak kullan, tek tırnak değil.
7. **Sahne etiketi yok (ne "Sahne 1:" ne "Kesme:")** Kesmeleri ima etmek için eylem fiilleri kullan.
8. **Prompt gövdesinde zaman damgası yok.** Seedance kesimleri 15 saniye zarfında otomatik olarak ayarlar.
9. **Kullanıcıya yönelik çıktıda cümle ayırıcı olarak em-dash veya tire kullanma.** Virgül, nokta veya satır sonu kullan.

### Sıkıştırma kuralı

/ugc senaryosu genellikle 30-60s konuşmadır. ~37 kelime diyaloğa sıkıştır (15s × 2.5 kelime/sn). En güçlü hook + bir destek satırı + kısa kapanış. Geri kalanı çok çekim temposuyla görseller taşır.

Tek bir promptun diyalogu 40 kelimeyi aşıyorsa destek satırını kes. Hook + kapanış yeterlidir.

---

## Adım 6, 6 promptu çıktı olarak ver

6 promptu Adım 0.5'te belirlenen proje klasörü altında tek bir dosyaya kaydet:

```
$RFLAB/05_UGC/prompts/<niche-slug>/seedance-prompts-<YYYY-MM-DD>.md
```

Yoksa `$RFLAB/05_UGC/prompts/<niche-slug>/` oluştur. Niş alt dizini uygulanamıyorsa şuna geri dön:
```
$RFLAB/05_UGC/prompts/seedance-prompts-<YYYY-MM-DD>-<niche-slug>.md
```

Kullanıcıya onaylarken mutlak yolu yaz (`$RFLAB` yerine gerçek çözümlenen yolu koy).

Dosya başlığı şunları içermeli:
- Marka / niş adı
- Tarih
- Kaynak (UGC senaryosu referansı)
- Kilitli karakter tanımlayıcısı (kullanıcı başka yere kopyalayabilsin diye)
- Kilitli ürün tanımlayıcısı
- Kilitli ışık ifadesi
- Numaralı sırayla 6 prompt

Yazdıktan sonra dosya yolunu sun ve kullanıcının hangi üretim yolunu istediğini sor. Tam olarak şu ifadeyi kullan:

> 6 Seedance 2.0 promptu hazır: `<yol>`
>
> Her biri farklı bir hook arketipi kullanıyor (görsel açılış, tepki, serzeniş, duyusal, demo, iddia) yani 6 farklı reklam olarak okunuyorlar, tek bir reklamın 6 varyantı değil.
>
> **Bu videoları gerçeğe dönüştürmenin dört yolu:**
>
> **(A) Higgsfield'e manuel yapıştırma.** Ücretsiz. [Higgsfield AI](https://higgsfield.ai/ai/video)'ı aç, 1080p'de Seedance 2.0 seç, bir prompt yapıştır, karakter ve ürün görselini yükle, üret. Seedance 2.0 için Plus veya üstü abonelik gereklidir.
>
> **(B) Higgsfield MCP.** Higgsfield aboneliğin varsa en iyi seçenek. Her videoyu doğrudan Higgsfield'e çağırarak üretirim, sürmek için tarayıcı gerekmez. İlk kullanımda @higgsfield/cli kurulur ve tarayıcı tabanlı cihaz girişi yapılır, yapıştırılacak anahtar yok. Her zaman kredi bakiyeni ve prompt listesini gösteririm ve herhangi bir üretimden önce açık `evet` beklerim.
>
> **(C) Fal.ai sonuç başına ödeme.** Abonelik gerekmez. Higgsfield hesabı olmayan veya mevcut AI video aboneliği bulunmayan herkes için. fal'da aynı Seedance 2.0 modeline karşı video başına ödeme; fal fiyatlandırmasına göre birim başına yaklaşık 0,014 dolar (çalışma zamanında `get_pricing` ile doğrulanır). `fal_api_key` gerektirir.
>
> **(D) Playwright ile web arayüzü otomasyonu.** Eski sürümlerde Yol B'ydi. Higgsfield arayüzünde gezinirim, her promptu yapıştırırım, dosya yüklemenizi isterim ve yalnızca her adımda açık onayınla üret'e tıklarım. Yol B ile aynı Higgsfield aboneliği gereklidir.
>
> Hangi yolu seçiyorsun? **(A)**, **(B)**, **(C)**, yoksa **(D)**?

---

## Adım 7, İsteğe bağlı video üretimi

**Bu adıma yalnızca kullanıcı açıkça (B), (C) veya (D) seçerse gir.** (A) seçerlerse beceri tamamdır.

### Adım 7B, Higgsfield MCP

Yol B, UGC videolarını doğrudan Claude Code içindeki Higgsfield CLI üzerinden üretir. Higgsfield aboneliği olan kullanıcılar için en iyi yol. Kullanıcıya yönelik etiket `Yol B, Higgsfield MCP` olarak kalır çünkü kullanıcı tarafındaki deneyim değişmez; aynı krediler, aynı Seedance modeli, aynı Higgsfield hesabı.

`../_shared/path-b-cli-implementation.md` dosyasını yükle ve oradaki B.0'dan B.9'a kadar olan adımları izle. Beceriye özgü değişkenler:

- `{{SKILL_SLUG}}`: `ugc-prompt`
- `{{MODEL_ID}}`: Seedance 2.0 için `seedance_2_pro` (varsayılan). Seedance 2.0 Fast için `seedance_2_lite`. Paylaşılan belgenin Model ID eşleme bölümü ikisini de belgeler. CLI seçilen ID'yi reddederse `higgsfield model list` ile canlı ID'yi doğrula; Higgsfield sürümler arasında video model ID'lerini zaman zaman yeniden adlandırıyor.
- `{{ASPECT}}`: `9:16` (dikey UGC varsayılanı)
- `{{QUALITY}}`: atla, Seedance kalite bayrağı kabul etmez (CLI, video modeller için `--quality`'ı sessizce yok sayar). Paylaşılan belgenin yapısıyla tutarlılık için gerekirse `high` ver ama etkisi yoktur.
- `{{RESOLUTION}}`: `1080p` (Seedance şemasına göre, görüntü modellerinin kullandığı `4k`/`2k` dizelerinden farklı)
- `{{OUTPUT_DIR}}`: `$RFLAB/05_UGC/videos/path_b_outputs`
- `{{OUTPUT_FILENAME}}`: `video_<N>.mp4`; `<N>` kullanıcının alt kümesinden prompt numarası
- Referans varlıklar: `$CHARACTER_REF` Adım 0.7'den ayarlıysa önce karakter `fullbody.png`, sonra ürün görseli, kullanıcı yüklediyse ses klibi. Adım 1'den gelen girdi matematiğini uygula; `character_video_seconds + voice_clip_seconds` 15'i geçmemeli.

**Alt küme seçici (beceriye özgü, B.5 onay kapısının parçası olarak çalışır).** Kullanıcıya söyle:

> 6 video promptu hazır (prompt 1'den 6'ya). Hangilerini Higgsfield üzerinden üreteyim? Numaraları virgülle ayrılmış olarak yaz. Örnek: "1, 3, 5 üret". Ya da her promptu çalıştırmak için "hepsi" yaz.

Yanıtı bekle. `hepsi` veya virgülle ayrılmış sayısal liste kabul et. Belirsizse yeniden sor. Her sayının 1 ile 6 arasında (dahil) olduğunu doğrula. Tekrarları reddet.

**Onay özeti ifadesi (B.5).**

> Prompt numaraları <liste> kullanarak Higgsfield üzerinden K video üretmek üzereyim. Video başına maliyet: <B.4'ten krediler>. Toplam: <K çarpı üretim başına> kredi. Mevcut bakiye: <B.3'ten krediler>. Devam etmek için `evet` onayla.

**Karakter öneki (B.7).** Her prompt için generate komutu oluştururken, `$CHARACTER_REF` Adım 0.7'den ayarlıysa, prompt metnini geçici dosyaya yazmadan önce başına tam olarak şu satırı ekle: `The person in this video must exactly match the reference image, face, hair, body, clothing.` Kaydedilen seedance promptları belgesi değişmez; önek yalnızca üretim sırasında uygulanır. Paylaşılan belgenin B.7 adımı (promptu geçici dosyaya yaz, sonra `--prompt` argümanına `cat` ile besle) bunun dışında değişmez.

**Videoya özgü bayraklar (B.7).** Seedance, görüntü modellerinin kabul etmediği ek bayraklar kabul eder. Generate komutuna ekle:

- `--duration "15"` (maksimum 15 saniye, varsayılan olarak üst sınırda)
- `--generate_audio "true"` (diyaloğu dudak senkronizasyonuyla oluştur, varsayılan true)

Bu bayraklar `--aspect_ratio`, `--resolution` ve `--image` bayraklarının yanında geçirilir. Gelecekteki bir CLI sürümü bunları yeniden adlandırırsa `higgsfield model get seedance_2_pro --json` ile tam bayrak adlarını doğrula.

**Paralel toplu işler (B.7).** 3 veya daha fazla video için Bash aracının `run_in_background` parametresi aracılığıyla generate komutlarını paralel çalıştır. Video üretimi görüntü üretiminden daha yavaştır; Seedance 2.0 işi genellikle 60 ila 180 saniye sürer. 6 videonun paralel toplu işi sıralı 12 ila 18 dakikaya karşın yaklaşık 3 ila 5 dakika gerçek zamanda tamamlanır.

**Manifest (B.9).** Paylaşılan belgeden standart şema; her prompt numarası için `{{OUTPUT_DIR}}` ile `video_<N>.mp4` dosya adını birleştirerek oluşturulan `output_path`. Manifest üst düzeyine `media_type: "video"` alanı ekle; böylece aşağı akış araçları video Yol B çıktısını görüntü Yol B çıktısından ayırt edebilir.

Eski MCP araç adları (`mcp__higgsfield__balance`, `mcp__higgsfield__generate_video` vb.) artık kullanılmıyor. CLI, aynı Higgsfield hesabını, aynı kredileri ve aynı Seedance modelini sunar; OAuth akışı `/mcp` artı Clerk yerine `higgsfield auth login` tarafından yönetilir.

### Adım 7C, fal.ai MCP üzerinden API üretimi

Bu yol, fal.ai'nin `bytedance/seedance-2.0/reference-to-video` modelini doğrudan fal-ai MCP sunucusu üzerinden kullanır. Video başına ödeme, aylık abonelik yok, arayüzden daha hızlı.

#### Önce kapıyı kontrol et: fal-ai-prerun-check çalıştır

Herhangi bir Yol C çalışmasından önce `fal-ai-prerun-check` koruma becerisini çalıştır. `fal_api_key`'in `pluginConfigs["reklam-fabrikasi"]` içinde olduğunu ve fal-ai MCP'nin erişilebilir olduğunu doğrular. Koruma eksik veya geçersiz kimlik bilgileri bildirirse kullanıcıya `/reklam-fabrikasi:setup-fal-ai` çalıştırmasını söyleyerek dur. Korumayı atlatma.

Koruma geçtikten sonra devam et.

#### fal-ai MCP araçlarının görünür olduğunu doğrula

`mcp__fal-ai__` ile başlayan herhangi bir araç ara. Bulunursa aşağıdaki "Uçuş öncesi kontrol listesi"ne atla. Koruma geçtiğine rağmen bulunamazsa kullanıcıya MCP sunucusunun anahtarı alması için Claude Code'u yeniden yüklemesini (Mac'te Cmd+Q sonra yeniden aç) söyle, ardından yeniden çalıştır.

#### Uçuş öncesi kontrol listesi (zorunlu)

fal.ai üzerinden herhangi bir şey üretmeden önce:

1. **Promptlar onaylandı mı?** Kullanıcı 6 promptu okuyup onayladı mı?
2. **fal-ai MCP bağlı mı?** Araçların mevcut olduğunu doğruladın mı?
3. **Karakter görseli / videosu,** yerel dosya yolu? (fal yükleyebilmek için erişilebilir olması gerekir.)
4. **Ürün görseli / videosu,** aynı.
5. **Ses klibi** (uygulanabilirse), dosya yolu?
6. **Çözünürlük,** 1080p öner (fal model şemasına göre).
7. **Ses üret,** true mu false mu? Varsayılan true, maliyet her iki durumda aynı (fal belgelerine göre).
8. **6'nın kaçı,** tümü mü yoksa alt küme mi? Maliyet beklentisini doğrula: `~0,014 dolar × süre × adet` (doğrulamak için `mcp__fal-ai__get_pricing` çalıştır).

Kontrol listesi olarak yaz. Eksik bir şey varsa dur.

#### Dosya yükleme kuralı

**Dosyaları hiçbir zaman otomatik yükleme.** Kullanıcı Yol C'yi seçmiş olsa bile, her dosya yüklemesi açık onay gerektirir:

> `<yol>` dosyasını Seedance üretiminde kullanmak için fal.ai'ye yüklemek için hazır mısın? (Evet/hayır.)

Her yol için kullanıcı onayladıktan sonra yalnızca `mcp__fal-ai__upload_file` kullan.

#### Üretim akışı

Her onaylanan prompt için:

1. `bytedance/seedance-2.0/reference-to-video` için en güncel girdi şeklini aldığını doğrulamak üzere `mcp__fal-ai__get_model_schema` kullan
2. `$CHARACTER_REF` Adım 0.7'den ayarlıysa bir kez `mcp__fal-ai__upload_file` ile yükle ve URL'yi tüm promptlarda yeniden kullan. Kullanıcıya söyle: "`<karakter-adı>` fullbody.png karakter referansı olarak kullanılıyor." Karakter için dosya başına yükleme onayı isteme. `$CHARACTER_REF` boşsa kullanıcının sağladığı karakter görselini/videosunu `mcp__fal-ai__upload_file` ile yükle (açık kullanıcı onayı sonrası).
3. Ürün görselini/videosunu `mcp__fal-ai__upload_file` ile yükle (açık kullanıcı onayı sonrası)
4. Ses klibi varsa `mcp__fal-ai__upload_file` ile yükle (açık kullanıcı onayı sonrası)
5. Girdiyi oluştur. Yüklenen medyaya promptta fal şemasına göre `@Image1`, `@Video1`, `@Audio1` vb. olarak başvur. `$CHARACTER_REF` ayarlıysa `prompt` alanına göndermeden önce tam olarak şu satırı başa ekle: `The person in this video must exactly match the reference image, face, hair, body, clothing.`
6. Premium varsayılanlar: `resolution: 1080p`, `duration: "15"`, `generate_audio: true`, `aspect_ratio: 9:16` (dikey UGC).
7. Son kez onayla: "Prompt N çalıştırmak için hazır mısın? Tahmini maliyet ~X dolar."
8. Tek videolar için `mcp__fal-ai__run_model` (senkron) veya toplu çalışmalar için `mcp__fal-ai__submit_job` + `mcp__fal-ai__check_job` kullan.
9. Dönen video URL'sini kaydet. `$RFLAB/05_UGC/videos/<niche-slug>/prompt-N.mp4` konumuna indir. Yoksa `$RFLAB/05_UGC/videos/<niche-slug>/` oluştur. Niş alt dizini oluşturulamazsa `$RFLAB/05_UGC/videos/prompt-N-<niche-slug>.mp4` konumuna geri dön. Tüm video çıktısı, proje başına `$RFLAB` ağacının içinde kalır.
10. 2-6 arası promptlar için tekrarla (kullanıcı paralel istemediği sürece sıralı olarak).

#### fal.ai girdi eşleme hızlı referansı

| Prompt slotu | fal alanı | Notlar |
|---|---|---|
| Prompt gövdesi (paragraf) | `prompt` | Yüklemelere `@Image1` vb. olarak başvur |
| Karakter görseli/videosu | yükle sonra `image_urls` veya `video_urls`'e ekle | Maksimum 9 görsel, 3 video toplam |
| Ürün görseli/videosu | yükle sonra `image_urls` veya `video_urls`'e ekle | Aynı dizi |
| Ses klibi | yükle sonra `audio_urls`'e ekle | Maksimum 3 ses, ≤15s toplam |
| En-boy oranı | `aspect_ratio` | Dikey UGC için `"9:16"` |
| Çözünürlük | `resolution` | `"1080p"` |
| Süre | `duration` | `"15"` |
| Ses senkronizasyonu | `generate_audio` | Dudak senkronizasyonu için `true` |

Tüm modalitelerdeki toplam medya dosyaları **12'yi geçmemeli**. Ses klibi + karakter videosu toplamı 15 saniyeyi geçemez (Yol D ile aynı katı kural).

### Adım 7D, Playwright MCP ile Higgsfield'de tarayıcı otomasyonu

Bu, Higgsfield MCP eklenmeden önceki sürümlerde eski Yol B'ydi. Beceri `https://higgsfield.ai/ai/video` adresindeki Higgsfield arayüzünü yönetir. Kendin çalıştıracağın akışın aynısı; Claude sadece butonlara tıklar.

#### Uçuş öncesi kontrol listesi (zorunlu)

Tarayıcıyı açmadan önce kullanıcıyla onayla:

1. **Promptlar onaylandı mı?** 6 promptu okuyup onayladılar mı yoksa önce düzenleme mi istiyorlar?
2. **Higgsfield hesabı hazır mı?** Giriş yapmış mı? Plus abonelik veya üstü (Seedance 2.0 için gerekli)?
3. **Karakter görseli / videosu hazır mı?** Dosya yerel mi ve nerede?
4. **Ürün görseli / videosu hazır mı?** Aynı.
5. **Ses klibi hazır mı?** (uygulanabilirse)
6. **Hangi model varyantı:** Seedance 2.0 (tam kalite, daha yavaş, daha fazla kredi) veya Seedance 2.0 Fast (daha ucuz, test için)?
7. **Çözünürlük,** 1080p öner ama onayla.
8. **6'nın kaçı,** tümü mü yoksa alt küme mi?

Kontrol listesini liste olarak yaz ve kullanıcının her maddeyi onaylamasını bekle. **Eksik bir şey varsa dur ve söyle.** Eksik kurulumla devam etme.

#### Dosya yükleme kuralı (kritik)

**Medya dosyalarını hiçbir zaman otomatik yükleme.** Kullanıcı kabul ettikten sonra bile, her dosya yüklemesi ayrı ve açık bir "evet, karakter görselimi şimdi yükle" gerektirir. Tarayıcı otomasyonu yükleme butonuna gidebilir, tıklayabilir ve dosya seçiciyi açabilir; ancak gerçek dosya seçimi kullanıcının eylemi ya da yol belirtilmiş açık "devam et" olmalıdır.

Şu şekilde ifade et:

> Sayfa artık karakter görseli için dosya seçiciyi gösteriyor. `<yol>` dosyasını yükleyeyim mi? (Evet/hayır.)

Her dosya için açık onay bekle.

#### Üretim akışı

Kullanıcı her kontrol listesi maddesini onayladıysa VE her dosya için açık yükleme izni verdiyse:

1. `https://higgsfield.ai/ai/video` adresine gitmek için Playwright MCP kullan
2. Sayfanın yüklendiğini ve kullanıcının giriş yaptığını onayla (giriş istemi görünürse dur ve kullanıcıya söyle)
3. Seedance 2.0'ı (veya Fast) ve seçilen çözünürlüğü seç
4. Prompt 1'in tam gövdesini prompt alanına yapıştır. `$CHARACTER_REF` Adım 0.7'den ayarlıysa yapıştırmadan önce prompt gövdesinin başına tam olarak şu satırı ekle: `The person in this video must exactly match the reference image, face, hair, body, clothing.`
5. Karakter dosyasını yükle (açık kullanıcı onayıyla). `$CHARACTER_REF` ayarlıysa tek bir onaylamayla otomatik olarak o yolu kullan, örn. "Bu video için karakter referansı olarak `<karakter-adı>` fullbody.png kullanılsın mı? (evet / hayır)". Aksi halde kullanıcıdan karakter dosyası yolunu iste.
6. Ürün dosyasını yükle (açık kullanıcı onayıyla)
7. Varsa ses klibini yükle (açık kullanıcı onayıyla)
8. Son kez onayla: "Prompt 1 için üretimi başlatmak için hazır mısın?"
9. Yalnızca açık evet sonrası üret'e tıkla
10. Aynı `$CHARACTER_REF` ön ekini ve yükleme kuralını her prompta uygulayarak prompt 2-6 için sırayla tekrarla

### Herhangi bir üretim yolu için yasaklar

- Belirli bir prompt için açık "evet, şimdi üret" olmadan **asla** üret'e tıklama, `run_model` veya `generate_video` çağırma
- Kullanıcının ad ve yol olarak onaylamadığı bir dosyayı **asla** yükleme
- Kullanıcı adına hizmet şartları veya sözleşmeleri **asla** onaylamama
- Hesap ayarlarını, faturalandırmayı veya aboneliği **asla** değiştirme
- Kullanıcı söylemedikçe birden fazla üretimi paralel **asla** çalıştırmama (her üretim para harcar)
- Önceki promptun onayının bir sonraki promptu kapsadığını **asla** varsaymama; her birini ayrı onayla
- Higgsfield CLI kurulu değilse veya kullanıcı kimlik doğrulaması yapmamışsa Yol B üretimine **asla** devam etme; `../_shared/path-b-cli-implementation.md` adresindeki paylaşılan referans B.0 kurulumu ve B.1 cihaz akışı girişini yönetir, önce o adımları izle
- `mcp__fal-ai__*` araçları mevcut değilse Yol C üretimine **asla** devam etme; bunun yerine kurulum adımlarını uygula

---

## Her kuralın neden önemli olduğu

**Birebir tanımlayıcılar:** Seedance'ın video modeli, tanımlayıcı dizelerini görsel referans olarak kullanır. Prompt 1'de "mat adaçayı yeşili termos" ve prompt 2'de "zeytunî renkli şişe" yazıyorsa, model bunları iki farklı ürün olarak değerlendirir ve sonuç rahatsız edici olur. Karakter için de aynısı geçerlidir.

**Tek ışık ifadesi:** Işık, iki klibin farklı zamanlarda çekildiğinin en büyük işaretidir. Işık ifadesini kilitlemek, 15 saniyenin tek bir çekimden geliyormuş gibi okunmasını sağlar.

**Negatif prompt:** `no captions` olmadan Seedance genellikle videoya metin bindirmeler yapar ve reklam yapay zeka üretimi gibi görünür. `no background music` olmadan diyaloğu boğan jenerik müzik bindirir.

**37 kelimeye sıkıştırma:** Bu gerçek konuşma hızı matematiğidir. 15 saniyeye 60 kelime doldurmak modelin çok hızlı konuşmasına ve dudak senkronizasyonunun bozulmasına yol açar.

**Birebir hook politikası:** /ugc becerisi VOC ve Marka DNA'sına karşı zaten alaka çalışması yaptı. Üst becerinin zaten doğruladığı bir hooku yeniden üretmek boşa harcanan çabadır ve çoğunlukla satırı düşürür.

**Üretimden önce uçuş öncesi kontrol listesi:** Higgsfield üretim başına ücret alır. Karakter görseli yüklenmediği için başarısız olan bir üretim gerçek para kaybıdır. Kontrol listesi kredi tasarrufu sağlar.

**Otomatik yükleme yok:** Kullanıcının aynı klasörde birden fazla karakter dosyası olabilir. Yanlış olanı otomatik seçmek, yanlış içerik üreticisiyle üretim yapmak demektir. Yalnızca kullanıcı onaylı yüklemeler.

---

## Referans dosyaları

| Dosya | Ne zaman yükle | Öncelik |
|---|---|---|
| `references/seedance-2-capabilities.md` | Adım 2, herhangi bir prompt yazmadan önce | Kritik |
| `references/ugc-prompt-examples.md` | Adım 5, her prompt yazılırken | Kritik |
| `references/Hook_Archetype_Guide.md` | Adım 4, 6 arketip seçilirken | Kritik |
| `references/fal-ai-setup.md` | Adım 7C, yalnızca kullanıcı API üretim yolunu seçerse | Talep üzerine |

---

## Çıktı doğrulaması

Bu beceriyi tamamlandı olarak bildirmeden önce doğrula:

1. Beklenen yolda çıktı mevcut: `<pwd>/Reklam Fabrikası/05_UGC/prompts/<niche-slug>/seedance-prompts-<YYYY-MM-DD>.md` (veya niş alt dizini yoksa yedek yol).
   - Yol B videoları (Yol B seçildiyse): kullanıcının istediği N değerleri için `<pwd>/Reklam Fabrikası/05_UGC/videos/path_b_outputs/video_<N>.mp4` ve `manifest.json`.
   - Yol C videoları (Yol C seçildiyse): kullanıcının istediği alt küme için `<pwd>/Reklam Fabrikası/05_UGC/videos/<niche-slug>/prompt-<N>.mp4`.
2. Çıktı boş değil (6 tam yazılmış prompt için dosya boyutu > 5000 bayt; video dosyaları her biri > 100000 bayt).
3. Beklenen içerik sayısı iddia ile eşleşiyor:
   - Dosyada tam olarak 6 numaralandırılmış prompt var.
   - 6 prompt arasında en az 4 farklı farkındalık aşaması kapsanmış.
   - Her promptta kilitli karakter tanımlayıcısı, kilitli ürün tanımlayıcısı, kilitli ışık ifadesi birebir mevcut.
   - Alt kümeyle Yol B için manifest, kullanıcının istediği tam prompt numaralarını içeriyor.
4. Yer tutucu dize kalmamış:
   - `<niche>`, `[BRAND]`, `[character]`, `<TODO>` veya `lorem ipsum` yok.
   - Herhangi bir prompt gövdesinde `Sahne 1:` veya zaman damgası işaretçisi yok.
5. Tüm zorunlu bölümler doldurulmuş:
   - Dosya başlığı (marka, tarih, kaynak UGC senaryosu referansı, kilitli tanımlayıcılar)
   - Prompt 1'den Prompt 6'ya, her biri `Negative prompt: no captions, no background music` ile bitiyor
   - Her promptun çift tırnak içinde diyaloğu var (Seedance dudak senkronizasyonu tetikleyicisi)

Doğrulama başarısız olursa:

1. Önce otomatik düzeltmeye çalış:
   - Bir promptta negatif prompt satırı eksikse ekle.
   - Tanımlayıcılar promptlar arasında kaymışsa etkilenen promptları kilitli dizeleri birebir kullanacak şekilde yeniden yaz.
   - Diyalog 40 kelimeyi aşıyorsa destek satırını keserek 37 kelimeye indirge.
   - Yer tutucular kalmışsa UGC senaryosu, VOC ve Marka DNA'sından doldur.

2. Otomatik düzeltme başarısız olursa, kullanıcıya dürüst bir rapor sun:
   "UGC promptları: 6 prompt ürettim ama doğrulama <sorun> gösterdi. <düzeltme girişimi>'ni denedim ve <işe yaramadı / kısmen işe yaradı>. Eksiksiz sonuç almak için şunları yapabilirsin:
   - En az 3 farklı hook içeren daha zengin bir UGC senaryosu sağla
   - Tanımlayıcının somut olması için karakter görseli yükle
   - Tanımlayıcının gerçek ürünle eşleşmesi için ürün görseli yükle
   Veya başarısız olan prompt numaralarını paylaş, yalnızca onları yeniden oluşturayım."

3. Senaryo arketip eşlemesi için 6 ayrı hook sağlamadıysa:
   - ONCE daha geniş parametrelerle dene:
     - Müşterinin sesindeki 2 ila 3 ek hook satırı için VOC belgesini tara
     - Doldurulmamış arketipler için Marka DNA tonunu kullanarak yeni hooklar üret
   - Hâlâ eksikse, dürüst rapor sun:
     "UGC promptları: 6 hook arketipini (görsel açılış, tepki, serzeniş, duyusal, demo, iddia) denedim ama kaynak UGC senaryosu yalnızca N kullanılabilir hook içeriyordu ve VOC yeterli alternatif sunmadı. Devam etmek için şunları yapabilirsin:
     - Daha fazla ayrı hook satırıyla daha uzun bir senaryo üretmek için /ugc'yi yeniden çalıştır
     - Müşterinin sesinde 3 ila 5 ek hook fikri yapıştır
     - Yalnızca en güçlü arketipleri kullanarak daha kısa bir seti onayla (6 yerine 4 prompt)
     Ya da senaryonun en güçlü satırını paylaş, 6 promptu onun varyasyonları etrafında oluşturayım."
