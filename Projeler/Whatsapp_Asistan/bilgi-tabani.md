# Bilgi Tabanı Şablonu

> Bu dosya asistanin BILGI TABANIDIR (knowledge base). Burayi kendi markaniza,
> urununuze ve sik sorulan sorulariniza gore doldurun.
>
> `scripts/seed_knowledge.js` bu dosyayi `## ` ve `### ` basliklarina gore parcalara
> (chunk) boler, her parcayi embed edip Supabase'e yazar. Asistan bir soru aldiginda
> en alakali parcalari semantic search ile cekip cevabini bunlara dayandirir.
>
> ONEMLI: Basliklara `0.`, `1.`, `2.` gibi numara koyarsaniz, `services/knowledge_base.js`
> bu numaralara gore belirli bolumleri "pinleyebilir" (orn: fiyat sorusunda 2. bolumu
> her zaman one cikarir). Numaralandirma sart degildir ama pinning kullanacaksaniz gereklidir.

## 0. Rol ve Konuşma Akışı

Asistanin temel rolunu, konusma tonunu ve adim adim akisini buraya yazin. Bu bolum
her sorguda asistana sabit olarak verilir. Ornek: "Asistan once kullaniciyi dinler,
ihtiyacini anlar, sonra dogru urunu onerir."

## 1. Marka / Topluluk Hakkında

Markaniz, topluluğunuz veya isletmeniz hakkinda genel bilgi. Ne yapiyorsunuz,
kimlere hitap ediyorsunuz, deger oneriniz nedir.

## 2. Paketler / Fiyatlar

Urun veya hizmet paketlerinizi, fiyatlarini ve farklarini buraya yazin. Asistan
fiyat sorusunda bu bolumu one cikarir.

## 3. Ürünler / Hizmetler

Sundugunuz urun veya hizmetlerin detayli listesi.

## 4. Sık Sorulan Sorular (SSS)

### 4.1 Örnek soru başlığı

Sik sorulan bir sorunun net cevabi. Her SSS'yi ayri bir `### ` alt basligi yapin
ki semantic search daha isabetli calissin.

## 5. Onboarding / İlk Adımlar

Yeni kullanici kayit olduktan sonra ne yapmali, nereden baslamali.

## 10. İletişim ve Linkler

Onemli linkleriniz (kayit sayfasi, topluluk, destek kanali) ve iletisim bilgileri.

## 13. Eskalasyon Politikası

Asistan hangi durumlarda insan yetkiliye eskale etmeli, hangi durumlarda kendi
cevap vermeli. `services/ai_engine.js` icindeki eskalasyon tool tanimiyla tutarli olsun.

## 18. Yasaklar

Asistanin kesinlikle yapmamasi gerekenler (uydurma fiyat, sahte kampanya, garanti
sozu vb.). Bu kurallar ayrica `prompts/system_prompt.md` ve `ai_engine.js` sanitizer'inda
da pekistirilmelidir.
