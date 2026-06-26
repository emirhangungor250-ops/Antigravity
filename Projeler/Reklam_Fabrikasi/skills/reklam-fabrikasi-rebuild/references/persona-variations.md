# Persona Varyasyonları, 5 Alıcı Persona Yeniden İnşa Promptu

Kullanıcı persona varyasyonları istediğinde, 5 tam referans görsel promptu üret. Promptlar model agnostiktir; hem GPT Image 2 (eklentinin önerilen varsayılanı) hem de Nano Banana 2 (daha ucuz alternatif) ile çalışır. Her varyasyon, VOC belgesinden alınan farklı bir alıcı personayı hedefler.

---

## Varyasyonlar Arasında Neyin Değişeceği

**Her varyasyonda aynı kalır:**
- Orijinal reklamın tam düzeni ve kompozisyonel yapısı
- Görsel bölgeler, metin yerleşim konumları, hiyerarşi
- Ürün görsel değiştirme (her promptta aynı talimat)
- Marka rengi ve kimlik değiştirmeleri (her promptta aynı)
- Kampanya veya teklif katmanı: kullanıcı bir teklif sağladıysa, 5 varyasyonun hepsinde aynı şekilde görünür
- Görsel stil ve işlem
- Koru talimatları

**Her varyasyonda değişir:**
- Başlık: farklı açı, farklı acı noktası veya istek, farklı duygusal tetikleyici
- Alt başlık: yeni başlık açısını destekler
- Gövde metni: personayla eşleşen farklı müşteri dili
- HGPM: persona farklı bir farkındalık düzeyindeyse hafifçe değişebilir
- Kanca mekaniği: farklı varyasyonlar farklı kanca tipleri kullanabilir

---

## 5 Personayı Nasıl Belirleyeceksin

Personaları doğrudan VOC belgesinden çek. Şunları ara:

1. **Farkındalık Düzeyi boyutu**: veride bulunan Schwartz farkındalığının farklı aşamaları. Bir persona sorun-farkında, bir diğeri çözüm-farkında, bir diğeri en-farkında olabilir.

2. **Acı Noktası boyutu**: VOC 6 ila 10 ayrı acı noktası ortaya çıkaracak. En yüksek frekans ve yoğunluğa sahip 3 ila 5 tanesini persona çıpası olarak seç.

3. **Kimlik boyutu**: ICP bölümü ve Dil Hazinesindeki kimlik dili farklı öz-tanımlamaları ortaya koyacak. "Meşgul ebeveyn", "fitness yeni başlayanı", "daha fazla enerji isteyen profesyonel" vb. persona çıpalarıdır.

4. **İstek boyutu**: arzular bölümünde bulunan farklı hayal edilen sonuçlar. Bir persona kendinden emin hissetmek ister, bir diğeri zaman kazanmak ister, bir diğeri başkalarını etkilemek ister.

5. **JTBD boyutu**: fonksiyonel iş, duygusal iş ve sosyal iş alıcıları aynı ürün için bile anlamlı biçimde farklı personalar oluşturur.

VOC 5 açıkça farklı persona içermiyorsa, yukarıdaki boyutların kombinasyonlarından oluştur. Her birini her zaman gerçek VOC diline dayandır.

---

## Persona Etiket Formatı

Prompttan önce her varyasyonu açıkça etiketle:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VARİYASYON 1, [Kısa persona açıklaması]
Farkındalık Düzeyi: [Habersiz / Sorun-Farkında / Çözüm-Farkında / Ürün-Farkında / En-Farkında]
Kanca Mekaniği: [tip]
Etkinleştirilen Birincil Duygu: [duygu]
VOC Kaynağı: [bu personanın dayandığı alıntı veya bölüm]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Tam prompt buraya]
```

Persona açıklaması kısa, spesifik bir etiket olmalıdır, genel bir demografik bilgi değil. İyi: "Her şeyi denemiş yorgun anne" / "Fiyat kaygısı olan ilk alıcı" / "Kategoriyi zaten biliyor, geçmek için bir neden arıyor." Kötü: "Kadın, 25-45, sağlıkla ilgileniyor."

---

## 5 Varyasyon Promptunu Yazma

Her prompt, `references/prompt-builder.md` içindeki ana yeniden inşa promptuyla aynı yapıyı izler:

1. Referans talimatı (5'in tamamında aynı)
2. Marka kimliği değiştirmeleri (5'in tamamında aynı)
3. Ürün görsel değiştirme (5'in tamamında aynı)
4. Metin değiştirmeleri, VARYASYONLARIN AYRILDIĞI YER BURASI
5. Koru talimatları (5'in tamamında aynı)
6. Kalite talimatı (5'in tamamında aynı)

Yalnızca Bölüm 4 (metin değiştirmeleri) değişir. Her şey diğeri taban prompttan kopyalanır.

---

## Her Varyasyon İçin Metin Yazma

Her persona için bu süreci izle:

**Adım 1, Personanın baskın duygusal durumunu belirle**
Şu anda ne hissediyorlar? Sinirli mi? Umutlu mu? Şüpheci mi? Çaresiz mi? Özlemli mi? Bu, metnin duygusal kaydını belirler.

**Adım 2, Eşleşen kanca mekaniğini seç**
- Sinirli / mahsur → Sorun-ajitasyon kancası
- Umutlu / motive → Özlem / dönüşüm kancası
- Şüpheci → Şüpheciden-inandırıcıya / sosyal kanıt kancası
- Çaresiz / acil → Korku/kayıp kancası
- Özlemli → Kimlik / istek kancası
- Almaya hazır → Doğrudan teklif / cesur iddia kancası

**Adım 3, VOC'dan tam müşteri dilini çek**
Bu personayla eşleşen VOC'un spesifik bölümüne git:
- Acı noktası personaları → Bölüm 4 (Acı Noktaları) ve 13 (Dil Hazinesi, sorun dili)
- İstek personaları → Bölüm 5 (İstekler) ve 13 (Dil Hazinesi, çözüm dili)
- Kimlik personaları → Bölüm 2 (ICP) ve Bölüm 13 (kimlik dili)
- Farkındalık düzeyi personaları → Bölüm 8 (Farkındalık Düzeyi Derin Dalış)
- Şüpheci personalar → Bölüm 14 (Sosyal Kanıt Cephaneliği, Şüpheciden-İnandırıcıya alıntılar)

**Adım 4, Başlığı yaz**
Orijinal kelime sayısını tam olarak eşleştir (maksimum artı veya eksi 1 kelime). Bu her tek varyasyona uygulanır. VOC müşteri dilini kullan. Personanın temel duygu/istek/acısını başlığın tam yapısına sıkıştır. Dili hedef kelime sayısına sığdıramazsan, daha sert sıkıştır. Bütçeyi aşma.

**Adım 5, Destekleyici metin yaz**
Alt başlık, gövde metni, HGPM ve rozet hepsi orijinal kelime sayılarıyla eşleşir (maksimum artı veya eksi 1 kelime). Kelime sayısı disiplini her varyasyondaki her metin öğesine uygulanır, yalnızca başlığa değil. VOC dil kaydını koru. Öğeler arasında ton değiştirme.

**Adım 6, Farkındalık düzeyi farklıysa HGPM'i ayarla**
- Habersiz / Sorun-Farkında: yumuşak HGPM: "See How It Works" / "Learn More" / "Discover"
- Çözüm-Farkında: orta HGPM: "See [Marka Adı]" / "Find Out More"
- Ürün-Farkında / En-Farkında: doğrudan HGPM: "Shop Now" / "Get Yours" / "Claim Offer"

HGPM ifadesi farkındalık düzeyine göre değişebilir ama kelime sayısı yine de orijinal HGPM'in kelime sayısıyla eşleşmelidir. Orijinal HGPM 2 kelimeyse, her varyasyonun HGPM'i 2 kelimedir.

---

## Varyasyonlar İçin Kalite Kontrolü

5 varyasyonun tamamını çıkarmadan önce şunları doğrula:

- [ ] 5 personanın tamamı anlamlı biçimde farklı. Farklı duygusal kayıt, farklı açı, farklı kanca mekaniği.
- [ ] Her persona etiketi spesifik bir VOC kaynağını alıntılıyor
- [ ] Her başlık orijinal kelime sayısıyla eşleşiyor (1 kelime içinde). 5'in tamamı için sayıldı ve onaylandı.
- [ ] Her alt başlık orijinal kelime sayısıyla eşleşiyor (1 kelime içinde). 5'in tamamı için sayıldı ve onaylandı.
- [ ] Her HGPM orijinal kelime sayısıyla eşleşiyor (1 kelime içinde). 5'in tamamı için sayıldı ve onaylandı.
- [ ] Her rozet/çağrı (varsa) orijinal kelime sayısıyla eşleşiyor (1 kelime içinde). 5'in tamamı için sayıldı ve onaylandı.
- [ ] Tüm gövde metni orijinal satır sayısı ve yaklaşık kelime sayısıyla eşleşiyor. 5'in tamamı için sayıldı ve onaylandı.
- [ ] Tüm metin VOC dilinde temelleniyor. İki varyasyon aynı ifadeleri kullanmıyor.
- [ ] Her prompt tam bağımsız. Diğer varyasyonlara çapraz referans yok.
- [ ] HGPM'ler farkındalık düzeyine göre uygun şekilde değişiyor ama yine de kelime sayısı kuralına uyuyor.
- [ ] Marka kimliği ve düzen bölümleri 5'in tamamında aynı
