# QA kapısı, prompt üretiminden önce konsept başına kontroller

Bu dosya, kullanıcı bir konsepti onayladıktan sonra ve her konsept revizyonunun ardından sessizce çalışan 6 konsept başına kontrolü tanımlar. 6 kontrolün tamamını geçen konseptler Adım 9'a (görsel prompt üretimi) geçer. Herhangi bir kontrolde başarısız olan konseptler kullanıcıya nedenini açıklayan tek satırla geri sunulur; böylece kullanıcı revize edebilir veya bırakabilir.

4 küme düzeyi kısıtlama (farkındalık kapsamı, çirkin/native, sosyal kanıt, örtüşme yok) Adım 5'teki strateji motoru tarafından yukarı akışta uygulanır. Burada yeniden çalışmazlar. Kullanıcı onaylamaya başladığında küme zaten dengelenmiştir.

Strateji motorundan gelen 4 konsept başına kısıtlama (VOC alıntısı, marka reklam sinyali veya beyaz alan boşluğu, sahte sosyal kanıt yok, evrimsel) burada 1, 2, 3 ve 6. kontroller olarak yeniden belirtilmektedir, çünkü her revizyon bunları yeniden kanıtlamalıdır.

---

## Kontrol 1, VOC kanıtı (konsept başına kısıtlama 5)

**Geçme kriteri:** Konseptin VOC alıntısı alanı, VOC araştırma belgesinde birebir görünen bir dize içerir. Eşleşme büyük/küçük harf duyarsızdır ancak boşluklar normalleştirilmiş. Parafrazlar geçemez.

**Başarısız mesajı:**

> N "<konsept adı>" konsepti birebir bir VOC alıntısı göstermedi. VOC alanındaki satır VOC belgenizde görünmüyor. Bu konsepti gerçek bir birebir alıntıyla revize etmemi ister misiniz, yoksa bırakalım mı?

---

## Kontrol 2, Marka reklam sinyali veya beyaz alan boşluğu (konsept başına kısıtlama 6)

**Geçme kriteri:** Konseptin "Neden işe yaramalı" bölümü şunlardan en az birine referans verir:
- Çekilen PROVEN veya HOT marka reklamından belirli bir unsur (markanın zaten başardığı bir açı, kanca, görsel format veya kanıt mekanizması)
- Strateji motorunun beyaz alan haritasında belirlenen belirli bir beyaz alan boşluğu (VOC'un desteklediği, markanın kullanmadığı bir açı)

Referans gerçek bir sinyale işaret edecek kadar özgün olmalıdır, yalnızca "markanın sesi" veya "müşterinin acısı" gibi genel ifadeler değil. Özgün bir referans şöyle görünür: "reklam #4'teki referans öncülü düzen (PROVEN, 87 gün çalışıyor)" veya "markanın son 20 reklamında problem-aware konsept yok, VOC alıntıların %38'inin problem-aware olduğunu gösteriyor".

**Başarısız mesajı:**

> N "<konsept adı>" konsepti belirli bir marka reklam sinyaline veya belirli bir beyaz alan boşluğuna dayanmadı. Gerekçe çok genel. Somut bir çıpa ile revize etmemi ister misiniz, yoksa bırakalım mı?

---

## Kontrol 3, FTC 2024 uyumluluğu (konsept başına kısıtlama 7)

**Geçme kriteri:** Konseptte hiçbir müşteri sayısı, yorum sayısı, yıldız puanı, referans, basın söylemi veya onay görünmez; bunlar VOC'tan, Marka DNA'sından veya çekilen reklamlardan kaynaklı değilse. Beceri bu adımda dahili bir kaynaklı-olgular listesi tutar. Konseptin metnindeki (büyük fikir, kanca, başlık adayları, görsel yön, neden işe yaramalı) herhangi bir olgusal iddia bu listeyle çapraz kontrol edilir.

Bu kontrol şu durumlarda devreye girer:
- Konsept bir müşteri sayısı uyduruyor ("10.000'den fazla anneden güvenilir")
- Konsept bir yorum sayısı veya yıldız puanı uyduruyor ("2.400 yorumdan 4,9 yıldız")
- Konsept bir basın söylemi uyduruyor ("Forbes'ta görüldüğü üzere")
- Konsept bir ünlü, uzman veya doktor onayı uyduruyor
- Konsept sahte bir kişiye atfedilmiş sahte bir referans içeriyor

**Başarısız mesajı:**

> N "<konsept adı>" konsepti VOC'unuzda, Marka DNA'nızda veya çekilen reklamlarınızda olmayan bir iddia içeriyor: "<belirli iddia>". FTC 2024, ücretli reklamlarda uydurulmuş sosyal kanıtı yasaklamaktadır. Onsuz revize etmemi ister misiniz, yoksa konsepti bırakalım mı?

---

## Kontrol 4, Görsel üretilebilirlik

**Geçme kriteri:** 5 görsel ailenin her biri bu konsept için GPT Image 2'nin yetenek aralığında güçlü bir render üretebilir. Kontrol şunları kapsar:

- Özne somuttur (bir ürün, bir şey yapan bir kişi, gerçek bir sahne), soyut değil ("özgürlük hissi", "enerji")
- Ürün yüklenen ürün görsellerinden render edilebilir (görsel yön hayal edilen bir ürünü değil, gerçek ürünü referans alır)
- Sahne GPT Image 2'nin güvenilir şekilde sunamayacağı yetenekler gerektirmiyor (uzun paragrafların mükemmel tipografisi, piksel hassasiyetli kullanıcı arayüzüyle belirli gerçek uygulamaların sahte ekran görüntüleri, karmaşık çok kareli çizgi roman düzenleri)
- Görsel yön Marka DNA'sında açıkça onaylanmadığı sürece belirli adlandırılmış kimlikte kişiler gerektirmiyor (gerçek ünlü, gerçek kurucu)

**Başarısız mesajı:**

> N "<konsept adı>" konsepti GPT Image 2'nin temiz render etmekte zorlanacağı bir görsel yöne sahip: "<belirli sorun>". Görsel yönü revize etmemi ister misiniz, yoksa konsepti bırakalım mı?

---

## Kontrol 5, Sahte aciliyet yok

**Geçme kriteri:** Konsept uydurulmuş aciliyet veya kıtlık kullanmıyor. Özellikle:
- Marka DNA'sı veya isteğe bağlı brifing açıkça gerçek bir son tarih belirtmediği sürece "sınırlı süre" veya "yalnızca bugün" yok
- Gerçek bir sayı sağlanmadığı sürece "yalnızca X kaldı" stok sayıları yok
- Geri sayım sayaçları yok
- Kaynaklı bir olgu olmadan "hızla tükeniyor" yok

Gerçek aciliyet (belgelenmiş bir indirim penceresi, belgelenmiş sınırlı bırakım) kabul edilebilir. Genel sahte aciliyet kabul edilemez.

**Başarısız mesajı:**

> N "<konsept adı>" konsepti brifingınızda veya Marka DNA'nızda olmayan bir aciliyete dayanıyor: "<belirli ifade>". Soğuk Meta trafiği sahte aciliyetle satın almaz. Onsuz revize etmemi ister misiniz, yoksa konsepti bırakalım mı?

---

## Kontrol 6, Klon değil evrimsel (konsept başına kısıtlama 8)

**Geçme kriteri:** Konsept bir marka reklam sinyalini kopyalamak yerine geliştiriyor. Evrim, kaynak reklamdan aşağıdakilerden en az ikisinin farklı olduğu anlamına gelir:
- Farkındalık aşaması
- Kanca mekaniği
- Görsel aile
- Kanıt mekanizması
- Persona
- Görsel sahne

Mevcut bir marka reklamından 6 boyuttan 5'ini kopyalayan bir konsept, çoğaltma değil klondur. (Yeni metinle klonlar için çoğaltıcı becerisini kullanın.)

**Başarısız mesajı:**

> N "<konsept adı>" konsepti mevcut bir marka reklamına ("<reklam referansı>") çok yakın. Yalnızca bir boyutta farklılaşıyor. O reklamın gerçek bir varyasyonu için çoğaltıcı becerisini kullanın. Bu konsepti gerçekten farklı bir konsepte dönüştürmemi ister misiniz, yoksa bırakalım mı?

---

## Beceri bu dosyayı nasıl kullanır

Becerinin Adım 8'i bu dosyayı yükler ve onaylanan her konsept üzerinde (Adım 7 düzenlemelerinin ardından yeniden yüzeylenen revize konseptler dahil) 1'den 6'ya kadar kontrolleri çalıştırır. 6 kontrol sessizce çalışır. 6 kontrolün tamamını geçen konseptler Adım 9'a geçer. Herhangi bir kontrolde başarısız olan konseptler eşleşen başarısız mesajı tetikler, kullanıcı revize eder veya bırakır ve döngü tekrar eder.

Bir konsept 6 kontrolün tamamını geçerse beceri bu konuda sessizdir. Kullanıcı yalnızca bir şey başarısız olduğunda QA kapısı çıktısını görür. Bu, arayüzü temiz tutar ve kullanıcının zamanına saygı gösterir.
