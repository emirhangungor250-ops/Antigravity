# HTML Biçimlendirme Talimatları, VOC Araştırma Belgesi

1. Aşamadan elde edilen eksiksiz VOC araştırma raporunu al ve profesyonel, indirilebilir bir HTML belgesine dönüştür. Tek başına çalışan, dışa bağımlılığı olmayan tek bir HTML dosyası olarak oluştur; CDN bağlantısı, harici font veya harici script yoktur.

---

## Tasarım Sistemi

**Renkler:**
- Birincil lacivert: `#162441`
- İkincil arduvaz: `#8A9BBC`
- Arka plan: `#FFFFFF`
- Yüzey açık: `#F4F6FA`
- Yüzey orta: `#E8EDF5`
- Acı/İtme vurgu: `#C0392B` (kısık kırmızı)
- Arzu/Çekme vurgu: `#1A6B3C` (kısık yeşil)
- Kaygı vurgu: `#8B6914` (kısık amber)
- Alışkanlık vurgu: `#5B4A8A` (kısık mor)
- Farkında Değil etiketi: `#6B7A99`
- Sorun Farkında etiketi: `#C0392B`
- Çözüm Farkında etiketi: `#1A5276`
- Ürün Farkında etiketi: `#1A6B3C`
- Çok Farkında etiketi: `#162441`

**Tipografi:** Sistem sans-serif yığını: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`
- Bölüm etiketleri: 11px büyük harf, harf aralığı 0.12em, `#8A9BBC`
- Bölüm başlıkları: 22px kalın, `#162441`
- Gövde metni: 15px, satır yüksekliği 1.75, `#2C3E50`
- Alıntı metni: 14px, font-style italik, `#162441`, satır yüksekliği 1.7
- Alıntı kaynağı: 11px, `#8A9BBC`
- Etiket haplar: 11px, kalın, büyük harf, harf aralığı 0.08em

---

## Belge Yapısı

### Kapak Başlığı
Tam genişlikte koyu lacivert (`#162441`) başlık bloğu. İçerir:
- "THE AI AD LAB" küçük arduvaz büyük harf takip
- Ürün adı büyük beyaz başlık olarak (28px kalın)
- Araştırma tarihi, ürün URL'si, toplanan toplam alıntı, aranan kaynaklar; temiz istatistik satırı olarak arduvazda
- Kapak başlığında küçük yatay çubuk/hap satırı olarak farkındalık düzeyi dağılımı

### Sabit Kenar Çubuğu Gezintisi
Kaydırmada görünür sabit sol kenar çubuğu (220px genişliğinde). Tüm 15 bölüme bağlantılar. Aktif bölümü sol kenar vurgusuyla laciverte vurgula. Mobilde kenar çubuğunu gizle ve bunun yerine üstte yapışkan gezinti çubuğu ekle. Kenar çubuğundaki bölüm başlıkları kısa etiketler olmalı: "Yönetici Özeti", "Ürün Görüntüsü", "Sorun Noktaları" vb.

### Ana İçerik Alanı
Kenar çubuğunu geçmek için sol dolgu (240px). Maksimum genişlik 820px. Bölümler arasında geniş dikey boşluk (80px).

Her bölümde:
- Arduvazda bölüm numarası (örn. "01")
- Kalın lacivert bölüm başlığı
- Bölüm içeriği
- Altta ince ayırıcı çizgi

---

## Bileşen Stilleri

### Birebir Alıntı Blokları
Bu, en önemli görsel öğedir. Her birebir müşteri alıntısı bu işlemi kullanmalıdır:

```
┌─ JTBD Kuvveti renginde 3px sol kenarlık ──────────────────────────┐
│  "İtalik, 14px, laciverde tam alıntı metni"                       │
│                                                                    │
│  Platform · Ürün/Başlık · Tarih    [YOĞUNLUK] [FARKINDALIK]      │
└────────────────────────────────────────────────────────────────────┘
```

- Sol kenarlık rengi JTBD Kuvvetiyle eşleşir: İtme = kırmızı, Çekme = yeşil, Kaygı = amber, Alışkanlık = mor
- Arka plan: `#F4F6FA`
- Dolgu: 16px 20px
- Kenarlık yarıçapı: 4px
- Kaynak satırı: 11px, `#8A9BBC`
- Etiketler kaynak satırıyla satır içi renkli hap rozetleri olarak gösterilir
- Sağ üst kayan "Kopyala" düğmesi: küçük, arduvaz, tıklamada 2 saniye "✓ Kopyalandı" gösterir
- Kopyalama şu şekilde uygulanır: `navigator.clipboard.writeText(quoteText)`

**Yoğunluk rozeti renkleri:**
- Düşük: `#BDC3C7` arka plan, beyaz metin
- Orta: `#F39C12` arka plan, beyaz metin
- Yüksek: `#E67E22` arka plan, beyaz metin
- Aşırı: `#C0392B` arka plan, beyaz metin

**Farkındalık rozeti renkleri:** Yukarıdaki tasarım sistemindeki farkındalık düzeyi renklerini kullan.

### Etiket/Hap Listeleri (Dil Altın Madeni, Güçlü İfadeler)
İki sütunlu hap düzeni. Her hap:
- Arka plan: `#E8EDF5`
- Kenarlık yarıçapı: 20px
- Dolgu: 6px 14px
- Font: 13px, `#162441`
- Üzerine gelindiğinde "Kopyala" düğmesi görünür

### Özellikten Faydaya Tablosu
Temiz çizgili tablo:
- Başlık satırı: `#162441` arka plan, beyaz metin, 12px büyük harf
- Değişen satırlar: `#FFFFFF` ve `#F4F6FA`
- Hücre dolgusu: 12px 16px
- Müşteri faydası ve duygusal fayda sütunları önceliği işaret etmek için biraz daha büyük metin kullanır

### İdeal Müşteri Profili Bölümü (Bölüm 2)
ICP paragrafı belirgin bir açıklama kutusu alır; koyu lacivert arka plan, beyaz metin, biraz daha büyük font (16px). Bu, belgenin "kuzey yıldızıdır". Altında, Durum, Kimlik Dili, Çevrimiçi Mekanlar ve Arama Dili 2x2 ızgarada dört temiz etiketli kart olarak gösterilir. Kimlik dili ifadeleri ve arama ifadeleri kopyalama düğmeli hap etiketleri olarak gösterilir.

### JTBD Kuvveti Kartları (Bölüm 7)
2x2 ızgarada dört kuvvet kartı:
- İtme kartı: kırmızı sol kenarlık, açık kırmızı arka plan tonu
- Çekme kartı: yeşil sol kenarlık, açık yeşil arka plan tonu
- Kaygı kartı: amber sol kenarlık, açık amber arka plan tonu
- Alışkanlık kartı: mor sol kenarlık, açık mor arka plan tonu

Her kart İş İfadesini, ardından altında destekleyici birebir alıntıları içerir.

### Duygusal Alan Haritası (Bölüm 8)
Duygu sıklığı dökümü saf CSS kullanılarak basit yatay çubuk grafik olarak gösterilir (JS grafik yok). Her duygu, sıklık sayısıyla orantılı bir çubuk alır. Yüksekten (kırmızı) düşüğe (arduvaz) renkli çubuklar.

### Farkındalık Düzeyi Dökümü (Bölüm 7)
Her farkındalık düzeyi daraltılabilir kart olarak (HTML `<details>`/`<summary>`) düzey adı, yüzde tahmini ve altta alıntılarla. Varsayılan olarak baskın düzey dışında daraltılmış.

### Görsel Yön Kartları (Bölüm 9)
Alt kategoriler (Sahne Tanımları, Renk ve Doku, Ruh Hali ve Atmosfer vb.) etiketli kart grupları olarak gösterilir. Her giriş birebir alıntıyı, ardından bir ok (→), ardından çıkarılan etiketi veya sahne türünü gösterir. Bu bölümü görsel olarak ayırt etmek için açık tonlu sol kenarlık.

### Sosyal Kanıt Kartları (Bölüm 13)
İlk 10 referansın her biri kart olarak. Büyük alıntı (16px), altında küçük kaynak. Kuşkucudan İnananaya geçiş alıntıları özel rozet alır: amberde "DÖNÜŞTÜRÜLMÜŞ KUŞKUCU".

### Rekabetçi Manzara (Bölüm 10)
Her rakip daraltılabilir bölümde. "Benzerlik Denizi" açıları kırmızı tonlu uyarı hapları olarak gösterilir. "İşgal Edilmemiş Alan" belirgin stillendirilmiş yeşil açıklama kutusunda gösterilir.

### Değer Denklemi (Bölüm 14)
Dört kaldıraç için dört bölmeli düzen (2x2 ızgara). Her bölme etiketli, altında destekleyici alıntılarla. En zayıf kaldıraç amber uyarı rozeti alır, en güçlü kaldıraç yeşil güç rozeti alır.

---

## Etkileşimli Öğeler

### Kopyalama Düğmesi (Evrensel)
Her alıntı bloğu, her güçlü ifade hapı, her dil altın madeni ifadesinin panoya kopyalama düğmesi olmalıdır. Uygulama:

```javascript
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.innerHTML;
    btn.innerHTML = '✓ Copied';
    btn.style.color = '#1A6B3C';
    setTimeout(() => { btn.innerHTML = original; btn.style.color = ''; }, 2000);
  });
}
```

### Daraltılabilir Bölümler
Tüm daraltılabilir öğeler için yerel `<details>`/`<summary>` kullan. Summary öğesini ham açıklama üçgeni değil, tıklanabilir başlık gibi görünecek şekilde biçimlendir.

### Aktif Bölüm Vurgusu
Kenar çubuğu gezintisinde geçerli bölümü vurgulamak için IntersectionObserver ile uygula:

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
      document.querySelector(`.nav-link[href="#${entry.target.id}"]`)?.classList.add('active');
    }
  });
}, { threshold: 0.3 });
document.querySelectorAll('section[id]').forEach(s => observer.observe(s));
```

### Filtre Çubuğu (Bölümler 3, 4, 5)
Sorun Noktaları, Arzular ve İtirazlar bölümleri için alıntıların üstüne filtre çubuğu ekle:
- JTBD Kuvvetine göre filtrele: Tümü | İtme | Çekme | Kaygı | Alışkanlık
- Yoğunluğa göre filtrele: Tümü | Yüksek | Aşırı
- Farkındalığa göre filtrele: Tümü | Farkında Değil | Sorun Farkında | Çözüm Farkında | Ürün Farkında | Çok Farkında
- Her alıntı bloğunda veri öznitelikleriyle uygula: `data-force`, `data-intensity`, `data-awareness`
- JavaScript, eşleşmeyen alıntı bloklarında `display: none` açar/kapar

---

## Belge Düzeyinde Özellikler

**Hızlı İstatistik Çubuğu:** Kapak başlığının hemen altında yatay istatistik şeridi şunları gösterir: Toplam Alıntı | Aranan Kaynaklar | Baskın Farkındalık Düzeyi | Birincil Duygu | Birincil Sorun Noktası (yalnızca adı). Hepsi tek bir taranabilir satırda.

**Bölüm ankrajları:** Her bölümün kenar çubuğu gezinti bağlantısıyla eşleşen bir `id` özniteliği olmalıdır.

**Yazdırma stilleri:** Kenar çubuğunu gizleyen, etkileşimli öğeleri kaldıran ve alıntı bloklarının temiz yazdırılmasını sağlayan bir `@media print` bloğu ekle.

**Bağımsız çalışır:** Tüm stiller `<head>` içindeki `<style>` bloğunda. Tüm JavaScript `</body>` öncesindeki `<script>` bloğunda. Hiçbir dışa bağımlılık yok.

---

## Bölüm Görüntüleme Sırası

Bölümleri tam olarak bu sırayla görüntüle; bu, reklam metni yazarının iş akışı önceliğiyle eşleşir:

1. Kapak Başlığı + Hızlı İstatistik Çubuğu
2. Yönetici Özeti (01)
3. Dil ve Mesajlaşma Altın Madeni (13), reklam metni yazarlarının önce ulaştığı yer olduğu için yukarı taşındı
4. Görsel ve Duyusal Dil (10), görsel üretim iş akışına hizmet etmek için yukarı taşındı
5. İdeal Müşteri Profili (02), bu kişinin kim olduğu ve çevrimiçi nerede yaşadığı
6. Müşteri Sorun Noktaları ve Hayal Kırıklıkları (04)
7. Müşteri Arzuları ve Hayaldeki Sonuçlar (05)
8. İtirazlar ve Satın Alma Kaygıları (06)
9. Duygusal Alan Haritası (09)
10. Farkındalık Düzeyi Derin Dalma (08)
11. Yapılacak İş Analizi (07)
12. Özellikten Faydaya Çeviri (12)
13. Sosyal Kanıt Cephanesi (14)
14. Rekabetçi Manzara (11)
15. Değer Denklemi Analizi (15)
16. Ürün ve Marka Anlık Görüntüsü (03)
17. Kaynak İndeksi (16)

Kenar çubuğu gezintisi orijinal numaralandırmayı değil, bu görüntüleme sırasını yansıtmalıdır.

---

## Kaydetmeden Önce Kalite Kontrolü

HTML dosyasını çıktılamadan önce şunları doğrula:

- [ ] Dosya tamamen bağımsız çalışıyor; harici CSS'e `<link>` etiketi yok, harici `<script src>` etiketi yok
- [ ] Her birebir alıntının kopyalama düğmesi var
- [ ] Alıntılardaki sol kenarlık renkleri JTBD Kuvvetiyle doğru eşleşiyor
- [ ] Her alıntıda yoğunluk ve farkındalık rozetleri görüntüleniyor
- [ ] Kenar çubuğu gezintisi tüm 17 bölüme (ICP ve Kaynak İndeksi dahil) doğru bağlanıyor
- [ ] Filtre çubukları Sorun Noktaları, Arzular ve İtirazlar bölümlerinde çalışıyor
- [ ] Kapak başlığında farkındalık düzeyi dağılımı gösteriliyor
- [ ] Dil Altın Madeni ve Görsel Dil bölümleri 3. ve 4. sırada (Yönetici Özetinden sonra)
- [ ] Belge 1280px görüntü alanında yatay kaydırma olmadan temiz görüntüleniyor
