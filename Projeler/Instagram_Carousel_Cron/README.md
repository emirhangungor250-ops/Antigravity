# Instagram Carousel Cron

Twitter_Text_Paylasim'in ürettiği günlük X+LinkedIn içeriklerini Instagram **kaydırmalı post (carousel)** formatına dönüştüren cron servisi. Her gün 13:30 UTC'de tetiklenir, o günün Notion `Status=Draft` satırlarını çeker, her satırı 5-9 slide'lık bir carousel olarak üretir, mail onayı için bekler.

## Stack

- **Içerik kaynağı:** Notion `NOTION_X_DB_ID` (Twitter_Text_Paylasim'in çıktı DB'si)
- **Slide planlama (LLM):** Anthropic Claude Opus 4.7 — tweet/thread → hook + argümanlar + CTA
- **Görsel üretim:** Kie AI (default `nano-banana-2`, env `KIE_MODEL` ile switchable). Sadece **arka plan sahnesi** üretilir (text-free).
- **Vision review:** Gemini 2.5 Flash — sahne kalitesini puanlar (photorealism, subject_clarity, brand_consistency). Score < 7 ise prompt iyileştirilip max 2 retry.
- **Slide composer:** Pillow — sahne üzerine deterministic overlay metin (Inter Black + Reels-style guide).
- **CDN:** ImgBB (kalıcı slide URL'leri)
- **Onay:** Twitter_Onay_Api'deki `/approve-carousel` endpoint'i (HMAC token, secret paylaşımı)
- **Mail:** Gmail outreach hesabı (Twitter_Text_Paylasim ile aynı OAuth)

## Çalışma Şekli

```
Cron 13:30 UTC
   │
   ├── Notion: bugün üretilmiş Status=Draft, Carousel Status≠Generated rows
   │
   ├── Her row için:
   │     ├── Carousel Planner → 5-9 slide (title + scene_description)
   │     ├── Her slide için:
   │     │     ├── Kie AI prompt build (style guide injection)
   │     │     ├── Kie AI generate + polling
   │     │     ├── Vision Reviewer (max 2 retry)
   │     │     ├── Slide Composer (Pillow overlay)
   │     │     └── ImgBB upload → URL
   │     ├── Caption Writer → Instagram caption
   │     └── Notion update: Carousel Slides + Caption + Status=Generated
   │
   └── Mail Sender: Status=Generated rows → preview HTML + onay butonu
```

## Marka Kimliği

`style/carousel_style_guide.md` — Reels learnings'ten türetilmiş:

- **Format:** 1080×1350 portrait (4:5)
- **Renk paleti:** Deep navy (#0E1116) + cream (#F4EBD9) + gold accent (#D4A24C)
- **Tipografi:** Inter Black (overlay), Inter Bold (sub), Inter Medium (body)
- **Sahne direktifi:** Photorealistic editorial, single subject, no text in image

## Environment Setup

`.env.example` kopyala, `master.env`'den doldur. Lokal:

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python tests/run_smoke.py     # 1 carousel dry-run
```

## Modes

```bash
RUN_MODE=cron      python main.py   # default
RUN_MODE=generate  python main.py   # tek satır manuel (NOTION_ROW_ID=...)
RUN_MODE=mail      python main.py   # sadece mail
RUN_MODE=migrate   python main.py   # Notion DB'ye carousel column'larını ekle
```

## Deploy

Railway service: rootDirectory=`Projeler/IG_Carousel_Cron`, RAILPACK builder, cronSchedule=`30 13 * * *`. Env var'lar master.env'den senkronize edilir. Detay: `_skills/canli-yayina-al`.

## TRANSPARENT teknik kararlar

- **`KIE_MODEL=nano-banana-2`** — GPT-Image-2 Kie API'sinde 2026-05 itibariyle 500 dönüyor (memory + eCom_Reklam_Otomasyonu notu). Düzelirse `gpt-image-2-text-to-image` env değişimiyle geçilir.
- **Hibrit görsel:** Kie sadece sahne üretir (text-free), metin Pillow ile basılır. Marka tutarlılığı garanti, retry sayısı ↓, maliyet ↓.
- **Notion DB ortak:** Twitter_Text_Paylasim ile aynı DB; carousel state yeni property'lere yazılır (1:1 ilişki, foreign key gereksiz).
