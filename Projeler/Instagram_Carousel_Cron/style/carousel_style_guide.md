# Instagram Carousel — Marka Stil Rehberi

Reels-Kapak (Rourke) DNA'sının carousel formatına adapte edilmiş hali.
Tüm slide'lar bu kurallarla üretilir; vision reviewer bu kurallara karşı puan verir.

## 1. Format

- **Boyut:** 1080 × 1350 px (4:5 portrait — Instagram carousel optimize)
- **Slide sayısı:** 5–9 (planner içeriğin uzunluğuna göre seçer; default 7)
- **Slide rolleri:**
  - Slide 1 → Hook (vurucu açılış, max 4 kelime)
  - Slide 2..N-1 → Argüman (her biri tek bir nokta)
  - Slide N → CTA (soru + Instagram bio yönlendirme)

## 2. Renk Paleti

```
PRIMARY_DARK   = #0E1116   (zemin / koyu overlay)
PRIMARY_LIGHT  = #F4EBD9   (beyaz alternatifi, krem)
ACCENT_GOLD    = #D4A24C   (vurgu — slide numarası, CTA)
TEXT_BODY      = #F4EBD9
TEXT_MUTED     = rgba(244, 235, 217, 0.7)
GRADIENT_OVERLAY = linear-gradient(180deg, transparent 0%, rgba(14,17,22,0.05) 30%, rgba(14,17,22,0.85) 100%)
```

Her sahnenin alt %50'sine deterministic gradient overlay basılır → metin okunabilirliği garanti.

## 3. Tipografi (Pillow ile basılır)

```
HOOK_FONT        = Inter Black (900)        — slide 1 hook
TITLE_FONT       = Inter Black (900)        — slide 2..N-1 başlık
BODY_FONT        = Inter Medium (500)       — gerekirse alt satır
CTA_FONT         = Inter Bold (700)         — slide N CTA
SLIDE_NUM_FONT   = Inter Bold (700)         — sağ üst "01/07" rakamı
```

- **Boyutlar (1080 px genişlik için):**
  - Hook: 140 px (auto-fit, 2 satıra böl, max-width %85)
  - Title: 96 px
  - Body: 42 px
  - CTA: 76 px
  - Slide number: 28 px
- **Caps:** TÜMÜ büyük harf (Türkçe upper)
- **Letter-spacing:** -1 px (sıkı), `tracking_em = -0.01`
- **Line-height:** 0.95
- **Türkçe yasağı yok** (Reels learnings #4 burada da geçerli — overlay metin %100 Türkçe)

## 4. Layout Grid

```
SAFE_ZONE_X   = 80 px      (sol & sağ)
SAFE_ZONE_TOP = 120 px
SAFE_ZONE_BOT = 160 px

OVERLAY_TEXT_BLOCK:
  width  = 1080 - 2*80 = 920 px
  y_anchor = "bottom"   (CTA hariç hep alt)
  y_baseline = 1350 - 160 = 1190 px (ilk satır alt kenarı)

SLIDE_NUMBER:
  position = top-right
  x = 1080 - 80 = 1000 px
  y = 80 px
  text = f"{i:02d} / {N:02d}"
  color = ACCENT_GOLD

CTA_SLIDE (son slide):
  text vertical-center (y=675)
  ek: "@yourbrand" küçük marka mark, alt-orta
```

## 5. Sahne (Kie AI üretimi) Direktifleri

Reels learnings'in carousel'a uygulanmış hali:

### 5.1 Photorealistic Editorial — ZORUNLU
```
"shot on Canon EOS R5, 35mm lens, natural light, shallow depth of field,
photojournalistic style, magnum photos quality"
```
Vector / illustration / 3D render / cartoon → SCORE 0.

### 5.2 NO TEXT IN IMAGE — ZORUNLU
Sahnede hiçbir yazı, sayı, logo, etiket, tabela olmamalı. Pillow overlay basacak.
Negative prompt:
```
"text, words, letters, numbers, labels, logos, watermarks, signs with readable text"
```

### 5.3 Concrete Physical Metaphor (Reels Kural #10)
Klişeden kaçın. Soyut kavramı somut sahneyle anlat.
- ❌ "Adam bilgisayara bakıyor"
- ✅ "Adam çöp dağı üzerinde duruyor (eski sistemleri terk etti metaforu)"

### 5.4 Single Focal Subject (Reels Kural #12)
Tek figür / tek nesne. Arka plan dramatik ama sade — max 2-3 ana element.
Depth of field ile özne ayrılsın.

### 5.5 Cinematic Lighting
- Outdoor: golden hour / blue hour
- Indoor: warm ambient + practical light source
- Yüksek kontrast, dramatik gölge OK

### 5.6 Composition (Carousel-spesifik)
- Hook slide: hero shot, ortada
- Argüman slide'ları: bottom-third compositional weight (overlay metin alt %35'i kaplıyor, üst %65 görsel)
- CTA slide: minimal sahne (boş alan + tek vurucu element)

### 5.7 Renk Tutarlılığı
Sahnenin dominant renkleri palet ile uyumlu olmalı:
- Koyu zemin (deep navy / charcoal / forest)
- Krem / sıcak beyaz vurgular
- Altın / pirinç highlight
Pastel, neon, mor, pembe → AVOID.

## 6. Vision Reviewer Rubric (1-10)

```
photorealism            : Gerçek fotoğraf gibi mi? (illustration / 3D = 0)
no_text_artifacts       : Sahnede yazı/logo/sayı var mı? (varsa < 5)
subject_clarity         : Tek özne öne çıkıyor mu?
visual_metaphor         : Somut bir hikaye anlatıyor mu? (klişe = düşük)
brand_color_palette     : Renkler dark/cream/gold yelpazesinde mi?
composition             : Bottom-third overlay alanı temiz mi (Pillow için yer var mı)?
lighting_quality        : Cinematic mi, flat mi?
```

Toplam ortalama < 7 → retry (max 2). Spesifik düşük puanlı kategori için feedback prompt'a inject edilir.

## 7. Caption Tonu (Pillow değil — Instagram caption)

- Hook (1 cümle, max 12 kelime)
- 3-5 bullet (her biri 1 satır, • ile değil yeni satır + emoji-free)
- Soru (engagement)
- 5-8 hashtag (Türkçe + İngilizce karışık, yapay zeka, otomasyon, KOBİ ekosistem)
- Em-dash YASAK (memory)
- Cümle max 15 kelime (memory)
- Ürün/marka adı (Suno, Rythmix vb.) caption'da geçmesin (memory)
