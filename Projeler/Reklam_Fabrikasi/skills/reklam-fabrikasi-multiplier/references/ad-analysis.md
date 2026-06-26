# Kazanan Reklam Analiz Çerçevesi, Bu Reklamı Kazandıran Neydi

Kullanıcının kazanan reklam görselini aldığında aşağıdaki her öğeyi analiz et. Kesin ve spesifik ol. Bu analizin amacı rakip yeniden inşasından farklıdır. Burada dönüşüm DNA'sını çıkarıyorsun; böylece sahne, kanca ve metinde bilinçli olarak ayrışırken varyasyonlarda onu koruyabilirsin.

---

## 1. YAPISAL İSKELET (varyasyonlar boyunca koru)

Bu, reklamın işe yarıyor olmasını sağlayan düzen desenidir. Sahne ve metin değişse bile her varyasyonda tanınabilir biçimde korunmalıdır.

- **Format ve boyutlar:** Kare (1:1), dikey (4:5 veya 9:16) veya yatay (1.91:1)?
- **Görsel bölgeler:** Görsel nasıl bölünmüş? Bölgeleri açıkla. Örnek: "üst %60 yaşam tarzı arka planında ürün hero, alt %40 beyaz başlıklı koyu metin bloğu"
- **Metin hiyerarşisi:** Her metin öğesi nerede ve nasıl ağırlıklandırılmış? (en büyükten en küçüğe)
- **Ürün konumu:** Merkezde, sola bağlı, sağa bağlı, hero, çevresel, elle tutulan vb.
- **Negatif alan deseni:** Boş alan nerede ve ne rol oynuyor?
- **Genel yoğunluk:** Minimal/temiz mi yoksa yoğun/kalabalık mı?

Bunu yapısal iskelet olarak kaydet. Her varyasyon bu iskeleti korumalıdır.

---

## 2. METİN ENVANTERİ

Reklamdaki her metin parçası için kelime sayısını ve rolünü kaydet. Kelime sayıları prompt oluşturucuya beslenirler böylece her varyasyon görsel dengeyi eşleştirebilir.

**BAŞLIK (en büyük/en belirgin metin):**
- Tam metin (okunabiliyorsa) veya yaklaşık içerik
- Kelime sayısı: [X kelime]
- Boşluklar dahil karakter sayısı: [yaklaşık X karakter]
- Yazı tipi ağırlığı: bold / yarı-bold / normal
- Görsele göre yazı tipi boyutu: büyük / orta / küçük
- Renk: [belirlenebiliyorsa hex, yoksa açıklama]
- Konum: [görsel üzerinde nerede]
- Tüm büyük harf / başlık büyüklüğü / cümle büyüklüğü

**ALT BAŞLIK veya İKİNCİL METİN (varsa):**
- Tam metin veya yaklaşık içerik
- Kelime sayısı: [X kelime]
- Boşluklar dahil karakter sayısı: [yaklaşık X karakter]
- Yazı tipi ağırlığı, boyutu, rengi, konumu

**GÖVDE METNİ (varsa):**
- Tam metin veya yaklaşık içerik
- Kelime sayısı: [X kelime]
- Satır sayısı: [X satır]
- Başlığa göre konum ve boyut

**HGPM / BUTON METNİ (varsa):**
- Tam metin veya yakın yaklaşım
- Kelime sayısı: [X kelime]
- Stil: buton / düz metin / rozet
- Konum

**ROZET, ETİKET veya ÇAĞRI (varsa):**
- Tam veya yaklaşık metin
- Kelime sayısı: [X kelime]
- Stil ve konum

**ÜST KATMAN METNİ veya GRAFİK METİN:**
- Görsel sahneye entegre edilmiş herhangi bir metin
- Her parça için kelime sayısı

---

## 3. DÖNÜŞÜM MEKANİĞİ (en önemli bölüm)

Dönüşüm mekaniği, bu reklamın işe yarıyor olmasının yapısal sebebidir. Açı ve sahne değişse bile her varyasyonun koruması gereken şeydir. Tam olarak belirle.

Bu listeden baskın mekaniği seç (veya karma tanımla):

- **Başlık odaklı:** Başlık reklamdır. Görsel temiz destektir. Mekanik: metin dönüşüm ağırlığını taşır.
- **İddia/sonuç odaklı:** Spesifik, çürütülebilir bir sonuç veya istatistik odak noktasıdır. Mekanik: sonuç kanıtı.
- **Referans odaklı:** Bir müşteri alıntısı veya yorumu odak noktasıdır. Mekanik: gerçek bir seste temellenen sosyal kanıt.
- **Demo odaklı:** Ürün kullanımda gösterilmiş veya mekanizması görünür. Mekanik: söylemek yerine göstermek.
- **Karşılaştırma odaklı:** İki durum veya iki seçenek yan yana gösterilmiş. Mekanik: kontrast tercih tetikler.
- **Teklif odaklı:** İndirim, anlaşma veya promosyon odak noktasıdır. Mekanik: aciliyet artı değer.
- **Yaşam tarzı odaklı:** Reklam üründen çok kimliği, ortamı veya anı satar. Mekanik: özlem.
- **Desen kesintisi odaklı:** Görsel olarak beklenmedik veya tonolarak karşıt bir şey. Mekanik: kaydırmayı durduran yenilik.
- **Liste odaklı:** Maddeler, çağrılar veya özellik noktaları baskındır. Mekanik: hızlı tarama fayda absorpsiyonu.
- **UGC odaklı:** Reklam kullanıcı tarafından üretilen içeriği taklit eder (telefon çekimi, sıradan, ham). Mekanik: yerel his reklam direncini kaldırır.

Ardından bu mekaniğin bu reklamda spesifik olarak nasıl işlediğini açıklayan 1 ila 2 cümle yaz. Örnek: "Beş yıldız çıpasıyla referans odaklı. Yaşam tarzı arka planındaki beyaz alıntı metni ağır işi yapıyor. Ürün kasıtlı olarak biraz odak dışında kalıyor böylece izleyici önce alıntıyı okuyor."

---

## 4. MEVCUT KANCA AÇISI (varyasyonlar bilinçli olarak farklılaşacak)

Bu kazanan reklamın kanca açısı şu anda nedir? En yakın eşleşmeyi seç:

- **Merak boşluğu:** Çözüm gerektiren bir bilgi boşluğu yaratır
- **Cesur iddia:** Spesifik, çürütülebilir sonuç veya istatistik
- **Desen kesintisi:** Beklenmedik bir şey gösterir veya söyler
- **İlişkilendirilebilirlik:** Müşterinin yaşanmış deneyimini tam olarak yansıtır
- **Sosyal kanıt:** Benimseme sayıları, referanslar, akran davranışı
- **Korku/kayıp:** Harekete geçilmezse kaybedilecek şey
- **Özlem:** Arzulanan kimliği veya sonucu çizer
- **Sorun-ajitasyon:** Acıyı adlandırır ve yoğunlaştırır
- **Doğrudan teklif:** İndirim, ücretsiz deneme veya sınırlı süreli anlaşma

Varyasyon motorunun varyasyon seti boyunca bilinçli olarak farklı olanları seçebilmesi için bu kancayı not et.

---

## 5. MEVCUT FARKINDALIK DÜZEYİ (varyasyonlar birden fazla düzeye yayılacak)

Kazanan reklam hangi Schwartz aşamasını hedefliyor?

- **Habersiz:** Sorun veya üründen bahis yok, kimlik veya yaşam tarzı odaklı
- **Sorun-Farkında:** Acıyı adlandırıyor, henüz çözüm yok
- **Çözüm-Farkında:** Kategori düzeyinde, marka adı yok
- **Ürün-Farkında:** Marka veya ürüne özgü
- **En-Farkında:** Doğrudan teklif, fiyat, aciliyet

Varyasyonların farklı aşamaları hedefleyebilmesi ve farklı izleyici segmentlerinin kilidini açabilmesi için bunu not et.

---

## 6. MEVCUT GÖRSEL SAHNE VE RENK DÜNYASI (varyasyonlar bundan ayrışacak)

Varyasyonların bilinçli olarak farklı olanları seçebilmesi için mevcut sahneyi tam olarak tanımla:

- **Mekan/ortam:** Stüdyo, mutfak, banyo, açık hava, spor salonu, yatak odası, çalışma alanı vb.
- **Aydınlatma:** Yumuşak doğal, sert stüdyo, altın saati, loş kasvetli, parlak klinik vb.
- **Arka plan stili:** Tek renk, degrade, yaşam tarzı sahnesi, dokulu vb.
- **Renk paleti:** 2 ila 4 baskın rengi ve atmosferi listele (sıcak/soğuk, cesur/soluk, koyu/açık)
- **Ürün bağlamı:** Temiz yüzey üzerinde hero, kullanım sırasında, elle tutulan, çevresel, düz yatış vb.
- **İnsan öğesi:** Biri var mı? Yüzü görünüyor mu? Beden dili? Yoksa hiç insan yok mu?
- **Aksesuar veya bağlam nesneleri:** Çerçevede başka ne var?
- **Görsel stil:** Fotoğraf, illüstrasyon, grafik tasarım, kolaj, ekran görüntüsü, maket
- **Sosyal kanıt görsel öğeleri:** Yıldızlar, logolar, yorum parçaları, sertifika rozetleri?

Bu temel sahnedir. Her varyasyon farklı bir sahne VE farklı bir renk dünyası kullanmalıdır.

---

## 7. BU REKLAM NEDEN KAZANIYOR

Bu reklamın neden performans gösterdiğine dair 3 ila 5 madde yaz. Şunları dikkate al:
- Spesifik kanca ve neden kaydırmayı durduruyor
- Vaadin netliği ve basitliği
- Gözü çeken görsel kontrast veya odak noktası
- Farkındalık düzeyi-izleyici eşleşmesi
- Mevcut güven sinyalleri
- Format verimliliği

Bu senin stratejik briefindir. Her varyasyon görsel olarak ayrışırken bu sebepleri onurlandırmalıdır.

---

## 8. KORU/DEĞİŞTİR LİSTESİ

Varyasyonlar boyunca neyin kalacağını ve neyin değişeceğini net biçimde listele.

**Tüm varyasyonlarda AYNI kalır:**
- Yapısal iskelet (düzen bölgeleri, metin hiyerarşisi, ürün konum deseni)
- Marka kimliği (Marka DNA'sında tanımlandığı biçimiyle renkler, logo yerleşimi)
- Ürün (kullanıcının yüklediği ürün görsellerinden render edilir)
- Dönüşüm mekaniği türü (referans odaklı reklamlar referans odaklı kalır, başlık odaklı başlık odaklı kalır vb.)

**Varyasyonlar boyunca DEĞİŞİR:**
- Görsel sahne ve ortam
- Renk dünyası ve aydınlatma
- Kanca mekaniği
- Farkındalık düzeyi
- Duygusal kayıt
- Metin (başlık, alt başlık, gövde, harekete geçirici mesaj, rozet)
- Aynı iskelet içinde ürün konumlandırma stili (hero vs. kullanım sırasında vs. elle tutulan)

Bu liste Aşama 1 ile Aşama 2 arasındaki köprüdür. Aşama 2, gerçek anlamda farklı varyasyonlar oluşturmak için bunu kullanır.
