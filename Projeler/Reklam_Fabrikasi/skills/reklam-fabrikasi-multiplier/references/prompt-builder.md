# Prompt Oluşturucu, Varyasyonlar İçin Referans Görsel Promptları

Bu kılavuzun ürettiği promptlar model agnostiktir. Hem GPT Image 2 (eklentinin yüksek kalitede ve 4K eşdeğeri `image_size` ile önerilen varsayılanı) hem de Nano Banana 2 (daha ucuz alternatif) için temiz biçimde yapıştırılabilir. Aşağıdaki metin "görsel model" der; bu, `reklam-fabrikasi-multiplier` içindeki model seçici adımında kullanıcının seçtiği ikisinden birini kasteder.

Bu kılavuz her varyasyonun promptunu nasıl oluşturacağını anlatır. Kullanıcı, seçilen modelde kazanan reklam görselini marka ve kalite referansı olarak, 1 ila 3 ürün görselini de yanına yükleyecek. Promptun, görsel modele ne üretmesi gerektiğini söyleyen metin talimatıdır.

Bu, yeniden inşa promptundan farklıdır. Yeniden inşada referans görsel klonlanacak bir düzen şablonudur. Çoğaltma varyasyonunda ise referans görsel bir marka ve kalite referansıdır; prompt dönüşüm mekaniğini korurken görsel olarak bilinçli biçimde ondan uzaklaşır.

---

## Çoğaltıcı 2.0'da Referans Görsel Promptları Nasıl Çalışır

Görsel model yüklenen görselleri iki rolde kullanır:

1. **Kazanan reklam görseli** marka kimliği, estetik kalite ve yapısal iskelet referansıdır. Görsel modele bu işin hangi marka dünyasında yaşadığını ve hangi prodüksiyon kalite çıtasına ulaşılacağını anlatır.

2. **Ürün görselleri** ürün için hakikatin kaynağıdır. Görsel model, ürünü kazanan reklamın ürün tasvirinden değil, bu görsellerden yola çıkarak doğru biçimde render etmelidir.

Metin promptun görsel modele şunları söylediği yerdir:
- Kazanan reklam referansının marka ve kalitesini onurlandır
- Ürünü ürün görsellerinden render et
- Varyasyonun YENİ görsel sahnesi, renk dünyası ve metnini kullan
- Yapısal iskeleti koru (düzen bölgeleri, metin hiyerarşisi)
- Dönüşüm mekaniği öğesini koru (referans / iddia / demo / yaşam tarzı / vb.)

---

## Prompt Yapısı

Her varyasyonun promptunu tam olarak bu sırayla oluştur.

---

### BÖLÜM 1, REFERANS TALİMATI

Görsel modele yüklenen görsellere nasıl davranması gerektiğini söyleyen tek bir cümleyle aç:

> "Use the first uploaded image as the brand identity and production quality reference. Match the brand colors, typography style, and overall production polish. Use the additional uploaded image(s) as the source of truth for the product itself. Do not clone the layout or scene of the reference ad. Build a new ad as specified below, preserving the structural skeleton and conversion mechanic but with a genuinely different visual scene."

---

### BÖLÜM 2, YAPISAL İSKELET (orijinalden korunmuş)

Aşama 1'den çıkarılan yapısal deseni kilitle. Örnek:

> "Maintain this layout structure: [yapısal iskeletin açıklamasını analizden buraya yaz, örn. 'top 60% is product on lifestyle background, bottom 40% is dark text block with white headline, logo bottom right']. Keep the same text hierarchy and proportional relationships."

Bu her varyasyon boyunca tutarlı kalır.

---

### BÖLÜM 3, GÖRSEL SAHNE (varyasyon başına benzersiz)

Her varyasyonun ayrıştığı yer burasıdır. Şu konularda spesifik ol:

- **Mekan/ortam:** Kesin konum ve bağlam. Örnek: "a sun-drenched kitchen with marble countertops and herbs in small terracotta pots near the window"
- **Aydınlatma:** Spesifik kalite ve yön. Örnek: "warm morning light from a window left of frame, golden tone, soft shadows"
- **Renk dünyası:** Baskın palet. Örnek: "warm whites, sage green, terracotta, no cool tones"
- **Yüzey/aksesuarlar:** Ürünün üzerinde durduğu veya çevresinde bulunduğu şeyler
- **Kamera işlemi:** Mesafe, açı, ilgili yerlerde alan derinliği. Örnek: "shot on 35mm at f/2.0, slight depth of field"
- **İnsan öğesi:** Biri var mı? Varsa demografik bilgi, beden dili, ifade. Yoksa "no human in frame" belirt

Bu bölüm Andromeda varyasyonunun özüdür. Her varyasyon burada net biçimde farklı okunmalıdır.

---

### BÖLÜM 4, ÜRÜN ENTEGRASYONU

Görsel modele bu varyasyonda ürünü nasıl render edeceğini söyle:

> "Render the product from the uploaded product image(s). Place it in the scene as follows: [hero on the surface / held by the person / in mid-use / flatlay among complementary objects / etc.]. The product should be [scale relative to frame] and [angle/orientation]. Maintain accurate product details from the uploaded product image(s). Lighting on the product should match the scene's overall lighting (warm/cool/clinical/etc.)."

Ürün konumlandırma stili varyasyonlar arasında farklılık gösterebilir (bir varyasyon hero, bir diğeri kullanım sırasında, bir diğeri elle tutulmuş) ancak Bölüm 2'deki yapısal iskelet korunduğu sürece.

---

### BÖLÜM 5, DÖNÜŞÜM MEKANİĞİ ÖĞESİ (orijinalden korunmuş)

Her varyasyon, orijinal reklamın dönüşüm mekaniğinin bağlı olduğu yapısal öğeyi içermelidir. Analizi referans al. Örnek ifadeler:

Referans odaklı orijinaller için:
> "Include a testimonial element: a short customer quote of [target word count] words rendered in [white/dark] text overlay, attributed to '[Name], [Credential]'. Five filled [brand color] stars beside or below the quote."

İddia odaklı orijinaller için:
> "Include a specific claim element: a bold falsifiable result rendered as the headline focal point. Example structure: '[NUMBER]% [OUTCOME]' or '[RESULT] in [TIMEFRAME]'."

Yaşam tarzı odaklı orijinaller için:
> "Lead with the lifestyle moment. The product is part of the scene, not the hero. The viewer should feel the moment first, see the product second."

Demo odaklı orijinaller için:
> "Show the product in use or with its mechanism visible. The viewer must understand how it works from the image alone."

Dili orijinalin spesifik mekaniğiyle eşleşecek biçimde uyarla.

---

### BÖLÜM 6, METİN DEĞİŞİMLERİ

Her metin öğesi için tam değiştirme metnini yaz.

**Kelime sayısı rehberi:** Orijinal reklamın kelime sayılarını görsel denge için referans olarak kullan. Mümkün olduğunda eşleştir (başlıklarda artı veya eksi 2 kelime, harekete geçirici mesajlarda ve rozette artı veya eksi 1 kelime). Kelime uzunluğunu açıyı feda edecek kadar kilitleme. Tüm amaç varyasyondur.

**Her metin öğesi için format:**

> "HEADLINE: '[BURAYA TAM BAŞLIĞINI YAZ]' (hedef kelime sayısı: [X kelime], orijinal [Y kelime] idi).
> [bold sans-serif / referans görüntüdeki marka tipografisiyle eşleşen] olarak render et. Konum: [üst / merkez / alt], [sol / merkez / sağ]. Renk: [beyaz / koyu / marka rengi]."

> "SUBHEADLINE: '[BURAYA TAM ALT BAŞLIĞINI YAZ]' (hedef kelime sayısı: [X kelime]).
> Başlıktan küçük, varyasyon kontrast gerektirmedikçe aynı renk işlemi."

> "BODY COPY: '[BURAYA TAM GÖVDE METNİNİ YAZ]' (hedef satır sayısı: [X satır], hedef kelime sayısı: yaklaşık [X kelime]).
> Orijinalle aynı yaklaşık metin bloku boyutlarını koru."

> "CTA: '[BURAYA TAM HGPM'İNİ YAZ]' (hedef kelime sayısı: [X kelime]).
> [Buton stili / düz metin / rozet stili], [konum]."

> "BADGE/CALLOUT: '[BURAYA TAM ROZETİNİ YAZ]' (hedef kelime sayısı: [X kelime], varyasyon içeriyorsa)."

**Değiştirme metnini yazma kuralları:**

- **Mümkün olan her yerde VOC belgesinden birebir müşteri dilini kullan.** Gerçek ifadeler çek, uydurma metin değil.
- **Bu varyasyonun kanca mekaniğiyle eşleş, orijinalinkiyle değil.** Her varyasyonun farklı bir kancası var. O kancanın mantığı içinde yaşayan metin yaz.
- **Bu varyasyonun farkındalık düzeyiyle eşleş.** Sorun-Farkında varyasyon ürün adını anmaz. En-Farkında varyasyon fiyat veya aciliyetle başlayabilir.
- **Markanın tonuyla eşleş.** Sıradan sıradan kalır. Klinik klinik kalır. Marka DNA'sını kontrol et.
- **İki varyasyon arasında asla aynı başlık veya anahtar ifadeyi tekrarlama.** Her varyasyonun ana metninin özgün olması şart.

---

### BÖLÜM 6b, KAMPANYA VEYA TEKLİF KATMANI (kullanıcı sağladıysa)

Kullanıcı "tüm varyasyonlar" dediyse teklifi her prompta ekle. "Karışık" dediyse yaklaşık yarısına ekle (En-Farkında, Ürün-Farkında veya Çözüm-Farkında kitleleri hedefleyen varyasyonlar).

**Varyasyon teklif içeriyorsa:**

Harekete geçirici mesaj varsa, teklif oraya gider:
> "CTA: '[TEKLİF ODAKLI HGPM, örn. Get 20% Off / Claim Free Trial / Shop the Sale]'."

Rozet veya çağrı yeri varsa:
> "Badge: '[TEKLİF METNİ, örn. Limited Time / 20% Off This Week / Free Shipping]'."

Teklif başlık açısını değiştiriyorsa:
> "Headline: '[TEKLİF AÇILI BAŞLIK, örn. Finally Clear Skin, Now 20% Off]'."

**Teklif entegrasyon kuralları:**
- Teklif gerçek olmalı, kullanıcının tam olarak tarif ettiğini kullan
- Yapısal iskelette mevcut olmayan bir yere teklifi zorla sıkıştırma
- Teklif, içinde bulunduğu öğe için kelime sayısı kılavuzuna (artı veya eksi 1 kelime) uymalı

---

### BÖLÜM 7, MARKA KİMLİĞİ KİLİDİ

Her varyasyon marka uyumlu kalmalı. Marka DNA'sını referans al:

> "Brand colors: [birincil hex], [ikincil hex], [aksan hex]. Apply these to text, graphic elements, and any color-coded zones. Brand logo: place [bottom right / bottom center / analizden konumu] in [white / brand color]. Typography style: match the reference image's typography family (sans-serif, weight, character). Overall production quality: match the polish of the reference image."

Bu bölüm her varyasyon boyunca aynıdır.

---

### BÖLÜM 8, KALİTE TALİMATI

Tek bir kalite direktifiyle kapat:

> "The output should look like a polished, production-ready static Meta ad. All text must be sharp, legible, and correctly spelled. Product details must match the uploaded product image accurately. The scene should feel intentional, not stock or generic. The ad should look distinctly different from the reference ad in scene, color world, and composition while still feeling unmistakably from the same brand."

---

## Prompt Uzunluğu ve Formatı

Her tamamlanmış prompt 250 ila 450 kelime olmalıdır. Yeterince kesin olmak için uzun, görsel model tarafından temiz işlenebilmek için kısa.

Açık, doğrudan talimat diliyle yaz. Promptun içinde madde işaretleri yok. Görsel modelin bir direktif olarak okuduğu akıcı talimatlar olarak yaz. Süslü dilden kaçın. Cerrahi ol.

---

## Belgelerden Metni Nasıl Çıkaracaksın

### Marka DNA'sı belgesinden çıkar:
- Marka adı ve ürün adı
- Temel ürün konumlandırma ifadesi
- Temel ürün faydaları (markanın dilinde)
- Marka görsel kimliği (renkler, yazı tipi stili, estetik)
- Ses tonu tanımlayıcıları
- Markanın tutarlı biçimde kullandığı spesifik ifade veya dil

### VOC belgesinden çıkar:
- BU varyasyonun kanca mekaniğiyle eşleşen en duygusal acı noktası
- Bu varyasyonun açısı için en güçlü istek/hayal edilen sonuç ifadeleri
- Önce/sonra dil çiftleri (özellikle dönüşüm kancaları için)
- Dil Hazinesinden yüksek yoğunluklu ifadeler
- Bu varyasyonun farkındalık düzeyiyle eşleşen kimlik dili
- Referans tarzı varyasyonlar için: Sosyal Kanıt Cephaneliğinden gerçek alıntılar

### Kanca mekaniğini VOC bölümüyle eşleştirme:
- Cesur sonuç / dönüşüm kancası → Sonrası-Durum Görsel Tanımlamaları ve Önce/Sonra çiftleri
- Sorun-ajitasyon kancası → en iyi acı noktaları ve zorluk anı dili
- Merak boşluğu kancası → "Keşke" ve karşılanmamış istek dili
- İlişkilendirilebilirlik kancası → kimlik dili ve durum açıklamaları
- Sosyal kanıt kancası → Sosyal Kanıt Cephaneliğinden en iyi referanslar
- Doğrudan teklif kancası → Değer Denklemi dili, Hayal Edilen Sonuç artı Zaman Gecikmesi
- Özlem kancası → kimlik odaklı istek dili ve gelecekteki-benlik ifadeleri

---

## Her Varyasyon Promptunu Sonlandırmadan Önce Öz-Kontrol

Her varyasyonun promptunu çıkarmadan önce şunları doğrula:

- [ ] Bölüm 1'deki referans talimatı görsel modele kazanan reklam görselini klonlanacak düzen değil, marka ve kalite referansı olarak kullanmasını söylüyor
- [ ] Ürün, kullanıcının yüklediği ürün görselinden render ediliyor, referans reklamdan değil
- [ ] Orijinalin yapısal iskeleti korunuyor
- [ ] Dönüşüm mekaniği öğesi korunuyor (referans / iddia / demo / yaşam tarzı / vb.)
- [ ] Görsel sahne orijinalden VE her diğer varyasyondan gerçek anlamda farklı
- [ ] Renk dünyası orijinalden VE her diğer varyasyondan gerçek anlamda farklı
- [ ] Tüm metin öğelerinin tam değiştirme metni yazılmış, yer tutucu yok
- [ ] Başlık kelime sayısı orijinalin artı veya eksi 2 kelimesi içinde
- [ ] Harekete geçirici mesaj kelime sayısı orijinalin artı veya eksi 1 kelimesi içinde
- [ ] Tüm değiştirme metni Marka DNA'sı veya VOC'dan alınmış, genel ifade yok
- [ ] Bu varyasyonun kanca mekaniği her diğer varyasyondan ayrı
- [ ] Bu varyasyonun farkındalık düzeyi kanca için uygun
- [ ] Bu varyasyon için bir teklif belirlenmişse temiz biçimde entegre edilmiş
- [ ] Prompt eksiksiz, bağımsız bir direktif olarak okunuyor; kullanıcı sıfır düzenlemeyle kopyalayıp yapıştırabilir

---

## Tüm Varyasyonlar Genelinde Öz-Kontrol (son çıktıdan önce çalıştır)

Tüm promptları yazdıktan sonra tam seti denetle:

- [ ] Her varyasyon diğer her varyasyondan VE orijinalden farklı bir görsel sahne kullanıyor
- [ ] Her varyasyon diğer her varyasyondan VE orijinalden farklı bir renk dünyası kullanıyor
- [ ] Her varyasyon diğer her varyasyondan farklı bir kanca mekaniği kullanıyor
- [ ] Farkındalık düzeyleri en az 3 aşamaya yayılmış
- [ ] İki varyasyon aynı başlığı veya ana ifadeyi paylaşmıyor
- [ ] Her varyasyon orijinalin dönüşüm mekaniğini onurlandırıyor
- [ ] Tüm varyasyonlar Marka DNA'sına göre marka uyumlu kalıyor
- [ ] Teklif için "karışık" belirtilmişse, teklif yaklaşık yarı varyasyonda görünüyor, daha yüksek farkındalık düzeylerine ağırlık verilerek

Herhangi bir kontrol başarısız olursa, son çıktıyı kullanıcıya sunmadan önce düzelt.
