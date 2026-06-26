# Sorgu Oluşturma Stratejisi v2

6 kanonik kapsam slotunu kapsayan 6 sorgu. Her sorgu 2 ila 4 kelimedir.
Kısa tut. Uzun sorgular TikTok'un yerel arama sinyalini seyreltir ve sayfa başına daha az sonuç döndürür.

## 6 slot

### 1. Müşteri dilinde acı
Bir acı çekenin yazacağı ham, filtresiz ifade. VOC'un "Problem-space language" bölümünden çek.

**İyi:** `ads stopped working`, `skin purging`, `cant scale meta`, `my product review`
**Kötü:** `Meta advertising underperformance issues` (çok resmi, kimse böyle aramaz)

### 2. Çözüm veya AI iş akışı
Müşterilerin çözümü tanımladığı yol. İddialı ama spesifik olmalı.

**İyi:** `ai ads that actually work`, `retinol routine`, `meta creative system`
**Kötü:** `advertising software` (jenerik; SaaS reklamları döndürür, UGC değil)

### 3. Kimlik / ICP + kategori
Hedef kitlenin kategori hakkında yaptığı videolar. ICP etiketini VOC'tan çek.

**İyi:** `dtc founder meta ads`, `media buyer strategy`, `paid social agency`
**Kötü:** `small business owner` (çok geniş; herhangi bir girişimci içeriği döndürür)

### 4. Problemi bilen ham duygu
Problemin kaba beyanı. Kısa, duygusal.

**İyi (Reklam Fabrikası için):** `meta ads not spending`, `facebook ads broken`, `roas tanking`
**Kötü (2026-04-22 test edildi):** `facebook ads dying`; Facebook hesap-yardım/doğrulama gürültüsü çekiyor

**Düz platform adı içeren sorgulardan kaçın** (`facebook`, `meta`) niteleyici olmadan. Platform adları tek başına hesap destek içeriği getirir.

### 5. İş akışı / nasıl yapılır
Öğretici niyet. İş akışını öğreten içerik üreticilerini getirir.

**İyi:** `ai ugc ads tutorial`, `creative strategy workflow`, `retinol how to`
**Kötü:** `tutorial` (çok geniş)

### 6. Akran güveni / format kalıbı
Niş içindeki formata özgü TikToklar. DIML, POV, tepki vb.

**İyi:** `media buyer day in the life`, `diml social media manager`, `pov running ads`
**Kötü:** `day in the life` (ofis, hemşire, öğretmen, barista vlogları döndürür)

## Kurallar

1. Sorgu başına **minimum 2 kelime.** Tek kelimeli sorgular çok geniş sonuçlar döndürür.
2. Sorgu başına **maksimum 4 kelime.** Daha uzun sorgular TikTok'un "sıfır sonuç" duvarına çarpar.
3. **Tırnak işareti, operatör yok.** TikTok araması boolean operatörlerini veya tam eşleşme tırnaklarını desteklemiyor.
4. **Aynı ismi iki sorgu arasında tekrar kullanma.** Örn. hem `meta ads fatigue` hem `meta ads broken` olmasın; ~%60 örtüşme.
5. **Bir sorgu, müşterinin kendi kelimelerinde ürün kategorisini içermeli.** Bu en düşük-alaka-ama-en-yüksek-hacim ağı haline gelir.

## Doğrulama adımı

6 sorguyu çıkardıktan sonra her birini mantık kontrolünden geçir:

- Bu sorguyla eşleşen bir video yapan gerçek bir içerik üreticisi hayal edebiliyor musun? Edemiyorsan yeniden yaz.
- Yalnızca hedef kitlenin dilini mi içeriyor, yoksa markanın reklam metninden terimler mi var? Pazarlama dilini sıyır.
- Niteleyici olmadan herhangi bir platform adı içeriyor mu (düz `facebook`, `tiktok`, `meta`)? Öyleyse niteleyici ekle veya yeniden yaz.

## Örnek set: Reklam Fabrikası VOC (2026-04-22 doğrulandı)

Bu 6 sorgu gerçek bir çalıştırmada ortalama 10 üzerinden 8,9 alaka üretiyor:

1. `meta ads creative fatigue` (acı)
2. `ai ads that actually work` (çözüm)
3. `dtc founder meta ads` (kimlik + kategori)
4. `meta ads not spending` (problemi bilen; kırık `facebook ads dying` yerine)
5. `ai ugc ads tutorial` (iş akışı)
6. `media buyer day in the life` (akran güveni)

## Ne zaman iterasyon yapılır

SKILL.md'nin Adım 5'teki alaka denetimi, 40 adaydan puan >=7 olan 20'den azını geçirirse, eşiği düşürmek yerine en zayıf performans gösteren sorguları yeniden yaz. Düzeltme aşağıda değil yukarıda yapılır.
