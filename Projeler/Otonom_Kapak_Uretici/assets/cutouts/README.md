# assets/cutouts/ — Anchor (Yüz Referansı) Fotoğrafları

Bu klasör boş gelir. Kendi yüz referans fotoğraflarınızı buraya koyarsınız.

## Ne koymalıyım

Kapak üreticisi, üretilen görsellerde tutarlı bir yüz çıkarması için "anchor"
(çapa) fotoğraflarına ihtiyaç duyar. Bunlar:

- Arka planı temizlenmiş (transparan PNG) portre fotoğraflarınız
- Yüzünüzün net göründüğü, iyi ışıklı kareler
- En az 3 adet: 1 net front-face (master anchor) + 2 farklı açı (secondary)

## Nasıl eklerim

1. Fotoğraflarınızın arka planını temizleyin (remove.bg, Photoshop vb.) ve PNG kaydedin
2. Bu klasöre koyun, örn: `cutout_ornek_1.png`, `cutout_ornek_2.png`, ...
3. `agents/cutout_tags.json` dosyasını açıp dosya adlarını ve meta-verileri girin:
   - `master_anchor`: en net front-face fotoğrafınız
   - `secondary_anchors`: 2 ek açı
   - `cutouts`: her dosya için mood/angle/quality bilgisi

Identity Lock mimarisi bu fotoğrafları her üretimde sabit referans olarak kullanır.
