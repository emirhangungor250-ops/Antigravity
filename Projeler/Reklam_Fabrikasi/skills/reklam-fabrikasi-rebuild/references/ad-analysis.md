# Reklam Analiz Çerçevesi, Rakip Reklam Dökümü

Rakip reklam görselini aldığında aşağıdaki her öğeyi analiz et. Kesin ve spesifik ol. Bu analiz doğrudan yeniden inşa promptuna beslenir. Belirsiz gözlemler belirsiz promptlar üretir.

---

## 1. DÜZEN VE KOMPOZİSYON

- **Format:** Yaklaşık boyutlar ne? Kare (1:1), dikey (4:5 veya 9:16), yatay (1.91:1)?
- **Görsel bölgeler:** Görsel nasıl bölünmüş? Bölgeleri açıkla, örn. "üst %60 ürün görseli, alt %40 koyu arka planda metin bloğu"
- **Baskın odak noktası:** Göz ilk nereye iniyor? Ürün? Yüz? Başlık metni?
- **Metin yerleşimi:** Her metin öğesi nerede oturuyor? (sol üst, merkezde, alt üst katman, ürünün yanında vb.)
- **Negatif alan:** Kasıtlı boş alan var mı ve nerede?
- **Genel görsel ağırlık:** Tasarım minimal/temiz mi yoksa yoğun/kalabalık mı?

---

## 2. METİN ENVANTERİ, KRİTİK, TAM OL

Reklamda görünen her metin parçası için kelime sayısını kaydet. Kelime sayıları doğrudan yeniden inşa promptuna beslenir ve değiştirme metninin nasıl yazılması gerektiğini belirler. Kesin ol. Her kelimeyi say.

**BAŞLIK (en büyük/en belirgin metin):**
- Tam metin (okunabiliyorsa) veya yaklaşık içerik
- Kelime sayısı: [X kelime]
- Boşluklar dahil karakter sayısı: [yaklaşık X karakter]
- Yazı tipi ağırlığı: bold / yarı-bold / normal
- Görsele göre yazı tipi boyutu: büyük / orta / küçük
- Renk: [belirlenebiliyorsa hex, yoksa açıklama]
- Konum: [görsel üzerinde nerede]
- Tüm büyük harf / başlık büyüklüğü / cümle büyüklüğü?

**ALT BAŞLIK veya İKİNCİL METİN (varsa):**
- Tam metin (okunabiliyorsa) veya yaklaşık içerik
- Kelime sayısı: [X kelime]
- Boşluklar dahil karakter sayısı: [yaklaşık X karakter]
- Yazı tipi ağırlığı, boyutu, rengi, konumu (başlıkla aynı döküm)
- Tüm büyük harf / başlık büyüklüğü / cümle büyüklüğü?

**GÖVDE METNİ (varsa):**
- Tam metin (okunabiliyorsa) veya yaklaşık içerik
- Kelime sayısı: [X kelime]
- Satır sayısı: [X satır]
- Başlığa göre konum ve boyut

**HGPM / BUTON METNİ (varsa):**
- Tam metin veya yakın yaklaşım
- Kelime sayısı: [X kelime]
- Stil: buton / düz metin / rozet?
- Konum

**ROZET, ETİKET veya ÇAĞRI (varsa, örn. "Yeni", "İndirim", "Şurada görüldüğü gibi..."):**
- Tam veya yaklaşık metin
- Kelime sayısı: [X kelime]
- Stil ve konum

**ÜST KATMAN METNİ veya GRAFİK METİN (görsel sahneye entegre metin, yalnızca metin katmanı değil):**
- Görsel sahnenin parçası gibi görünen herhangi bir metni açıkla
- Her parça için kelime sayısı: [X kelime]

---

## 3. METİN STRATEJİSİ ANALİZİ

- **Kanca mekaniği:** Bu reklam nasıl bir kanca kullanıyor?
  - Merak boşluğu ("İnanamayacaksın...")
  - Cesur iddia / spesifik sonuç ("8 haftada 12 kilo verdi")
  - Desen kesintisi / karşıt ("X kullanmayı bırak")
  - İlişkilendirilebilirlik ("Her anne bu hissi bilir")
  - Sosyal kanıt ("10.000 müşteri yanılıyor olamaz")
  - Sorun-ajitasyon ("Hâlâ X ile mi mücadele ediyorsun?")
  - Doğrudan teklif ("Bugün sadece %50 indirim")
  - Önce/sonra ("Z günde X'ten Y'ye")

- **Hedeflenen farkındalık düzeyi:** Bu reklam hangi Schwartz aşamasına hitap ediyor?
  - Habersiz (sorun veya üründen bahis yok, kimlik/yaşam tarzı odaklı)
  - Sorun-Farkında (acıyı adlandırıyor, henüz çözüm yok)
  - Çözüm-Farkında (kategori düzeyinde, marka adı yok)
  - Ürün-Farkında (marka/ürüne özgü)
  - En-Farkında (doğrudan teklif, fiyat, aciliyet)

- **Etkinleştirilen birincil duygu:** Bu reklam izleyicide hangi duyguyu tetikliyor? (hayal kırıklığı, istek, korku, merak, rahatlama, özlem, aidiyet, FOMO)

- **Ton:** Klinik / otoriter / sıcak / sıradan / mizahi / acil / özlemli?

- **Metnin vaat ettiği:** Tek cümlede, bu reklam izleyiciye ne vaat ediyor?

---

## 4. GÖRSEL VE ÜRÜN ÖĞELERİ

- **Ürün yerleşimi:** Ürün görünüyor mu? Ne kadar belirgin? Merkez sahnede mi, köşede mi, biri tarafından tutuluyor mu, yaşam tarzı bağlamında mı, düz yatışta mı?
- **Arka plan:** Tek renk, degrade, yaşam tarzı sahnesi, stüdyo? Rengi/atmosferi açıkla.
- **İnsan öğesi:** Reklamda biri var mı? Yüzü görünüyor mu? İfadesi/beden dili?
- **Aksesuar veya bağlam nesneleri:** Ürünün ötesinde görüntüde ne var?
- **Renk paleti:** 2 ila 4 baskın rengi listele. Genel palet atmosferi açıkla (sıcak/soğuk, cesur/soluk, koyu/açık).
- **Görsel stil:** Fotoğraf / illüstrasyon / grafik tasarım / kolaj / ekran görüntüsü / maket?
- **Sosyal kanıt görsel öğeleri:** Herhangi bir yıldız, yorum parçası, logo, sertifika rozeti var mı?

---

## 5. BU REKLAMI İŞE YARDIRAN NEYDİ

Bu reklamın neden performans gösterdiğine dair 3 ila 5 madde yaz. Şunları dikkate al:
- Spesifik kanca ve neden kaydırmayı durduruyor
- Vaadin netliği ve basitliği
- Gözü çeken görsel kontrast veya odak noktası
- Soğuk kitleyle farkındalık düzeyi eşleşmesi
- Mevcut güven sinyalleri
- Format verimliliği: ne kadar az alanda ne kadar çok şey ilettiği

Bu senin yeniden inşa için stratejik briefindir. Amaç, marka, ürün ve metni değiştirirken bu kazanan özellikleri korumaktır.

---

## 6. DEĞİŞTİRME GEREKSİNİMLERİ ÖZETİ

Yeniden inşa için değiştirilmesi gereken her öğeyi öncelik sırasına göre listele. Her metin öğesi için tam hedef kelime sayısını dahil et. Kelime sayısı yeniden inşa promptu için en önemli kısıttır.

1. **Başlık** yeni metin gerektiriyor [hedef: X kelime, X karakter, aynı format]
2. **Alt başlık** yeni metin gerektiriyor [hedef: X kelime, aynı format]
3. **Gövde metni** yeni metin gerektiriyor [hedef: X kelime, X satır]
4. **HGPM** yeni metin gerektiriyor [hedef: X kelime]
5. **Rozet/Çağrı** yeni metin gerektiriyor [hedef: X kelime] (varsa)
6. **Ürün görseli** kullanıcının ürünüyle değiştirilmeli
7. **Marka renkleri** [Marka DNA'sı renkleriyle] değiştirilmeli
8. **Logo/marka adı** değiştirilmeli (varsa)
9. **Arka plan** olduğu gibi tut / rengi marka paletine göre uyarla
10. **Diğer herhangi bir öğe** [açıkla]

Bu listede olmayan her şey referans görüntüde tam olarak olduğu gibi kalır.
