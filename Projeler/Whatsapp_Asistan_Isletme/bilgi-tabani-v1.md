# İşletme WhatsApp Asistanı — Bilgi Tabanı v1 (ŞABLON)

> Bu dosya asistanın "beyni"dir. Buraya kendi işletmenizin bilgi tabanını yazın.
> Yapısı: `##` başlıkları KB section'larını oluşturur. Numaralandırma `services/knowledge_base.js`
> içindeki pinning mantığıyla uyumludur — section numaralarını DEĞİŞTİRMEYİN, sadece içeriği güncelleyin.
> Aşağıdaki örnek bir villa kiralama işletmesi içindir; kendi sektörünüze göre uyarlayın
> (`services/knowledge_base.js` içindeki keyword listelerini de güncelleyin).

> Dosya değişti mi? `node scripts/seed_knowledge.js` çalıştırın (eski chunk'lar silinir, yenisi embed edilir).

---

## 0.1 Asistan Rolü

Buraya asistanın kim olduğunu yazın. Örnek: "Sen <ISLETME_ADI>'nin WhatsApp danışmanısın.
<ISLETME_ADI> <sektör/hizmet> alanında hizmet veren bir işletmedir. Müşteriyi dinler,
ihtiyacını anlar, doğru ürün/hizmeti önerir, satış aşamasında ekibe devreder."

## 0.2 Konuşma Akışı

Asistanın izleyeceği akışı adım adım yazın. Örnek:
1. Açılış keşfi: müşterinin ihtiyacını anlamak için 2-3 kısa soru.
2. İhtiyaç netleştirme: müşteri profilini tespit et.
3. Uygun seçeneklerden 2-3 alternatif öner.
4. Talep netleşince `escalate_to_team` tool çağır → ekip devralır.

## 1.1 Şirket Bilgileri

Buraya işletmenizin ne yaptığını, hangi bölgede/sektörde çalıştığını yazın.

## 1.2 İletişim

- Web: <ISLETME_WEBSITE>
- Telefon: <PHONE>
- WhatsApp: <PHONE>
- E-posta: <EMAIL>
- Ofis: <ADRES>

## 2.1 Bölge / Kategori 1

[BURAYI DOLDURUN] — İlk bölge veya ürün kategorisi hakkında detaylar.

## 2.2 Bölge / Kategori 2

[BURAYI DOLDURUN] — İkinci bölge veya ürün kategorisi.

## 2.3 Bölge / Kategori 3

[BURAYI DOLDURUN] — Üçüncü bölge veya ürün kategorisi.

## 3.1 Ürün / Hizmet Kategorileri

[BURAYI DOLDURUN] — Sunduğunuz ürün/hizmet tiplerini listeleyin. Örnek (villa kiralama):

- **Deniz manzaralı seçenekler** — kısa açıklama
- **Lüks segment** — kısa açıklama
- **Aile dostu seçenekler** — kısa açıklama
- **Bütçe dostu seçenekler** — kısa açıklama

## 3.2 Popüler Örnekler

[BURAYI DOLDURUN] — En çok tercih edilen 10-15 ürün/hizmet: ad, özellik, kapasite, fiyat aralığı.

Örnek format:
- **<Ürün adı>** — <bölge/kategori>, <kapasite>, <öne çıkan özellik>, <fiyat aralığı>

## 4.1 Fiyatlandırma

[BURAYI DOLDURUN] — Genel fiyat aralıklarını ve fiyatı etkileyen faktörleri yazın.
Asistan kesin fiyat söyleyemez; bilgi toplanıp ekip net teklif gönderir.

## 4.2 Ödeme Koşulları

[BURAYI DOLDURUN] — Kapora oranı, taksit imkanı, indirim koşulları.

## 4.3 İptal ve İade Politikası

[BURAYI DOLDURUN] — Resmi iptal/iade politikanız. İptal süreleri, force majeure, değişiklik koşulları.

## 5.1 SSS — Müsaitlik

[BURAYI DOLDURUN] — Müsaitlik nasıl öğrenilir, asistan bunu nasıl ekibe iletir.

## 5.2 SSS — Teslimat / Giriş Süreci

[BURAYI DOLDURUN] — Teslimat veya check-in süreci, saatleri, kim karşılar.

## 5.3 SSS — Bakım / Destek

[BURAYI DOLDURUN] — Hizmet sırasında verilen destek, bakım, ek talep süreçleri.

## 5.4 SSS — Özel Durum 1

[BURAYI DOLDURUN] — Sektörünüze özgü sık sorulan bir konu.

## 5.5 SSS — Özel Durum 2

[BURAYI DOLDURUN] — Sektörünüze özgü sık sorulan bir konu.

## 5.6 SSS — Özel Durum 3

[BURAYI DOLDURUN] — Sektörünüze özgü sık sorulan bir konu.

## 6.1 İletişim Kanalları

Müşteri satın almak istiyorsa asistan `escalate_to_team` tool'unu çağırır. Müşteri kendisi de ulaşabilir:
- WhatsApp: <PHONE>
- Telefon: <PHONE>
- E-posta: <EMAIL>
- Ofis: <ADRES>

## 7.1 Ek Hizmet 1

[BURAYI DOLDURUN] — Sunduğunuz ek hizmet.

## 7.2 Ek Hizmetler

[BURAYI DOLDURUN] — Diğer ek hizmetler.

## 7.3 Özel İstekler

Müşteri özel bir istekte bulunursa asistan `escalate_to_team` çağırır,
ekip karşılayıp karşılayamayacağını bildirir.
