"""Marka kimliği constants — carousel_style_guide.md'nin Python karşılığı.

Slide composer (Pillow), image generator (Kie prompt), vision reviewer
hepsi buradan okur. Tek source of truth.
"""

import os
from dataclasses import dataclass, field

# ── Format ──
SLIDE_W = 1080
SLIDE_H = 1350
ASPECT_RATIO = "4:5"

# ── Renk Paleti ──
PRIMARY_DARK = (14, 17, 22)        # #0E1116
PRIMARY_LIGHT = (244, 235, 217)    # #F4EBD9
ACCENT_GOLD = (212, 162, 76)       # #D4A24C
TEXT_BODY = PRIMARY_LIGHT
TEXT_MUTED = (244, 235, 217, 178)  # alpha 70%

# ── Layout Grid ──
SAFE_ZONE_X = 80
SAFE_ZONE_TOP = 120
SAFE_ZONE_BOT = 160
OVERLAY_TEXT_WIDTH = SLIDE_W - 2 * SAFE_ZONE_X  # 920
OVERLAY_TEXT_Y_BASELINE = SLIDE_H - SAFE_ZONE_BOT  # 1190 — alt kenarı

SLIDE_NUMBER_X = SLIDE_W - SAFE_ZONE_X  # 1000 (sağ)
SLIDE_NUMBER_Y = 80  # üst
BRAND_MARK_TEXT = os.environ.get("BRAND_MARK_TEXT", "@yourbrand")

# ── Tipografi (px @ 1080) ──
# HOOK & CTA: kapak gibi kısa, dev font
FONT_HOOK_PX = 140
FONT_CTA_PX = 96

# ARGUMENT slide: küçük başlık + bilgilendirici body paragraf
FONT_ARG_TITLE_PX = 64        # accent başlık (1-2 satır)
FONT_ARG_BODY_PX = 40         # paragraf body (multi-line)

# Eski (geri uyumluluk)
FONT_TITLE_PX = 96            # legacy
FONT_BODY_PX = 42             # legacy

FONT_SLIDE_NUMBER_PX = 28
FONT_BRAND_PX = 24

LETTER_SPACING = -1  # px, tight
LINE_HEIGHT_RATIO_TIGHT = 0.95  # hook/cta için sıkı
LINE_HEIGHT_RATIO_BODY = 1.30   # body paragrafı için rahat
LINE_HEIGHT_RATIO = LINE_HEIGHT_RATIO_TIGHT  # legacy

# Font dosyaları (fonts/ klasörü, ilk run'da indirilir)
FONT_BLACK_PATH = "fonts/Inter-Black.ttf"
FONT_BOLD_PATH = "fonts/Inter-Bold.ttf"
FONT_MEDIUM_PATH = "fonts/Inter-Medium.ttf"

INTER_FONT_URLS = {
    "Inter-Black.ttf": "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Black.woff2",
    # NOT: woff2 değil ttf lazım — alternatif: Google Fonts API
}
# Pratikte Google Fonts CDN'inden ttf çekeceğiz (bkz. utils/font_loader.py)

# ── Gradient Overlay ──
# Hook/CTA: yumuşak alt gradient (sahne dominant)
GRADIENT_BOTTOM_OPACITY = 0.85
GRADIENT_TOP_OPACITY = 0.05
GRADIENT_START_Y_RATIO = 0.30

# Argument: agresif gradient (body paragraf okunaklı olmalı)
GRADIENT_ARG_BOTTOM_OPACITY = 0.94
GRADIENT_ARG_START_Y_RATIO = 0.32  # alt %68 okunabilir koyu zemin


# ── Sahne (Kie) Direktifi ──
SCENE_PHOTOREALISTIC_PREAMBLE = (
    "shot on Canon EOS R5, 35mm lens, natural light, shallow depth of field, "
    "photojournalistic style, editorial documentary photography, magnum photos quality, "
    "cinematic lighting, single focal subject, dramatic composition"
)

SCENE_NEGATIVE_PROMPT = (
    "Avoid: illustration, cartoon, 3D render, flat design, vector art, infographic, "
    "diagram, icons, text, words, letters, numbers, labels, logos, watermarks, signs, "
    "AI-generated artifacts, oversaturated colors, stock-photo cliché smiles, "
    "neon colors, pastel pink, purple gradients"
)

SCENE_BOTTOM_THIRD_RULE = (
    "IMPORTANT composition rule: leave the bottom third of the frame visually quieter "
    "(darker, less detail, fewer elements) so overlay text can be added later. "
    "Subject and main action should occupy the upper two-thirds."
)

SCENE_COLOR_PALETTE_HINT = (
    "Color palette: deep navy, charcoal, warm cream, brass/gold accents. "
    "Avoid neon, pastel, pink, purple."
)


# ── Vision Reviewer Rubric ──
VISION_RUBRIC_CATEGORIES = [
    "photorealism",          # 1-10
    "no_text_artifacts",     # 1-10 (text varsa düşük)
    "subject_clarity",       # 1-10
    "visual_metaphor",       # 1-10
    "brand_color_palette",   # 1-10
    "composition",           # 1-10 (bottom-third overlay alanı)
    "lighting_quality",      # 1-10
]


@dataclass
class SlideRole:
    """Slide rolü — planner ve composer için ortak enum-like."""
    HOOK: str = "hook"
    ARGUMENT: str = "argument"
    CTA: str = "cta"


SLIDE_ROLE = SlideRole()


@dataclass
class SlidePlan:
    """Planner çıktısı — tek bir slide'ın spec'i."""
    index: int                    # 1-based
    total: int                    # toplam slide sayısı
    role: str                     # SLIDE_ROLE.*

    # Hook & CTA: overlay_text dev font ile basılır (kapak mantığı)
    # Argument: overlay_text küçük başlık olarak basılır + body_text paragraf
    overlay_text: str             # Türkçe BÜYÜK HARF, hook=4-7 kelime, arg=2-5 kelime başlık, cta=4-9 kelime
    body_text: str = ""           # ARGUMENT için 3-5 cümle bilgi (~250-500 char). Hook/CTA için boş.
    sub_text: str = ""            # opsiyonel alt satır (CTA için yönlendirme)
    scene_description: str = ""   # English, photorealistic, Kie AI'a gider
    cta_handle: str = BRAND_MARK_TEXT  # CTA slide için
