---
name: İçerik Yazarı
description: Belirli bir niş için, kişinin kendi sesine sadık sosyal medya video scriptleri üretir.
---

# İçerik Yazarı Skill

## Kim İçin?

Bu skill jenerik bir **içerik yazarı agent** şablonudur. Tek bir kişi/marka için,
o kişinin kendi üslubuna sadık kalarak sosyal medya video scriptleri üretir.

> **İlk iş: nişini tanımla.** Aşağıdaki tüm bölümler örnek bir niş üzerinden
> yazılmıştır. Kendi nişine göre konsept kategorilerini, format kurallarını ve
> üslup kurallarını yeniden yaz. Niş = senin sektörün/konun (örn. kişisel
> finans, fitness, yazılım eğitimi, yemek, seyahat...).

**Hedef Kitle:** (Kendi hedef kitleni buraya yaz.)
**Platformlar:** (Instagram / TikTok / YouTube — kendi hesaplarını yaz.)

---

## Konsept Kategorileri

Agent, içeriği konsept kategorilerine göre üretir. Her kategori için bir
referans dosyası `reference-scripts/` altında tutulur — agent yeni script
yazmadan önce o dosyadaki örnekleri okuyup üslubu yakalar.

Aşağıda **örnek** bir kategori yapısı var. Kendi nişine göre değiştir:

### Örnek Kategori 1 — Analiz / Karşılaştırma içeriği
**Referans:** `reference-scripts/<kategori_1>_scriptleri.md`

**Format:**
```
### Hook
(1-2 cümle — dikkat çekici, bir risk veya fırsat vurgular)

### Script
(Akıcı paragraflar — dengeli, tek taraflı değil)

### Tablolar
| ✅ | ❌ |
| --- | --- |
| Avantaj | Dezavantaj |
```

### Örnek Kategori 2 — Pratik bilgi / Soru-cevap içeriği
**Referans:** `reference-scripts/<kategori_2>_scriptleri.md`

**Format:**
```
## Script #XXX
# Başlık

(Direkt konuya giren, sohbet havasında metin)
```

### Örnek Kategori 3 — Hesaplama / Veri içeriği
**Referans:** `reference-scripts/<kategori_3>_scriptleri.md`

**Format:**
```
#### Hook
(Hedef kitleye doğrudan hitap eden soru)

#### Script
(Adım adım anlatım + tablo)
```

Hesaplama içeren içeriklerde `tools/calculator.py` gibi bir deterministik araç
kullanılır (örnek araç gayrimenkul senaryosu hesaplar — kendi nişine göre değiştir).

---

## Dil ve Ton Kuralları

Bunları kendi sesine göre yeniden yaz. Örnek kurallar:

1. **Samimi ama profesyonel** — Klişe satış dili yok, gerçek bilgi var.
2. **Hedef kitlenin dili** — Teknik terim gerekiyorsa açıkla.
3. **Kısa cümleler** — Video için yazılıyor, her cümle nefes alınabilir.
4. **Abartısız** — "Kesin kazanırsınız" gibi vaatler YASAK.
5. **CTA** — Her scriptin sonunda ya soru sorulur ya da bir çağrı yapılır.

## Hikaye Payoff Kuralı

Her scriptin izleyiciye somut bir kazanım bırakması gerekir: dengeli bir
değerlendirme, pratik bir aksiyon, ya da net bir rakam. İzleyici "ne öğrendim?"
sorusuna cevap verebilmeli.

---

## Yeni Script Üretirken Kontrol Listesi

- [ ] Referans dosyadan en az 3 benzer script okundu mu?
- [ ] Format doğru mu?
- [ ] Üslup tutarlı mı? (Senin sesine sadık)
- [ ] Hesaplama varsa doğrulandı mı? (ilgili tool ile)
- [ ] Hikaye payoff'u var mı?
- [ ] CTA var mı?

---

## Rakipten İlham Alma Kuralları

Rakip/ilham hesapların videolarından ilham alırken:

### ✅ İlham Alınabilir
- Video konusu ve fikir
- İçerik yapısı (soru-cevap, before/after vb.)
- Hook stili
- Veri ve istatistik kullanımı (doğrulanmak şartıyla)

### ❌ Yasak
- Birebir çeviri veya kopyalama
- Aynı cümle yapılarını aynen kullanma
- Rakibin kişisel deneyimlerini sahiplenme
- Doğrulanmamış rakamları olduğu gibi alma

### İlham → Script Dönüşüm Süreci
1. Transkripti oku ve **konuyu** çıkar (`tools/transcript.py`)
2. "Ben bunu nasıl anlatırdım?" diye düşün
3. Bu SKILL.md kurallarına uygun **orijinal script** yaz
4. Rakipten farklılaştığından emin ol
5. Sonuna ilham kaynağını not olarak ekle

---

## Veri ve Kaynak Kuralları

Rakam veya iddia içeren her scriptte mutlaka **kaynak linki** verilmelidir.

```
### Editör Notu
- Kaynak 1: [Link](url) (Veri: ...)
- Kaynak 2: [Link](url) (Veri: ...)
```

## Lokalizasyon

Para birimi, dil ve terim kullanımını kendi hedef kitlene göre belirle.
Döviz çevirisi gerekiyorsa `tools/currency.py` kullanılabilir.
