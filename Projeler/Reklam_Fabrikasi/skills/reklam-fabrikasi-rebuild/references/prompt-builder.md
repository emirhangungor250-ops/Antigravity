# Prompt Oluşturucu, Referans Görsel Promptu

Bu kılavuzun ürettiği prompt model agnostiktir. Hem GPT Image 2 (eklentinin yüksek kalitede ve 4K eşdeğeri `image_size` ile önerilen varsayılanı) hem de Nano Banana 2 (daha ucuz alternatif) için temiz biçimde yapıştırılabilir. Aşağıdaki metin "görsel model" der; bu, `reklam-fabrikasi-rebuild` içindeki model seçici adımında kullanıcının seçtiği ikisinden birini kasteder.

Bu kılavuz yeniden inşa promptunu nasıl oluşturacağını anlatır. Kullanıcı rakip reklam görselini seçilen modelde referans görsel olarak, ürün görselini de yanına yükleyecek. Promptun, görsel modele neyi değiştireceğini ve neyi koruyacağını söyleyen metin talimatıdır.

---

## Referans Görsel Promptları Nasıl Çalışır

Görsel model, yüklenen referans görseli yapısal ve kompozisyonel bir şablon olarak kullanır. Ne değiştireceğini anlamak için metin promptunu okur. Senin işin:

1. Düzeni kilitle: görsel modele orijinal kompozisyonu korumasını söyle
2. Her görsel değiştirmeyi belirt: ürün, renkler, marka öğeleri
3. Her metin değiştirmesini önceden yaz: görsel modele kullanılacak tam kelimeleri ver
4. Görsel modele asla karar bırakma: belirtmezsen, görsel model hayal gücüyle hareket eder

---

## Prompt Yapısı

Promptu tam olarak bu sırayla oluştur:

---

### BÖLÜM 1, REFERANS TALİMATI

Görsel modele yüklenen görsele nasıl davranması gerektiğini söyleyen tek bir cümleyle aç:

> "Use the uploaded image as the compositional reference. Preserve the exact layout, visual zones, text placement positions, and overall structure. Do not redesign, only replace the specific elements listed below."

---

### BÖLÜM 2, MARKA KİMLİĞİ DEĞİŞİMLERİ

Marka DNA'sı belgesinden çek. Her marka düzeyindeki görsel değişikliği listele:

**Format:**
> "Replace the brand colour palette with: [birincil renk hex], [ikincil renk hex], [aksan renk hex]. Apply these to backgrounds, text elements, and graphic shapes."
>
> "Replace any logo or brand name visible in the ad with: [marka adı] in [Marka DNA'sında belirtilmişse marka yazı tipi stili, aksi takdirde: clean sans-serif]."
>
> "Maintain the overall colour mood/temperature as [warm/cool/neutral], shift the palette toward [Marka DNA'sından marka paleti açıklaması]."

---

### BÖLÜM 3, ÜRÜN GÖRSEL DEĞİŞİMİ

Kullanıcı ürün görselini görsel modele ayrıca yüklüyor. Talimatı yaz:

> "Replace the product in the reference image with the second uploaded product image. Place the product in the same position and at the same scale as the original product in the reference. Maintain the same angle and orientation if possible. [Marka DNA'sından varsa spesifik ürün bağlamı ekle, örn. 'The product is a glass bottle with a gold cap', böylece görsel model doğru render eder.]"

Orijinalde yaşam tarzı bağlamı varsa (ürün tutulmuş, ürün bir sahnede), belirt:
> "Keep the [lifestyle element / background scene] from the reference image. Integrate the new product into this scene naturally."

---

### BÖLÜM 4, METİN DEĞİŞİMLERİ

Bu en kritik bölümdür. Reklam analizinde tanımlanan her metin öğesi için tam değiştirmeyi yaz.

#### KELİME SAYISI KURALI (her seferinde önce bunu oku)

Her değiştirme metin öğesi, o öğenin orijinal kelime sayısıyla mümkün olduğunca yakın eşleşmelidir. Bu pazarlık konusu değildir.

Kabul edilebilir tolerans maksimum artı veya eksi 1 kelimedir. 4 kelimelik başlık, 3, 4 veya 5 kelimelik başlığa dönüşür. Asla 7 kelimelik başlık. Asla 2 kelimelik başlık. Aynı kural alt başlık, HGPM, rozet, çağrı, gövde metninin satır sayısı ve reklamdaki her metin öğesi için geçerlidir.

Sebebi: orijinal reklamın görsel dengesi, metin bloku boyutları ve okuma ritmi onun dönüşüm sağlamasının parçasıdır. 4 kelimelik başlığın yerine 9 kelimelik başlık yazarsan, reklamın görsel hiyerarşisi çöker, başlık bölgesini taşar ve yeni reklam kazanan reklam gibi ne görünür ne de performans gösterir.

Herhangi bir değiştirme metnini yazmadan önce, reklam analizine bak ve her metin öğesinin tam kelime sayısını yaz. Ardından o kelime sayılarıyla eşleşen metin yaz. Müşteri dilini hedef kelime sayısına sığdıramazsan, daha sert sıkıştır. Daha kısa kelimeler kullan. Dolgu kes. Kelime sayısı kısıttır, öneri değil.

**Her metin öğesi için format (promptun kendisinde her zaman hedef kelime sayısını dahil et):**

> "HEADLINE: Replace the headline text with: '[BURAYA TAM BAŞLIĞINI YAZ]' (target word count: [X words], matching the original).
> Keep the same font weight (bold), same font size relative to the image, same position ([top/centre/bottom], [left/centre/right]), same colour treatment ([white text / dark text / coloured text as in original])."

> "SUBHEADLINE: Replace the subheadline with: '[BURAYA TAM ALT BAŞLIĞINI YAZ]' (target word count: [X words], matching the original).
> Same size, position, and colour as original."

> "BODY COPY: Replace the body text with: '[BURAYA TAM GÖVDE METNİNİ YAZ]' (target line count: [X lines], target word count: approximately [X words], matching the original).
> Maintain the same approximate line count ([X lines]) and text block dimensions."

> "CTA: Replace the CTA text with: '[BURAYA TAM HGPM'İNİ YAZ]' (target word count: [X words], matching the original).
> Keep the same button/text style, colour, and position."

> "BADGE/CALLOUT: Replace the badge text with: '[BURAYA TAM ROZETİNİ YAZ]' (target word count: [X words], matching the original).
> Keep the same position and style."

**Değiştirme metnini yazma kuralları:**

- **Kelime sayısı eşleşmesi her zaman ilk kuraldır.** Her öğede maksimum artı veya eksi 1 kelime. Sonlandırmadan önce sayarak her öğeyi doğrula.
- **Mümkün olan her yerde VOC belgesinden birebir müşteri dilini kullan.** Gerçek ifadeler çek, uydurma metin değil.
- **Kanca mekaniğini orijinaliyle hizala.** Orijinal cesur bir sonuç iddiası kullandıysa, senin değiştirmen de cesur bir sonuç iddiası kullanır, yalnızca bu markanın ürünü için. Bir sorun kancası kullandıysa, seninki de bir sorun kancası kullanır.
- **Tonu eşleştir.** Sıradan = sıradan. Klinik = klinik. Marka DNA'sı ses tonunu kontrol et.
- **Başlık için:** VOC belgesinden orijinalin kanca mekaniğiyle eşleşen tek en güçlü acı noktasını veya isteği çıkar. Orijinal kelime sayısına sıkıştır, sıfatları kesmek veya ifadeyi basitleştirmek zorunda kalsan bile.
- **Gövde metni için:** VOC belgesinden özellik-fayda dilini ve müşteri ifadelerini kullan. Orijinalin satır sayısını ve yaklaşık kelime sayısını eşleştir. Genel reklam metni yazma.
- **HGPM için:** Orijinal HGPM tipini eşleştir (keşif HGPM'i "Daha Fazla Bilgi" / taahhüt HGPM'i "Şimdi Al" / yumuşak HGPM "Nasıl Olduğunu Gör" gibi). Tam kelime sayısını eşleştir. Marka DNA'sı belgesinde markanın tercih ettiği HGPM dilini kontrol et.

---

### BÖLÜM 4b, KAMPANYA VEYA TEKLİF KATMANI (yalnızca kullanıcı sağladıysa)

Kullanıcı bir kampanya, indirim, promosyon veya belirli teklif belirttiyse, reklamı şöyle yere işle:

**Orijinal reklamda bir HGPM butonu veya rozeti varsa**, bu teklifi enjekte etmek için birincil yerdir:
> "CTA: Replace the CTA with: '[TEKLİF ODAKLI HGPM, örn. "Get 20% Off", "Claim Free Trial", "Shop the Sale"]'. Keep the same button style, colour, and position."

**Orijinal reklamda bir rozet, etiket veya çağrı öğesi varsa**, teklif için kullan:
> "Badge/Label: Replace with: '[TEKLİF METNİ, örn. "Limited Time", "20% Off This Week", "Free Shipping"]'. Keep the same position and style."

**Teklif reklamın vaadini değiştiriyorsa** (örn. başlık açısını etkileyecek bir lansman anlaşmasıysa), başlığa yansıt:
> "Adjust the headline to incorporate the offer: '[TEKLİF AÇILI BAŞLIK, örn. "Finally Clear Skin, Now 20% Off"]'. Match the original word count as closely as possible."

**Teklif sağlanmadıysa**, bu bölümü tamamen atla. Genel bir teklif ekleme veya promosyon uydurma.

**Teklif entegrasyon kuralları:**
- Teklif gerçek olmalı. Kullanıcının tarif ettiğini tam olarak kullan, parafraz değil
- Orijinal reklamın düzeninde mevcut olmayan bir yere teklifi zorla sıkıştırma
- Orijinal reklamda rozet/çağrı öğesi yoksa, teklifi yalnızca HGPM'e enjekte et
- Teklif yine de kelime sayısı kuralına uymalı. Değiştirdiği öğenin kelime sayısını eşleştir, maksimum artı veya eksi 1 kelime

Promptu açık bırakma talimatlarıyla bitir:

> "Keep the following elements exactly as they appear in the reference image:
> - Overall layout and compositional zones
> - Text placement positions and hierarchy
> - Background style and atmosphere [unless colour swap specified above]
> - Visual style and image treatment
> - Any graphic elements not listed above for replacement"

---

### BÖLÜM 6, KALİTE TALİMATI

Tek bir kalite direktifiyle kapat:

> "The output should look like a polished, production-ready static Meta ad. All text must be sharp, legible, and correctly spelled. Brand elements should feel cohesive and intentional."

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
- Orijinal reklamın kanca mekaniğiyle eşleşen en duygusal acı noktası
- En güçlü istek/hayal edilen sonuç ifadeleri
- Önce/sonra dil çiftleri
- Dil Hazinesi bölümünden yüksek yoğunluklu ifadeler
- Orijinal reklamın izleyici düzeyiyle eşleşen kimlik dili
- Baskın farkındalık düzeyi, buna uygun dil kullan

### Kanca mekaniğini VOC bölümüyle eşleştirme:
- Cesur sonuç / dönüşüm kancası → VOC'dan Sonrası-Durum Görsel Tanımlamaları + Önce/Sonra çiftleri kullan
- Sorun-ajitasyon kancası → JTBD bölümünden en iyi acı noktaları + zorluk anı dilini kullan
- Merak boşluğu kancası → Dil Hazinesinden "Keşke" ve karşılanmamış istek dilini kullan
- İlişkilendirilebilirlik kancası → ICP bölümünden kimlik dili + durum açıklamaları kullan
- Sosyal kanıt kancası → Sosyal Kanıt Cephaneliğinden en iyi referansları kullan
- Doğrudan teklif kancası → Değer Denklemi dilini kullan, Hayal Edilen Sonuç + Zaman Gecikmesi

---

## Prompt Uzunluğu ve Formatı

Tamamlanan prompt 200 ila 400 kelime olmalıdır. Yeterince kesin olmak için uzun, görsel model tarafından temiz işlenebilmek için kısa.

Açık, doğrudan talimat diliyle yaz. Promptun içinde madde işaretleri yok. Görsel modelin bir direktif olarak okuduğu akıcı talimatlar olarak yaz. Süslü dilden kaçın. Cerrahi ol.

---

## Sonlandırmadan Önce Öz-Kontrol

Promptu çıkarmadan önce şunları doğrula:

- [ ] Reklam analizindeki her metin öğesinin tam değiştirmesi yazılmış. Yer tutucu yok.
- [ ] Değiştirme başlığı orijinal kelime sayısıyla eşleşiyor (1 kelime içinde). Sayıldı ve onaylandı.
- [ ] Değiştirme alt başlığı orijinal kelime sayısıyla eşleşiyor (1 kelime içinde). Sayıldı ve onaylandı.
- [ ] Değiştirme HGPM'i orijinal kelime sayısıyla eşleşiyor (1 kelime içinde). Sayıldı ve onaylandı.
- [ ] Değiştirme rozet/çağrı (varsa) orijinal kelime sayısıyla eşleşiyor (1 kelime içinde). Sayıldı ve onaylandı.
- [ ] Gövde metni orijinal satır sayısı ve yaklaşık kelime sayısıyla eşleşiyor (yüzde 10 içinde). Sayıldı ve onaylandı.
- [ ] Prompttaki her metin öğesi talimatı hedef kelime sayısını içeriyor, böylece görsel model kısıtı görüyor.
- [ ] Tüm değiştirme metni Marka DNA'sı veya VOC'dan alınmış. Uydurma genel ifade yok.
- [ ] Ürün değiştirme talimatı kullanıcının yüklediği ürün görselini referans alıyor
- [ ] Marka rengi değiştirmeleri Marka DNA'sı belgesinden spesifik değerleri referans alıyor
- [ ] Koru talimatı değişmeden kalması gereken her şeyi listeliyor
- [ ] Prompt eksiksiz, bağımsız bir direktif olarak okunuyor. Kullanıcı sıfır düzenlemeyle kopyalayıp yapıştırabilir.
