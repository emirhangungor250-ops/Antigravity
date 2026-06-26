# DTC Rotası, Bölüm Sırası ve Düzenler

Meta ücretli trafiğinden gelen e-ticaret ürün açılış sayfaları için. Tek birincil CTA: Sepete Ekle veya Şimdi Satın Al.

## Bölüm sırası (zorunlu)

1. **Kahraman** (gömülü sosyal kanıtla)
2. **Sorun pekiştirme** (VOC ağrı alıntısı)
3. **Ürün tanıtımı veya "Yeni yol"** (1-2 cümlede mekanizma, ardından görsel)
4. **Fayda ızgarası** (VOC'tan 3-6 sonuç maddesi)
5. **Sosyal kanıt bloğu** (fotoğraflı referanslar + varsa kullanıcı içeriği)
6. **Karşılaştırma tablosu** (müşterinin kullandığı alternatife karşı)
7. **Ayrıntılı ürün bilgisi** (bileşenler, teknik özellikler, materyaller; şeffaflık güven oluşturur)
8. **Kurucu hikayesi** (neden bunu inşa ettik, en fazla 3-5 cümle)
9. **Yorum yığını** (yıldız puanlarıyla 5+ kısa yorum)
10. **SSS** (birebir VOC soruları)
11. **Garanti bloğu** (spesifik risk tersine çevirme)
12. **Son CTA** (kahraman CTA hedefiyle eşleşir)
13. **Mobil yapışkan CTA çubuğu** (kahraman kaydırmasının ardından görünür, her zaman mevcut)
14. **Minimal alt bilgi** (en fazla 3 satır, telif hakkı, gizlilik, koşullar)

## Kahraman kompozisyonu

```
[Logo sol üst, bağlantısız]                    [Sepete Ekle butonu sağ üst, mobilde gizli]

[H1 sola hizalı, büyük, reklama mesaj uyumlu]
[Alt başlık VOC sonucu cilalı]

[Yıldız puanı + yorum sayısı satırı, 1.847 yorumdan 4,8]

[Birincil CTA butonu, Sepete Ekle, $XX]
[İkincil güven satırı, $50 üzeri ücretsiz kargo. 30 günlük iade.]

[Ürün kahraman görseli masaüstünde sağda, mobilde metnin altında]
```

## Birincil CTA butonu kuralları

- Tek fiil niyeti: "Sepete Ekle", "Kiti Al", "Paketi Satın Al", "Şimdi Al"
- AOV reklamda gösterildiyse buton metnine fiyat ekle: "Sepete Ekle, $48"
- Renk: `--brand-paper`'a karşı iyi kontrast varsa `--brand-accent`, yoksa `--brand-primary`
- Boyut: mobilde minimum `px-8 py-4 text-lg`
- Animasyon: hafif üzerine gelme ölçeklendirmesi (1,02); sıçrama yok, nabız yok

## Mobil yapışkan CTA çubuğu (DTC için zorunlu)

```html
<div class="fixed bottom-0 left-0 right-0 bg-[var(--brand-paper)] border-t border-[var(--brand-muted)]/20 p-3 md:hidden z-50 shadow-lg">
  <a href="#buy" class="block w-full text-center bg-[var(--brand-accent)] text-white py-4 rounded-md font-semibold">
    Add to Cart, $XX
  </a>
</div>
```

Çubuk, kullanıcı kahraman CTA'yı geçtikten sonra görünür. Sayfa CTA'larının her zaman görünür olduğu masaüstünde `md:hidden` ile gizle.

## Karşılaştırma tablosu düzeni

Karşılaştırma tablosu, en yüksek kaldıraçlı DTC bloklarından biridir. 10 fayda maddesinin işini yapar.

```
                    [Markan]        [Kullandıkları Alternatif]
Bileşen kalitesi    [spesifik]      [spesifik zayıflık]
Sonuç süresi        [spesifik]      [spesifik]
Kullanım başına fiyat [spesifik]    [spesifik]
İadeler             [spesifik]      [spesifik veya sunulmaz]
Üretim yeri         [spesifik]      [spesifik veya bilinmiyor]
```

"Kullandıkları alternatifi" VOC'tan çek. Yaygın desenler: "eczanedeki versiyon", "reçeteli olan", "sakızlı olanlar", "toz halindeki versiyon".

## SSS bloğu (DTC özgü)

Mümkün olduğunda birebir VOC'tan 6 soru. En yaygın DTC SSS desenleri:

1. Gerçekten işe yarıyor mu?
2. Sonuçları ne zaman görürüm?
3. Yan etkileri var mı?
4. Her zaman iptal edebilir miyim? (abonelik varsa)
5. Benim için işe yaramazsa ne olur?
6. Kargo ne kadar hızlı?

1-3 cümleyle yanıtla. Dürüst. Spesifik. Pazarlama dili yok.

## Garanti bloğu

SSS ile son CTA arasına yerleştir. Spesifik risk tersine çevirme. "Memnuniyet garantisi" yetmez, hiçbir şey anlatmaz.

İşe yarayan desenler:

- "60 gün dene. Daha keskin bir odak hissetmezsen bize yaz ve her kuruşu iade ederiz. Geri kargo dahil."
- "30 günlük iade garantisi. Şişeyi sende tut. Sadece mike@brand.com'a yaz."
- "Tüm paketi kullan. Beğenmezsen paranı geri göndeririz. Geri kargo bizden."

Spesifiklik kanıttır. Belirsiz garantiler hiçbir şey söylemez.

## Güven unsuru yerleşimi

| Unsur | Nereye | Neden |
|---|---|---|
| Yıldız puanı + yorum sayısı | Kahraman alt başlık alanı | Kahraman CTA tereddüdünü azaltır |
| Müşteri sayısı | Kahraman CTA altında güven satırı | "Birçok kişi satın aldı" fikrini pekiştirir |
| Basın logoları | Kahraman altına (logo şeridi) VEYA atla | Yalnızca gerçek ve hedef kitleye tanınmış ise |
| Kullanıcı içeriği fotoğraf karuseli | Sayfa ortası (faydaların ardından) | Referans değil kullanım yoluyla sosyal kanıt |
| Ayrıntılı yorumlar | Alt üçte bir (garantinin üstünde) | Yüksek değerlendirmeli satın almalar için |
| Güven rozetleri (SSL, Norton) | Markalı Shopify sayfasında ASLA | Güveni artırmaz, düşürür |
| Para iade garantisi | Son CTA'nın hemen üstünde | Son dakika tereddüdünü azaltır |

## Tetiklenecek Pixel olayları (DTC)

Bunları Meta Pixel iskeletine yerleştir. Temel script `references/section-library.md` dosyasındadır. CTA tıklaması başına şunları ekle:

```html
<!-- Herhangi bir birincil CTA tıklamasında, navigasyondan önce -->
<script>
  document.querySelectorAll('a[href^="REPLACE_WITH_CHECKOUT_URL"], a[href="#buy"]').forEach(el => {
    el.addEventListener('click', () => {
      if (typeof fbq !== 'undefined') fbq('track', 'InitiateCheckout');
    });
  });
</script>
```

Sayfa barındırılan Shopify ya da Stripe Checkout'a yönleniyorsa gerçek Satın Alma olayı ödeme tamamlama sayfasından tetiklenir, açılış sayfasından değil. Açılış sayfası yalnızca PageView (otomatik) + InitiateCheckout (CTA tıklamasında) tetikler.

## DTC rotası için değişmez kurallar

1. Tam olarak 1 birincil CTA hedefi (Şimdi Al veya Sepete Ekle eylemi). Tüm birincil CTA'lar aynı yere bağlanır.
2. Mobil yapışkan CTA çubuğu zorunludur.
3. Gerçek ürün görseli zorunludur. Soyut grafik yok.
4. Karşılaştırma tablosu zorunludur.
5. İsim ve fotoğraflarıyla en az 3 referans. VOC'ta fotoğraflı 3 referans yoksa gerçek olanları kullan ve bölümü ayarla.
6. Garanti bloğu spesifik olmalıdır ("memnuniyet garantisi" yetmez).
7. SSS soruları birebir VOC'tan.
8. AOV reklamda varsa birincil CTA butonunda fiyat görünür olmalıdır.
9. Süreklilik teklifleri için geri sayım sayaçları yok (soğuk trafik sahte aciliyete inanmaz).
10. Meşru bir Shopify sayfasında Norton, McAfee veya SSL güven rozetleri yok.
