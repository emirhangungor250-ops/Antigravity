# 34 Klişe, Açılış Sayfaları için Yapay Zeka Klişesi Denetimi

awaken7050dev/anti-slop-ui (MIT) kaynaklı uyarlamalar ve anthropics/skills/frontend-design yönergeleriyle birleştirilmiştir. Ücretli Meta reklam açılış sayfaları için özelleştirilmiştir.

## Kritik sarmalayıcı kural

**Marka, estetik tercihin önüne geçer.** Marka DNA'sı açıkça Inter'i gövde yazı tipi olarak bildiriyorsa Inter kullan. Marka DNA'sı kahraman bölümü için mor gradyan belirtiyorsa kullan. Aşağıdaki 34 klişe YALNIZCA beyan edilmemiş tercihler için geçerlidir. Markaya rağmen değil, marka içinde özgün ol.

Aşağıdaki her klişeyi kontrol ederken şunu sor: "Marka DNA'sı bu tercihi açıkça bildirdi mi?" Evet ise marka kazanır. Hayır ise klişeyi uygula.

---

## Aile 1: Görsel Varsayılanlar (8 klişe)

### Klişe 1: Genel gradyanlar

**Klişe:** Mor-mavi gradyan kahraman. Pembe-turuncu "canlı" kahraman. Anlatısı olmayan her türlü gökkuşağı gradyanı.

**Düzeltme:** `--brand-primary` ile düz marka rengi kullan. Gradyan Marka DNA'sı tarafından zorunlu kılınıyorsa yalnızca 2 durak, marka renkleri kullan ve açıyı eğ (35 veya 145 derece; asla 90 veya 180 derece değil).

### Klişe 2: Her şey hap şekli

**Klişe:** Her kart `rounded-full` veya `rounded-3xl`. Her buton bir hap. Her rozet bir hap.

**Düzeltme:** TEK bir yarıçap ölçeği belirle ve ona sadık kal. Marka DNA'sı aksi belirtmedikçe kartlar için varsayılan `rounded-lg` (8px), butonlar için `rounded-md` (6px) kullan. Haplar yalnızca durum rozetleri ve etiketler içindir.

### Klişe 3: Her şeyin üzerinde yumuşak gölgeler

**Klişe:** Her kartta `shadow-xl`. Her bölümde yumuşak düşen gölge. Varsayılan olarak cam efekti.

**Düzeltme:** Gölgeyi bilinçli kullan. Kahraman CTA'sı bir gölge alır. Diğer elemanlar ayrım için kenarlıklar kullanır (`border-[var(--brand-muted)]/20`). Ağır gölgeleri izlenim düzeyi 4-5 için sakla.

### Klişe 4: Dokunulmadan teslim edilen bileşen kütüphaneleri

**Klişe:** Varsayılan dolgu, varsayılan kenarlık, varsayılan başlıkla shadcn/ui kartı. Özelleştirme yapılmamış varsayılan Tailwind UI kahraman bölümü. Kütüphanenin kendi pazarlama sitesine benzeyen her şey.

**Düzeltme:** Bileşen başına en az 3 tasarım tokenını geçersiz kıl: boşluk, renk, tipografi veya kenarlık işlemi. Sayfa bir shadcn demosu gibi GÖRÜNMEMELIDIR.

### Klişe 5: Dekoratif tireler ve italik vurgular

**Klişe:** "FEATURES" başlığını tirelerle çerçeveleyen üst etiket etiketleri. Anlamsal bir neden olmaksızın "vurgu" için başlıkta italikleştirilen tek bir kelime.

**Düzeltme:** Sade bölüm işaretleri (`01 / FEATURES` ya da yalnızca `FEATURES`). Italik yalnızca alıntılarda veya gerçekten italik olan terimlerde. Dekoratif noktalama işareti yok. Hiçbir yerde tire yok.

### Klişe 6: Ürün yerine soyut grafikler

**Klişe:** Ürün gerçek satış noktasıyken kahramanın yörüngesel şemalar, geometrik şekiller veya belirsiz marka işaretleri kompozisyonu göstermesi. Satılan şey görünmez.

**Düzeltme:** Ürünü göster. DTC için yaşam tarzı fotoğrafı. SaaS için ürün ekran görüntüsü. Hizmet işletmeleri için gerçek yüz. Ürün görseli yoksa `REPLACE_WITH_PRODUCT_HERO_IMAGE` işaretçiyle yüksek kaliteli bir yer tutucu blok kullan, soyut dekorasyon değil.

### Klişe 7: Genel stok fotoğrafı kahraman bölümleri

**Klişe:** Ofiste gülen çeşitli insanlar stok fotoğrafı. Dizüstü bilgisayarda eller. Markayla ilgisi olmayan yaşam tarzı stoku.

**Düzeltme:** Gerçek reklam kreatifini veya ondan türetilmiş bir karesini kahraman olarak kullan. Bu otomatik olarak mesaj uyumunu sağlar. Görsel yoksa H1'in görüntü alanına hakim olduğu tipografik bir kahraman bölümü kullan.

### Klişe 8: Mor, teal veya gradyanla doldurulmuş metin

**Klişe:** `bg-clip-text` gradyan dolguyla işlenen başlık. "Premium" görünmek için gölgeli kelimeler. Beyaz üzerine mor metin.

**Düzeltme:** Düz renkli metin. Gövde için `--brand-ink`, vurgulanan kelimeler için `--brand-primary` kullan. Gradyanlı metin yalnızca Marka DNA'sı açıkça bildiriyorsa kabul edilir.

---

## Aile 2: Tipografi (8 klişe)

### Klişe 9: Her şeyde Inter

**Klişe:** Hem ekran hem gövde yazı tipi olarak Inter Variable. Ağırlık değişikliklerinin ötesinde hiyerarşi yok.

**Düzeltme:** Marka DNA'sından iki farklı yazı tipi ailesi (1 ekran + 1 gövde). Marka DNA'sı yalnızca tek bir yazı tipi adlandırıyorsa aynı dökümhaneden ya da Google Fonts'tan zıt bir gövde yazı tipiyle eşleştir (ekran: editoryal serif ve gövde: temiz sans-serif).

### Klişe 10: Mobilde kırılan kahraman metni

**Klişe:** Duyarlı ölçekleme yapılmadan `text-7xl` masaüstü boyutunda H1. 375px görüntü alanında H1 beş satıra sarılıp sıkışmış görünür.

**Düzeltme:** `clamp()` veya Tailwind duyarlı öneklerini kullan: `text-4xl md:text-6xl lg:text-7xl`. H1'i zihinsel olarak 375px, 768px, 1280px'de test et.

### Klişe 11: 16px altında gövde metni

**Klişe:** Gövde metni olarak `text-sm` (14px) veya `text-xs` (12px). Mobilde okunması güç.

**Düzeltme:** Gövde metni minimum 16px (`text-base`). Premium his için 17px veya 18px. Daha küçük boyutlar yalnızca yasal metinler ve meta veriler içindir.

### Klişe 12: Gövdede çok sıkı satır yüksekliği

**Klişe:** Gövde paragraflarında `leading-tight` veya `leading-snug`. Sıkışmış görünür.

**Düzeltme:** Gövde paragrafları `leading-relaxed` (1,625) veya premium his için `leading-loose` kullanır. Başlıklar `leading-tight` (1,25) kullanır.

### Klişe 13: Tamamen cümle harfi VEYA tamamen büyük harf

**Klişe:** Her başlık kurumsal sunum gibi büyük harfle yazılmış. Ya da marka minimalist değilken "minimalist" his için her başlık küçük harf.

**Düzeltme:** Marka DNA'sının ses bloğunu izle. Marka editoryal veya lüks değilse varsayılan olarak başlıklarda cümle harfine dön. H1'i bir cümle gibi noktalandır (noktalı veya noktasız, ama tutarlı).

### Klişe 14: Her başlıkta ekran yazı tipleri

**Klişe:** H1, H2, H3, H4 hepsinde aynı ekran yazı tipi. Görsel ritim çöker.

**Düzeltme:** Ekran yazı tipi yalnızca H1 ve bölüm H2'lerinde. H3 ve altı gövde yazı tipinde, ağırlık olarak bold'a yükseltilmiş.

### Klişe 15: Küçük büyük harflerde harf aralığı yok

**Klişe:** `uppercase` ile varsayılan `tracking-normal` kullanan üst etiket etiketleri. Sıkışmış görünür.

**Düzeltme:** Büyük harfli üst etiketler `tracking-wider` veya `tracking-widest` (0,05-0,1em) kullanır. Yazı tipi ağırlığını 500-600 ekle.

### Klişe 16: Her yerde aynı yazı tipi ağırlığı

**Klişe:** Her şey `font-medium`. Ya da her şey `font-bold`. Kontrast yok.

**Düzeltme:** Ağırlığı hiyerarşi için kullan: H1'de 700-900, H2'de 700, H3'te 600, gövdede 400-500, üst etikette 500-600. Sayfa genelinde minimum üç ağırlık.

---

## Aile 3: Düzen (10 klişe)

### Klişe 17: Simetrik üç kartlı ızgara

**Klişe:** Özellikler bölümü her zaman aynı kart yüksekliği ve aynı simge yerleşimiyle 3 kartlık ızgara. Öngörülebilir.

**Düzeltme:** Izgarayı çeşitlendir: masaüstünde bir kartın 2 sütun kapladığı 4 sütunluk. Ya da asimetrik 2x2. Ya da mobilde yatay kaydırmalı liste. Hiyerarşiyi ima etmek için düzeni kullan.

### Klişe 18: Her şey ortalanmış

**Klişe:** Kahraman metni ortada. Bölüm H2'leri ortada. Gövde paragrafları ortada. Web sitesi değil slayt sunumu gibi görünür.

**Düzeltme:** Asimetrik varsayılandır. Sağda hizalanmış görüntüyle solda hizalanmış metin. Başlıklar butonlar ortalanmışken bile solda hizalanmış olabilir. Yalnızca içerik gerçekten bunu gerektirdiğinde ortala (tek CTA, alıntı çekimi, final kapanış).

### Klişe 19: Gösterge panelinde tüketici uygulama boşluğu

**Klişe:** B2B SaaS sayfasında büyük bölümler, büyük dolgu, büyük kenar boşlukları. Sayfa ciddi bir araç yerine iPhone uygulaması gibi hissettiriyor.

**Düzeltme:** Yoğunluğu hedef kitleyle eşleştir. İzlenim düzeyi 1-2 (veri terminalleri, profesyonel panolar) `py-8` ile `py-12` sıkı bölümler kullanır. Düzey 4-5 (vitrinler) `py-24` ile `py-32` cömert boşluk kullanır. Marka DNA'sının ses bloğunu oku.

### Klişe 20: Hiçbir şey katmayan hareket

**Klişe:** Her bölüm kaydırmada beliriyor. Her kartın üzerine gelince kaldırma efekti. Hareket işlevsel değil performatif.

**Düzeltme:** Hareket yalnızca anlam taşıdığında. Sosyal kanıt bloğunda kaydırma görünümü (referans önemlidir). Yalnızca birincil CTA'da üzerine gelme durumu. Hareket uğruna hareket yok.

### Klişe 21: 12 sütunlu ızgara taşması

**Klişe:** Kahraman metni tam 12 sütun genişliğine yayılıyor. Satırlar 120 karaktere ulaşıyor. Okumak zor.

**Düzeltme:** Gövde içeriği satır başına maksimum 65-75 karakter. Kahraman alt başlığı için `max-w-2xl`, gövde bölümleri için `max-w-prose`. Konteynerler (`max-w-7xl`) yalnızca tam genişlikli görsel bölümler için.

### Klişe 22: Bağlamsız logo şeridi

**Klişe:** Markanın hiç yer almadığı Forbes, Inc, TechCrunch gibi yayınlarla "Şurada yayınlandı" logo çubuğu. Ya da "güven" için rastgele ortak logolar.

**Düzeltme:** Yalnızca markanın hak ettiği logoları ekle. Markanın kayda değer basın haberi yoksa müşteri sayısıyla değiştir ("2022'den bu yana 4.200 müşteri") veya yorum sayısıyla yıldız puanı kullan.

### Klişe 23: Ücretli açılış sayfasında çapa bağlantılı nav

**Klişe:** Meta reklamından tek tıkla gelen bir sayfada Ana Sayfa, Özellikler, Fiyatlandırma, Hakkımızda, İletişim bağlantıları içeren üst nav.

**Düzeltme:** Nav'ı tamamen gizle ya da yalnızca logo (bağlantısız) ve birincil CTA göster. Diğer bölümlere çapa bağlantısı yok (kullanıcı kaydırır). Kesinlikle sayfa dışı bağlantı yok.

### Klişe 24: Tek sayfalık açılışta hamburger menüsü

**Klişe:** Tek sayfalık bir açılışta üç satırlı mobil menü simgesi. Menü tek bir boş bağlantıya açılıyor.

**Düzeltme:** Hamburger yok. Mobil nav yalnızca logo + CTA gösterir. Sayfa gerçekten çok bölümlüyse bunun yerine yapışkan alt CTA çubuğu kullan.

### Klişe 25: 5 sütunlu boş bağlantılarla dolu alt bilgi

**Klişe:** Marka henüz bu sayfalara sahip olmadığı için gri yer tutucu bağlantılarla dolu "Kaynaklar, Şirket, Yasal, Sosyal, Destek" sütunlu alt bilgi.

**Düzeltme:** Minimal alt bilgi: telif hakkı, gizlilik bağlantısı, koşullar bağlantısı, destek e-postası. En fazla üç satır. Markanın gerçek alt bilgi içeriği varsa kullan. Yer tutucu yok.

### Klişe 26: Mobil yapışkan CTA yok

**Klişe:** Birincil CTA yalnızca kahramanda ve alt bilgide görünür uzun DTC açılış sayfası. Ortayı kaydıran kullanıcıların dönüşüme giden yolu yok.

**Düzeltme:** Kullanıcı kahramanı geçtikten sonra görüntü alanının altında görünen mobil yapışkan CTA çubuğu. DTC için zorunlu. Lead gen için isteğe bağlı ama tavsiye edilir.

---

## Aile 4: İçerik Klişesi (8 klişe)

### Klişe 27: Kahraman bölümünde "Hoş geldiniz"

**Klişe:** H1, "BrandName'e Hoş Geldiniz" veya "X'in geleceğini sunuyoruz" şeklinde okunuyor. Ürünün ne yaptığını söylemiyor.

**Düzeltme:** H1, reklam başlığından en az bir 3+ kelimelik ifade içermelidir (mesaj uyumu kuralı). Bir ürün duyurmak değil, bir sonuç vaat etmek zorundadır.

### Klişe 28: Her cümlede tireler

**Klişe:** Gövde kopyası konuşma duraklamaları olarak tirelerle dolu. Yapay zeka klişesi.

**Düzeltme:** Konuşma duraklaması olarak tire yok. Duraklama olarak kısa tire de yok. Nokta, virgül veya iki nokta üst üste kullan. Tireler yalnızca gerçek parentetik açıklamalarda kabul edilebilir, ama yine de virgüller tercih edilir.

### Klişe 29: Doğrulanmamış pazarlama kopyası

**Klişe:** Kaynaksız "10.000'den fazla müşteri tarafından güvenildi". Yorum sayısı olmadan "5 yıldızlı". Ölçüt olmadan "sektör lideri".

**Düzeltme:** Her sayı Marka DNA'sından veya VOC'tan gelir. Müşteri sayısı varsa tarihiyle birlikte belirt. Yorum sayısı varsa kaynağına bağla. Sayı yoksa farklı bir cümle yaz.

### Klişe 30: Yapay zeka klişesi kelime ve ifadeleri

**Klişe:** revolutionize, unlock, seamless, leverage, supercharge, game changer, harness, empower, elevate, transformative, in today's fast paced world, level up, paradigm shift, holistic, robust, scalable, synergistic.

**Düzeltme:** Yasak liste uygulanır. Bu kelimeleri içeren her cümleyi yeniden yaz. Markanın kendi kelimelerini bulmak için Marka DNA'sının ses bloğunu kullan.

### Klişe 31: Belirsiz fayda madde işaretleri

**Klişe:** "Zaman kazanın", "Verimliliği artırın", "Sonuçları yönlendirin", "Verimliliği artırın". Spesifiklik olmayan faydalar.

**Düzeltme:** VOC'tan somut fayda kopyası. "Daha iyi odaklanma" değil "10'a kadar daha keskin odak". "Raporlama zamanını 4 saatten 30 dakikaya indir" değil "Rapor hazırlamada zaman kazan". VOC'tan spesifikler; asla uydurulmuş sayılar.

### Klişe 32: Genel kurucu hikayesi

**Klişe:** "X'i demokratize etme misyonuyla 2021'de kuruldu" şablonu. Her markaya uyabilir. Gerçek hiçbir şey söylemiyor.

**Düzeltme:** Mevcutsa Marka DNA'sındaki köken hikayesini birebir kullan. Yoksa bir spesifik somut olgu (konum, kuruluş anı, ismi verilen kurucu, yıl) kullan ve gerisini bırak.

### Klişe 33: Yer tutucu referanslar

**Klişe:** "Bu ürün hayatımı değiştirdi! En iyi alışveriş. 10/10!" ile "Doğrulanmış Alıcı Sarah J." atıfı.

**Düzeltme:** VOC'tan bütün birebir alıntıları çek. Müşterinin gerçek adını, rolünü, yaşını veya şehrini VOC'ta mevcutsa ekle. Uzunlukları karıştır (biri kısa ve etkili, diğeri daha uzun hikaye). VOC'ta kullanılabilir uzunlukta 3'ten az referans varsa yalnızca gerçek olanları kullan.

### Klişe 34: Uydurulmuş sorularla SSS

**Klişe:** "Bu ürün iyi mi?" "Nasıl çalışır?" "Neden satın almalıyım?" Gerçek hiçbir müşterinin sormadığı genel SSS soruları.

**Düzeltme:** SSS soruları BİREBİR VOC'tan gelir. VOC "Her zaman iptal edebilir miyim?" içeriyorsa SSS sorusu budur, "İptal politikanız nedir?" değil. Müşterinin gerçek ifadesini kullan.

---

## Gönderim öncesi kontrol listesi

Dosyayı diske yazmadan önce tüm 34 klişenin çözüldüğünü doğrula. Her aile için tek satır onay yazdır:

```
Aile 1 (Görsel Varsayılanlar): 8/8 temiz
Aile 2 (Tipografi): 8/8 temiz
Aile 3 (Düzen): 10/10 temiz
Aile 4 (İçerik Klişesi): 8/8 temiz
```

Herhangi bir klişe çözülmemişse çıktıdan önce düzelt. Bilinen klişelerle gönderme.

## İzlenim düzeyi ölçeği

anti-slop-ui (MIT) kaynaklı. İzlenim düzeyini Adım 5'te Marka DNA'sının tonuna göre erken belirle:

| Düzey | Ad | Kullanım | Yoğunluk | Hareket | Renk |
|---|---|---|---|---|---|
| 1 | GÖRÜNMEZ | Veri terminali, bilginin kendisi ürün | Sıkı | Yok | Tek ton |
| 2 | IHTIYATLI | Profesyonel pano, B2B SaaS lead gen | Orta | Minimal | 2 ton |
| 3 | DENGELİ | Modern SaaS, orta AOV DTC | Standart | Hafif | 3 ton |
| 4 | ETKİLEYİCİ | Premium DTC, tasarım odaklı tüketici | Cömert | Düşünülmüş | Tam palet |
| 5 | MUHTEŞEM | Lüks, yüksek AOV ($150+) DTC vitrini | Bol | Koreografili | Tam palet + doku |

Yanlış düzeyi seçmek sayfanın markayla uyumsuz görünmesine neden olur. Düzey 4'te ciddi bir B2B SaaS oyuncak gibi hissettiriyor. Düzey 2'de premium DTC vergi formu gibi görünüyor.

Ücretli Meta reklam trafiği için:

- $50 altı AOV DTC: Düzey 3
- $50-$150 AOV DTC: Düzey 3-4
- $150 üstü AOV DTC: Düzey 4-5
- B2B lead gen: Düzey 2-3
- Tüketici hizmeti lead gen: Düzey 3-4
