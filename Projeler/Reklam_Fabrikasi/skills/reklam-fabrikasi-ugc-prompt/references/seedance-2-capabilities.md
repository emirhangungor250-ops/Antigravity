# Higgsfield'de Seedance 2.0

Higgsfield, AI video üretimi için önde gelen platformdur. Seedance 2.0 dahil en yeni sınır modellere en kolay ve ucuz erişimi sağlar.

Higgsfield'in Starter, Plus, Ultra ve Business planları var. Seedance 2.0, Starter planına dahil değildir; bu nedenle erişim için en az Plus aboneliği gereklidir.

UGC reklamları için **Seedance 2.0** kullan. **Seedance 2.0 Fast**, tam standart üretimden önce promptları test etmek istersen daha ucuz bir varyantır.

---

## Seedance 2.0

- Çözünürlük: 480p, 720p, 1080p
- Süre: 15 saniyeye kadar
- Dudak senkronizasyonlu yerel ses
- En-boy oranları: 9:16, 16:9, 1:1, 21:9, 4:3, 3:4

## Seedance 2.0 Fast (daha ucuz, test için)

Standartla aynı, şu farklar hariç:
- Çözünürlük: yalnızca 720p
- Biraz daha düşük kalite, daha hızlı üretim

---

## Görüntü girdileri

Kullanıcı yükler:
- 1 karakter görseli
- 1 ila 3 ürün görseli

Karakter görseli içerik üreticisinin görünüşünü kilitler. Ürün görselleri ürünün görünüşünü bir veya birden fazla açıdan kilitler. Model bunları üretilen video boyunca görsel referans olarak kullanır.

---

## Çok çekim

Seedance 2.0, 15 saniyelik zarf içinde çok çekimli düzenlenmiş sekanslar üretir. Çekim değişiklikleri, eylem fiilleri ve kamera geçişleri kullanılarak akıcı düzyazı olarak yazılır.

Şu ifadeleri kullan:

- `she switches to the back camera`
- `quick cut`
- `close-up shot of`
- `she sets the phone down`
- `she brings the front camera back up`
- `medium shot`
- `final close-up`

Model, kesimleri toplam süre içinde doğal olarak ayarlar. Prompt gövdesinde sahne etiketi veya zaman damgası kullanma.

---

## Diyalog

Çift tırnak içindeki metin dudak senkronizasyonunu tetikler:

```
She says, "this is the line."
```

---

## Tutarlılık kuralları

1. Karakter ve ürün tanımlayıcı dizelerini prompt genelinde birebir yeniden kullan, eş anlamlı kelime kullanma
2. Prompt genelinde tek bir ışık ifadesini kilitle
3. Her çekim açıklamasında konum ve atmosferi tutarlı tut

---

## Negatif prompt

Her promptun sonuna ekle:

```
no captions, no background music
```
