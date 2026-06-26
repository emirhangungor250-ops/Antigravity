# İçerik Yazarı Agent

Belirli bir niş için, kişinin **kendi sesine sadık** sosyal medya video
scriptleri üreten AI agent şablonu.

## Ne işe yarar?

Tek bir kişi/marka için içerik üretir. Agent, kişinin geçmiş "altın standart"
scriptlerinden oluşan bir referans arşivi okur, o üslubu öğrenir ve aynı tarzda
yeni scriptler üretir. Hesaplama gerektiren içeriklerde deterministik araçlar
çağırır, rakip hesaplardan ilham alırken transkript çıkarıp orijinal içerik yazar.

## Desen — bu yapı şuna yarar

Bu proje "voice-consistent content generation agent" desenidir:

1. **Referans corpus** — Kişinin kendi iyi içerikleri `reference-scripts/`'te tutulur;
   agent her üretimden önce bunları okuyup üslubu yakalar.
2. **Skill tanımı** — `skills/icerik-yazari/SKILL.md` format, ton ve konsept
   kurallarını içerir (agent'in "anayasası").
3. **Tool'lar** — `tools/` altında niş-spesifik deterministik araçlar
   (hesaplama, döviz, transkript) — agent rakam üretmek yerine bunları çağırır.
4. **İlham listesi** — `rakipler.md`'deki hesaplardan transkript çıkarıp
   orijinal içeriğe dönüştürür.

Bu desen herhangi bir niş için çalışır: kişisel finans, fitness, yazılım,
yemek, seyahat... Niş, referans corpus ve skill kuralları tamamen sana ait.

## İlk Kurulum — sıralı

1. **Nişini tanımla.** `skills/icerik-yazari/SKILL.md` baştan sona örnek bir niş
   üzerinden yazılmıştır. Konsept kategorilerini, format ve üslup kurallarını
   kendi sektörüne göre yeniden yaz.
2. **Referans corpus'u doldur.** `reference-scripts/` boş bir şablonla geliyor.
   Kendi en iyi scriptlerinden 5-15 tanesini buraya koy — agent senin tarzını
   bunlardan öğrenir.
3. **İlham listesini doldur.** `rakipler.md`'ye kendi nişindeki ilham
   kaynaklarını ekle.
4. **Tool'ları uyarla.** `tools/calculator.py` örnek bir gayrimenkul hesaplayıcı.
   Nişin farklıysa kendi hesaplama mantığınla değiştir veya sil. `currency.py` ve
   `transcript.py` jenerik — çoğu nişte olduğu gibi kullanılabilir.

## Proje Yapısı

```
├── skills/icerik-yazari/
│   └── SKILL.md               ← Üslup, format, ton rehberi (agent anayasası)
├── tools/
│   ├── calculator.py          ← Örnek niş-spesifik hesaplama aracı
│   ├── currency.py            ← Döviz kuru çevirici (jenerik)
│   └── transcript.py          ← Video transkript çıkarıcı (Supadata API)
├── rakipler.md                ← İlham kaynağı hesaplar (şablon)
└── reference-scripts/         ← Kendi script arşivin (şablon — sen doldurursun)
    └── _BOS_SABLON.md
```

## Kullanım

- **Script üret:** Konsepti + konuyu söyle, agent referans corpus'a sadık script üretir.
- **Hesaplamalı içerik:** Parametreleri ver, ilgili tool tabloyu üretir.
- **İlham al:** `rakipler.md`'den bir hesap seç, agent transkript çıkarıp orijinal
  script yazar.

## Bağımlılıklar

`tools/transcript.py` için `SUPADATA_API_KEY` environment variable gerekir
(https://supadata.ai). `currency.py` ve `calculator.py` sadece standart kütüphane
kullanır. Detay için `requirements.txt`.
