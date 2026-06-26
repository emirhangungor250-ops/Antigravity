# Görsel aileler ve 10 satırlık evrensel yapı

Bu dosya, her render promptu için 5 sabit görsel aileyi ve 10 satırlık evrensel yapıyı tanımlar. Becerinin Adım 9'u bu dosyayı yükler ve onaylanan her konsept için tam 5 prompt yazar, her aile için bir tane. Her prompt GPT Image 2 hedeflidir.

Düzenleme geçiş promptları yoktur. Varyant başına tek güçlü render. Oluşturulan görsel ince ayar gerektiriyorsa kullanıcı ChatGPT konuşmasında normal bir takip mesajı gönderir, herhangi bir görseli nasıl düzelteceklerini bildikleri gibi.

---

## 5 görsel aile

Onaylanan her konsept 5 render alır, bu ailelerin her birinde birer tane. Aileler birbirinin yerine geçemez. Her aile farklı bir mekanizma aracılığıyla ikna eder, bu nedenle 5 varyantlık bir küme aynı fikir için 5 farklı dönüşüm kolunu kapsar.

### Aile 1, Product Hero

Ne aracılığıyla ikna eder: netlik ve arzu. Ürün odak noktasıdır, en çekici haliyle sunulur, maksimum işçilikle ve sıfır dikkat dağıtmayla.

Tipik sahne: temiz stüdyo yüzeyi veya düz marka rengi arka plan, ürün merkezi veya altın oran üçte birde, yumuşak yönlü ışık, kasıtlı gölge, marka renk paleti.

Bu ailedeki güçlü render'ı yapan: ürünün mutlak etiket doğrulukla render edilmesi (ambalajdaki her kelime yüklenen ürün görseli ile eşleşir), ışığın malzeme kalitesini ortaya koyması (mat ve parlak, doku, ağırlık) ve kompozisyonun pazar listesi değil editoryal çekim gibi hissettirmesi.

Kaçınılacaklar: karışık yüzeyler, çerçevede eller veya kollar (bu Aile 5'tir), ürün etrafında soyut dekorasyon, uyumsuz marka renkleri, bulanık veya bozulmuş ürün geometrisi.

### Aile 2, Problem State

Ne aracılığıyla ikna eder: tanıma. İzleyici kendi acısını 1,5 saniyede görsel olarak görerek duruyor çünkü onu tanıyor.

Tipik sahne: acı anındaki müşteri (ıstırap içinde değil, acının tanıdık günlük versiyonunda). Bir kişi olabilir, bir elde veya vücudun bir bölgesindeki semptomun yakın çekimi olabilir, sorunu işaret eden bir ortam olabilir (dağınık masa, yarı boş buzdolabı, loş ışıklı banyo).

Bu ailedeki güçlü render'ı yapan: acının hedef personanın kendisini hemen görmesi için yeterince özgün olması, görselin tıbbi korku veya utanç tetikleyicilerinden kaçınması (soğuk trafikte daha kötü performans gösterir) ve çerçevelemenin odak noktasını kalabalıklaştırmadan başlık yer paylaşımı için alan bırakması.

Kaçınılacaklar: genel stok fotoğraf "hayal kırıklığına uğramış kişi" enerjisi, sahte görünümlü sıkıntı, izleyiciye yargılayıcı görünen her şey, ürünün görünür olmasını gerektiren her şey (ürün Sonuç Durumuna aittir, Sorun Durumuna değil).

### Aile 3, Outcome State

Ne aracılığıyla ikna eder: özlem. İzleyici sonrayı, istenen hissi, "bu ben olabilirim" anını görür. Ürün mevcuttur ancak odak noktası değildir.

Tipik sahne: ürün sonrasındaki müşteri, kazanma anında. Sonucu yaşayan bir kişi olabilir (daha sakin sabah, işte daha keskin odaklanma, aynada özgüven, dışarıda enerji), kişiyi göstermeden kazanımı işaret eden çevresel bir çekim olabilir.

Bu ailedeki güçlü render'ı yapan: sonucun somut ve zamana bağlı olması ("harika hissediyor" değil "sabah 6'da tamamen uyanık", "daha fazla enerji" değil "saat 10'da daha keskin odaklanma"), ürünün mevcut ve tanınabilir ama ikincil olması ve duygusal okumanın umut, gurur veya huzur olması, sahte gülümseme değil.

Kaçınılacaklar: sahte "önce/sonra" sahneleme, stok fotoğraf neşesi, çerçevenin ortasında belirgin şekilde yüzen ürün (bu Aile 1'dir), markanın yasal olarak iddia edemeyeceği tıbbi bir sonucu ima eden her şey.

### Aile 4, Proof or Mechanism

Ne aracılığıyla ikna eder: güvenilirlik. İzleyici ürünün işe yaradığına dair kanıtı veri, mekanizma diyagramı, bileşen dökümü, karşılaştırma veya görünür sonuç olarak görür.

Tipik sahne: ürün etrafında istatistik çağrıları, bir bileşen veya parça patlama görünümü, yan yana karşılaştırma (biz ve alternatif), etiketli mekanizma diyagramı veya belgelenmiş sonuç görseli (üçüncü taraf testi, laboratuvar görseli, demonstrasyon çekimi).

Bu ailedeki güçlü render'ı yapan: her sayının, etiketin, bileşen adının veya karşılaştırma unsurunun gerçek olması (VOC'tan, Marka DNA'sından veya çekilen reklamlardan alınmış, asla uydurulmamış), düzenin yoğun veri yerine taranabilir bilgi olarak okunması ve ürünün kompozisyonu bastırılmadan sabitleyen unsur olması.

Kaçınılacaklar: uydurma istatistikler veya araştırmalar, sahte "[kurum] tarafından test edildi" iddiaları, sahte doktor onayları, sahte önce-sonra laboratuvar görselleri, uydurulmuş yüzdeler veya araştırma alıntıları. FTC 2024, ücretli reklamlardaki tüm bunları yasaklamaktadır.

### Aile 5, Identity or Social Proof

Ne aracılığıyla ikna eder: kabile ve tanıklık. İzleyici kendisiyle özdeşleştiği (veya özdeşleştiğini hayal ettiği) gerçek bir kişiyi ya da ürünün işe yaradığını onaylayan diğer gerçek müşterileri görür.

Tipik sahne: ürünü tutan veya kullanan gerçek hissettiren bir kişi (ürün çekiminden Held modu), UGC tarzı ayna selfie, yaşam tarzı fotoğrafı üzerine bindirilmiş ekran görüntüsü yorumu kartı, dikilmiş referans düzeni, genel bir ürün fotoğrafı üzerinde müşteri Reddit veya Instagram yorumu.

Bu ailedeki güçlü render'ı yapan: kişinin bu markanın gerçek bir müşterisi gibi görünmesi (stok model değil, jenerik influencer değil), referans metninin gerçek VOC'tan alınması (asla uydurulmamış), düzenin taklit ettiği platforma yerli görünmesi (Instagram yorumu gerçek bir Instagram yorumu gibi görünür, sahte reklam versiyonu gibi değil) ve biçim kasıtlı olarak kaba olduğunda bile marka kimliğinin sağlam kalması.

Kaçınılacaklar: sahte referanslar, sahte değerlendirme atıfları, markanın ortaklık kurmadığı gerçek ünlülerin fotoğrafları, jenerik "çeşitli gülümseyen insanlar grubu" stok enerjisi, sahnelenmiş görünen aşırı parlak UGC.

---

## 10 satırlık evrensel yapı

Her render promptu bu tam 10 satırlık yapıyı izler. Satırlar sabit sıradadır. Her satırın tek bir işi vardır. Yapı tutarlı olduğunda model daha iyi ayrıştırır ve satırlar öngörülebilir olduğunda becerinin QA'sı daha kolaydır.

```
1. Intent. Bu görüntünün ne için olduğunu ve hangi mekanizma aracılığıyla ikna ettiğini açıklayan tek cümle. "Static Meta ad for [MARKA], [AİLE] variant, [FARKINDALIK AŞAMASI]." ile başlar. Her şey için çerçeveyi belirler.

2. Subject. Çerçevede ne olduğunu adlandıran tek cümle. Ürün, kişi, sahne unsuru. Konseptin görsel yönünden ve yüklenen ürün görselinden alınmış.

3. Action or pose. Öznenin ne yaptığını açıklayan tek cümle. Stillat görsellerin bile ima edilmiş bir anı vardır, bunu adlandır.

4. Environment. Ortamı açıklayan tek cümle. Arka plan, yüzey, aksesuarlar, günün saati, konum.

5. Composition. Çerçeveyi açıklayan tek cümle. Kamera mesafesi, açısı, ürünün altın oran üçte birinde nerede durduğu, metin yerleşiminin nasıl sığacağı.

6. Lighting. Işığı açıklayan tek cümle. Kaynak, yön, kalite, gölge davranışı.

7. Style and medium. Görsel dili açıklayan tek cümle. Editoryal fotoğrafçılık, UGC selfie, illüstrasyon, ekran görüntüsü, mockup, kolaj. Konseptin görsel yönünden alınmış.

8. Mood and color. Duygusal okumayı ve renk paletini açıklayan tek cümle. Marka DNA'sı renk tokenlarından ve konseptin farkındalık aşamasından alınmış.

9. Text. Metin yerleşimini açıklayan tek cümle. Başlık (konseptin başlık adaylarından biri), yerleştirme, yazı tipi ağırlığı, renk. Başlıkların sonunda nokta yok. Görüntü metninde CTA yok.

10. Constraints. Modelin yapmaması gerekenleri listeleyen sabit son satır. Nokta yasağı kuralını, CTA yasağı kuralını, yapay zeka estetiği engelini, mobil öncelikli kompozisyon kuralını, ürün doğruluk kuralını ve FTC uyumluluk kuralını içerir.
```

Becerinin yazdığı her render promptunda kısıtlamalar satırı aynıdır:

```
Constraints: no period at the end of any headline. No call to action button or CTA text inside the image. No AI-aesthetic tells (no purple-to-blue gradient backgrounds, no orbital diagrams, no floating geometric shapes, no fake reflective light streaks, no over-saturated rainbow color fills). Mobile-first composition (subject and headline both readable on a 9:16 phone crop). Product label rendered with absolute fidelity to the uploaded product image (every word, every character, exact colors). No fabricated star ratings, no fabricated review counts, no fabricated press logos, no fabricated testimonials. Render at 1:1 aspect ratio (2880 by 2880) unless the concept's visual direction explicitly calls for another aspect.
```

---

## Beceri bu dosyayı nasıl kullanır

Adım 9, QA'dan geçen her konsepti döngüyle işler. Her konsept için 10 satırlık evrensel yapıyı izleyen 5 render promptu üretir, her aile için bir tane. Çıktı formatı tam olarak şudur:

```
APPROVED CONCEPT N: <konsept adı>

VARIANT N.1, Product Hero
1. Intent. <doldurulmuş>
2. Subject. <doldurulmuş>
3. Action or pose. <doldurulmuş>
4. Environment. <doldurulmuş>
5. Composition. <doldurulmuş>
6. Lighting. <doldurulmuş>
7. Style and medium. <doldurulmuş>
8. Mood and color. <doldurulmuş>
9. Text. <doldurulmuş>
10. Constraints. <yukarıdaki sabit kısıtlamalar satırı>

VARIANT N.2, Problem State
<10 satır>

VARIANT N.3, Outcome State
<10 satır>

VARIANT N.4, Proof or Mechanism
<10 satır>

VARIANT N.5, Identity or Social Proof
<10 satır>
```

Her varyant, Yol A'da ChatGPT'ye veya Adım 11'deki yol seçicide bağımsız olarak kopyalanıp yapıştırılabilir.

---

## Sıkı kurallar

1. Konsept başına tam 5 varyant. Her aile için bir tane. Ne daha fazla ne daha az.
2. 10 satır sabit sıradadır. Asla yeniden sıralama, asla atlama.
3. Kısıtlamalar satırı her varyant boyunca aynıdır. Asla yeniden yazma veya kısaltma.
4. 9. satırdaki başlık konseptin 3 başlık adayından biridir. Aynı konseptin farklı varyantları aday listesinden farklı başlıklar kullanabilir ancak her başlık kullanıcının daha önce gördüğü adaylardan biri olmalıdır.
5. Ürün doğruluğu tartışmasızdır. Her varyant yüklenen ürün görselini referans alır ve mutlak etiket eşleşmesi gerektirir.
6. Görüntünün içinde CTA metni yok. CTA'lar reklam metninde yaşar, kreatifte değil. (Metin becerisi CTA'ları yönetir.)
7. Başlıklarda nokta yok. Başlıklar son noktalama işareti olmadan biter. Soru işareti ve ünlem işareti uygun olduklarında kullanılabilir.
8. Hiçbir satırda em-dash veya cümle arası kısa çizgi yok. Virgül, "ve" kullan veya cümleleri böl. Pay-per-use gibi bileşik kelimeler kabul edilebilir.
