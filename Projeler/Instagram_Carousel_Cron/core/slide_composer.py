"""Slide Composer — Kie sahnesi + Pillow overlay → final 1080x1350 slide.

Akış (per slide):
  1. Sahneyi aç, cover-fit ile 1080x1350
  2. Bottom gradient overlay (deep navy, alfa 0→%85)
  3. Slide number (sağ üst, gold)
  4. Overlay text (Türkçe BÜYÜK, auto-fit, alt 1/3'e basılır)
  5. Sub-text varsa (üstüne body font, daha küçük)
  6. CTA slide ise: özel layout (centered + brand mark)

Çıktı: outputs/slide_{idx:02d}.png
"""

from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageOps

from core.style import (
    SLIDE_W,
    SLIDE_H,
    PRIMARY_DARK,
    PRIMARY_LIGHT,
    ACCENT_GOLD,
    SAFE_ZONE_X,
    SAFE_ZONE_BOT,
    SLIDE_NUMBER_X,
    SLIDE_NUMBER_Y,
    BRAND_MARK_TEXT,
    FONT_HOOK_PX,
    FONT_BODY_PX,
    FONT_CTA_PX,
    FONT_ARG_TITLE_PX,
    FONT_ARG_BODY_PX,
    FONT_SLIDE_NUMBER_PX,
    FONT_BRAND_PX,
    LINE_HEIGHT_RATIO,
    LINE_HEIGHT_RATIO_BODY,
    GRADIENT_BOTTOM_OPACITY,
    GRADIENT_START_Y_RATIO,
    GRADIENT_ARG_BOTTOM_OPACITY,
    GRADIENT_ARG_START_Y_RATIO,
    SLIDE_ROLE,
    SlidePlan,
)
from core.font_loader import ensure_fonts, font_path


def _load_font(weight_name: str, size: int) -> ImageFont.FreeTypeFont:
    """Variable font + set_variation_by_name. weight_name: Black/Bold/Medium."""
    f = ImageFont.truetype(font_path(), size)
    try:
        f.set_variation_by_name(weight_name)
    except Exception:
        pass
    return f
from ops_logger import get_ops_logger

ops = get_ops_logger("IG_Carousel_Cron", "Composer")


PROJECT_ROOT = Path(__file__).parent.parent.resolve()
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def _cover_fit(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resize + center-crop ile target boyutuna cover fit."""
    # Tek satır: ImageOps.fit
    return ImageOps.fit(img, (target_w, target_h), method=Image.LANCZOS, centering=(0.5, 0.4))


def _draw_bottom_gradient(canvas: Image.Image, start_ratio: float = GRADIENT_START_Y_RATIO,
                          max_opacity: float = GRADIENT_BOTTOM_OPACITY) -> None:
    """Alt kısma deep-navy gradient overlay (mutate canvas)."""
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    start_y = int(canvas.height * start_ratio)
    max_alpha = int(255 * max_opacity)
    for y in range(start_y, canvas.height):
        ratio = (y - start_y) / max(canvas.height - start_y, 1)
        t = ratio * ratio * (3 - 2 * ratio)
        alpha = int(t * max_alpha)
        draw.line([(0, y), (canvas.width, y)], fill=PRIMARY_DARK + (alpha,))
    canvas.alpha_composite(overlay)


def _wrap_to_lines(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Greedy word-wrap. Boş satır filtrelenir."""
    words = text.split()
    lines: list[str] = []
    current = ""
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    for w in words:
        candidate = (current + " " + w).strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        cw = bbox[2] - bbox[0]
        if cw <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def _autofit_font(text: str, weight_name: str, start_px: int, max_width: int, max_lines: int = 2) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Metni max_lines satırda max_width'e sığacak en büyük font'u bulur."""
    px = start_px
    while px > 32:
        font = _load_font(weight_name, px)
        lines = _wrap_to_lines(text, font, max_width)
        if len(lines) <= max_lines:
            draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
            ok = True
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                if bbox[2] - bbox[0] > max_width:
                    ok = False
                    break
            if ok:
                return font, lines
        px -= 6
    font = _load_font(weight_name, 48)
    return font, _wrap_to_lines(text, font, max_width)


def _draw_text_block(
    canvas: Image.Image,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    anchor_y: str = "bottom",  # "bottom" | "center"
    bottom_margin: int = SAFE_ZONE_BOT,
    align: str = "left",
) -> tuple[int, int]:
    """Çoklu satır metin çiz. Returns (top_y, bottom_y) — diğer elementler için."""
    draw = ImageDraw.Draw(canvas)
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
    line_gap = int(font.size * (LINE_HEIGHT_RATIO - 1))
    total_h = sum(line_heights) + line_gap * (len(lines) - 1)

    if anchor_y == "bottom":
        baseline_y = canvas.height - bottom_margin
        top_y = baseline_y - total_h
    else:  # center
        top_y = (canvas.height - total_h) // 2

    cur_y = top_y
    for line, lh in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        if align == "center":
            x = (canvas.width - text_w) // 2
        elif align == "right":
            x = canvas.width - SAFE_ZONE_X - text_w
        else:
            x = SAFE_ZONE_X
        draw.text((x, cur_y - bbox[1]), line, font=font, fill=fill)
        cur_y += lh + line_gap

    return (top_y, top_y + total_h)


def _draw_slide_number(canvas: Image.Image, idx: int, total: int) -> None:
    font = _load_font("Bold", FONT_SLIDE_NUMBER_PX)
    text = f"{idx:02d} / {total:02d}"
    draw = ImageDraw.Draw(canvas)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    x = SLIDE_NUMBER_X - text_w
    draw.text((x, SLIDE_NUMBER_Y), text, font=font, fill=ACCENT_GOLD)


def _draw_brand_mark(canvas: Image.Image) -> None:
    font = _load_font("Bold", FONT_BRAND_PX)
    draw = ImageDraw.Draw(canvas)
    bbox = draw.textbbox((0, 0), BRAND_MARK_TEXT, font=font)
    text_w = bbox[2] - bbox[0]
    x = (canvas.width - text_w) // 2
    y = canvas.height - 80
    draw.text((x, y), BRAND_MARK_TEXT, font=font, fill=ACCENT_GOLD)


def _solid_dark_canvas() -> Image.Image:
    """Sahne yoksa fallback: solid deep-navy zemin."""
    return Image.new("RGBA", (SLIDE_W, SLIDE_H), PRIMARY_DARK + (255,))


def _compose_hook(canvas: Image.Image, slide: SlidePlan) -> None:
    """HOOK: dev font, bottom anchor, kapak mantığı."""
    _draw_bottom_gradient(canvas, GRADIENT_START_Y_RATIO, GRADIENT_BOTTOM_OPACITY)
    overlay = (slide.overlay_text or "").upper()
    font, lines = _autofit_font(overlay, "Black", FONT_HOOK_PX,
                                 max_width=SLIDE_W - 2 * SAFE_ZONE_X, max_lines=3)
    _draw_text_block(canvas, lines, font, PRIMARY_LIGHT,
                     anchor_y="bottom", align="left")


def _compose_cta(canvas: Image.Image, slide: SlidePlan) -> None:
    """CTA: orta-vertikal, soru, brand mark altta."""
    _draw_bottom_gradient(canvas, GRADIENT_START_Y_RATIO, GRADIENT_BOTTOM_OPACITY)
    overlay = (slide.overlay_text or "").upper()
    font, lines = _autofit_font(overlay, "Black", FONT_CTA_PX + 20,
                                 max_width=SLIDE_W - 2 * SAFE_ZONE_X, max_lines=3)
    _draw_text_block(canvas, lines, font, PRIMARY_LIGHT,
                     anchor_y="center", align="center")

    if slide.sub_text:
        sub_font = _load_font("Medium", FONT_BODY_PX)
        sub_lines = _wrap_to_lines(slide.sub_text, sub_font, SLIDE_W - 2 * SAFE_ZONE_X)
        draw = ImageDraw.Draw(canvas)
        y = canvas.height // 2 + 140
        for sl in sub_lines:
            bbox = draw.textbbox((0, 0), sl, font=sub_font)
            w = bbox[2] - bbox[0]
            draw.text(((canvas.width - w) // 2, y), sl, font=sub_font, fill=ACCENT_GOLD)
            y += int(sub_font.size * LINE_HEIGHT_RATIO_BODY)
    _draw_brand_mark(canvas)


import re


def _draw_solid_panel(canvas: Image.Image, top_y: int, alpha: float = 0.93) -> None:
    """y=top_y'den canvas alt'a kadar solid PRIMARY_DARK panel (sahne hafif görünür).
    Üstte yumuşak transition (50px gradient).
    """
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    a = int(255 * alpha)
    # Transition (50px üst geçiş)
    transition_h = 50
    for y in range(max(0, top_y - transition_h), top_y):
        ratio = (y - (top_y - transition_h)) / transition_h
        t = ratio * ratio * (3 - 2 * ratio)
        draw.line([(0, y), (canvas.width, y)], fill=PRIMARY_DARK + (int(t * a),))
    # Solid block
    draw.rectangle([0, top_y, canvas.width, canvas.height], fill=PRIMARY_DARK + (a,))
    canvas.alpha_composite(overlay)


def _text_with_shadow(draw: ImageDraw.ImageDraw, xy: tuple, text: str,
                       font: ImageFont.FreeTypeFont, fill: tuple,
                       shadow_offset: int = 2) -> None:
    """Drop-shadow + text. Kontrast garantisi."""
    x, y = xy
    shadow_color = (0, 0, 0, 180)
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=fill)


# ── Body content parsing helpers ──

def _split_sentences(body: str) -> list[str]:
    """Body'i cümlelere böl. '.', '!', '?' sınırları."""
    parts = re.split(r"(?<=[\.!?])\s+", body.strip())
    return [p.strip().rstrip(".") for p in parts if p.strip()]


_HIGHLIGHT_PATTERNS = [
    r"\b\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?\s*(?:TL|tl|₺|dolar|USD|usd|\$|€|EUR|euro|kuruş)\b",  # paralar
    r"\b\d+(?:[\.,]\d+)?\s*(?:dakika|saat|gün|hafta|ay|yıl|saniye|kez|kat|katlık|misli|adet|tane|x|X)\b",  # zaman/çarpan
    r"\b%\s*\d+(?:[\.,]\d+)?\b",                # %15 vs
    r"\b\d+(?:[\.,]\d+)?\s*%\b",                # 15% vs
    r"\b\d{2,}(?:[\.,]\d{3})+\b",               # büyük sayılar (1.000+)
]


def _highlight_chunks(line: str) -> list[tuple[str, bool]]:
    """Line'ı (text, is_highlight) parçalarına böl."""
    spans = []
    for pat in _HIGHLIGHT_PATTERNS:
        for m in re.finditer(pat, line):
            spans.append((m.start(), m.end()))
    if not spans:
        return [(line, False)]
    spans.sort()
    # Overlap merge
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    chunks = []
    cur = 0
    for s, e in merged:
        if s > cur:
            chunks.append((line[cur:s], False))
        chunks.append((line[s:e], True))
        cur = e
    if cur < len(line):
        chunks.append((line[cur:], False))
    return chunks


# ── Body format renderers ──

def _render_paragraph(draw: ImageDraw.ImageDraw, body: str, top_y: int,
                       font: ImageFont.FreeTypeFont, max_w: int, line_h: int) -> None:
    lines = _wrap_to_lines(body, font, max_w)
    cur_y = top_y
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        _text_with_shadow(draw, (SAFE_ZONE_X, cur_y - bb[1]), line, font, PRIMARY_LIGHT)
        cur_y += line_h


def _render_bullets(draw: ImageDraw.ImageDraw, body: str, top_y: int,
                     font: ImageFont.FreeTypeFont, max_w: int, line_h: int) -> None:
    sentences = _split_sentences(body)
    bullet_w = 28
    text_x = SAFE_ZONE_X + bullet_w + 16
    cur_y = top_y
    for s in sentences:
        # bullet çizimi (gold dolu daire)
        bb_first = draw.textbbox((0, 0), s, font=font)
        ascent = -bb_first[1]
        bullet_y = cur_y + ascent // 2 + 4
        draw.ellipse(
            [SAFE_ZONE_X, bullet_y, SAFE_ZONE_X + 14, bullet_y + 14],
            fill=ACCENT_GOLD,
        )
        # cümleyi text wrap
        avail_w = max_w - bullet_w - 16
        wrapped = _wrap_to_lines(s, font, avail_w)
        for i, line in enumerate(wrapped):
            bb = draw.textbbox((0, 0), line, font=font)
            _text_with_shadow(draw, (text_x, cur_y - bb[1]), line, font, PRIMARY_LIGHT)
            cur_y += line_h
        cur_y += int(line_h * 0.35)  # bullet'lar arası ekstra boşluk


def _render_numbered(draw: ImageDraw.ImageDraw, body: str, top_y: int,
                      font: ImageFont.FreeTypeFont, max_w: int, line_h: int) -> None:
    sentences = _split_sentences(body)
    num_font = _load_font("Black", font.size + 8)
    cur_y = top_y
    for i, s in enumerate(sentences, start=1):
        prefix = f"{i:02d}"
        # numara
        nb = draw.textbbox((0, 0), prefix, font=num_font)
        prefix_w = nb[2] - nb[0]
        _text_with_shadow(draw, (SAFE_ZONE_X, cur_y - nb[1]), prefix, num_font, ACCENT_GOLD)
        # cümle (numara'nın yanında)
        text_x = SAFE_ZONE_X + prefix_w + 24
        avail_w = max_w - prefix_w - 24
        wrapped = _wrap_to_lines(s, font, avail_w)
        for j, line in enumerate(wrapped):
            bb = draw.textbbox((0, 0), line, font=font)
            _text_with_shadow(draw, (text_x, cur_y - bb[1]), line, font, PRIMARY_LIGHT)
            cur_y += line_h
        cur_y += int(line_h * 0.4)


def _render_highlighted(draw: ImageDraw.ImageDraw, body: str, top_y: int,
                         font: ImageFont.FreeTypeFont, max_w: int, line_h: int) -> None:
    """Düz paragraf ama sayılar/para/zaman accent gold ile vurgulu."""
    # Önce satır wrap (chunk'sız) yap, sonra her satır içinde highlight uygula
    plain_lines = _wrap_to_lines(body, font, max_w)
    cur_y = top_y
    for line in plain_lines:
        chunks = _highlight_chunks(line)
        x = SAFE_ZONE_X
        bb0 = draw.textbbox((0, 0), line, font=font)
        ascent_y = cur_y - bb0[1]
        for txt, is_hl in chunks:
            color = ACCENT_GOLD if is_hl else PRIMARY_LIGHT
            # kalın highlight için Black weight kullan
            f = _load_font("Black" if is_hl else "Medium", font.size)
            _text_with_shadow(draw, (x, ascent_y), txt, f, color)
            bb = draw.textbbox((0, 0), txt, font=f)
            x += bb[2] - bb[0]
        cur_y += line_h


def _render_bullets_highlighted(draw: ImageDraw.ImageDraw, body: str, top_y: int,
                                  font: ImageFont.FreeTypeFont, max_w: int, line_h: int) -> None:
    """Madde işaretli (•) + cümle içindeki sayı/para/zaman accent gold + Black weight."""
    sentences = _split_sentences(body)
    bullet_w = 28
    text_x_indent = SAFE_ZONE_X + bullet_w + 16
    avail_w = max_w - bullet_w - 16
    cur_y = top_y

    for s in sentences:
        # bullet (gold dolu daire) — ilk satırın baseline'ına denk
        bb_first = draw.textbbox((0, 0), s, font=font)
        ascent = -bb_first[1]
        bullet_y = cur_y + ascent // 2 + 4
        draw.ellipse(
            [SAFE_ZONE_X, bullet_y, SAFE_ZONE_X + 14, bullet_y + 14],
            fill=ACCENT_GOLD,
        )

        # cümleyi satırlara wrap et (Medium genişliğine göre)
        wrapped = _wrap_to_lines(s, font, avail_w)
        for line in wrapped:
            chunks = _highlight_chunks(line)
            x = text_x_indent
            bb0 = draw.textbbox((0, 0), line, font=font)
            ascent_y = cur_y - bb0[1]
            for txt, is_hl in chunks:
                color = ACCENT_GOLD if is_hl else PRIMARY_LIGHT
                f = _load_font("Black" if is_hl else "Medium", font.size)
                _text_with_shadow(draw, (x, ascent_y), txt, f, color)
                bb = draw.textbbox((0, 0), txt, font=f)
                x += bb[2] - bb[0]
            cur_y += line_h
        cur_y += int(line_h * 0.35)


BODY_FORMATS = {
    "paragraph": _render_paragraph,
    "bullets": _render_bullets,
    "numbered": _render_numbered,
    "highlighted": _render_highlighted,
    "bullets_highlighted": _render_bullets_highlighted,  # ← seçilen final format
}


def _compose_argument(canvas: Image.Image, slide: SlidePlan,
                       body_format: str = "paragraph") -> None:
    """ARGUMENT: küçük accent başlık + body (paragraph/bullets/numbered/highlighted).

    Layout (1080x1350):
      y=80          slide number (sağ üst)
      [scene visible upper ~y=0..420]
      y=420-1350    SOLID DARK PANEL (alpha 0.93 — kontrast garantili)
      y=460-560     küçük TITLE (BÜYÜK HARF, ~64px, accent gold, max 2 satır)
      y=600         ince ayraç (gold, 80px width)
      y=640-1190    BODY (format'a göre)
    """
    # Solid panel (kontrast garanti)
    _draw_solid_panel(canvas, top_y=420, alpha=0.93)

    title = (slide.overlay_text or "").upper()
    body = (slide.body_text or "").strip()
    if not body and slide.sub_text:
        body = slide.sub_text

    text_max_w = SLIDE_W - 2 * SAFE_ZONE_X
    draw = ImageDraw.Draw(canvas)

    # ── TITLE
    title_font, title_lines = _autofit_font(title, "Black", FONT_ARG_TITLE_PX,
                                              max_width=text_max_w, max_lines=2)
    cur_y = 480
    for line in title_lines:
        bb = draw.textbbox((0, 0), line, font=title_font)
        _text_with_shadow(draw, (SAFE_ZONE_X, cur_y - bb[1]), line, title_font, ACCENT_GOLD)
        cur_y += int(title_font.size * 1.0)
    title_bot_y = cur_y

    # ── ayraç
    sep_y = title_bot_y + 24
    draw.rectangle([SAFE_ZONE_X, sep_y, SAFE_ZONE_X + 80, sep_y + 4], fill=ACCENT_GOLD)
    body_top_y = sep_y + 40

    # ── BODY (format'a göre, auto-fit font size)
    renderer = BODY_FORMATS.get(body_format, _render_paragraph)
    body_font_size = FONT_ARG_BODY_PX
    while body_font_size >= 26:
        body_font = _load_font("Medium", body_font_size)
        line_h = int(body_font_size * LINE_HEIGHT_RATIO_BODY)
        # Conservative size estimate (worst case lines)
        if body_format in ("bullets", "numbered"):
            sentences = _split_sentences(body)
            est_lines = sum(len(_wrap_to_lines(s, body_font, text_max_w - 60)) for s in sentences)
            est_h = est_lines * line_h + len(sentences) * int(line_h * 0.4)
        else:
            est_lines = len(_wrap_to_lines(body, body_font, text_max_w))
            est_h = est_lines * line_h
        if body_top_y + est_h <= SLIDE_H - SAFE_ZONE_BOT:
            break
        body_font_size -= 2

    renderer(draw, body, body_top_y, body_font, text_max_w, line_h)


def compose_slide(slide: SlidePlan, scene_path: Optional[str],
                   out_dir: Optional[Path] = None,
                   body_format: str = "paragraph",
                   filename: Optional[str] = None) -> str:
    """Tek slide'ı compose et, PNG path döner.

    body_format: argument slide'lar için 'paragraph' | 'bullets' | 'numbered' | 'highlighted'.
    filename: özel dosya adı (alternative renderlar için).
    """
    ensure_fonts()
    out_dir = out_dir or OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Sahne aç (yoksa solid)
    if scene_path and Path(scene_path).exists():
        try:
            scene = Image.open(scene_path).convert("RGBA")
            canvas = _cover_fit(scene, SLIDE_W, SLIDE_H)
        except Exception as e:
            ops.warning(f"Sahne açılamadı, solid fallback", details=str(e)[:200])
            canvas = _solid_dark_canvas()
    else:
        canvas = _solid_dark_canvas()

    # 2. Slide number
    _draw_slide_number(canvas, slide.index, slide.total)

    # 3. Role bazlı render
    if slide.role == SLIDE_ROLE.HOOK:
        _compose_hook(canvas, slide)
    elif slide.role == SLIDE_ROLE.CTA:
        _compose_cta(canvas, slide)
    else:
        _compose_argument(canvas, slide, body_format=body_format)

    # 4. Save
    fname = filename or f"slide_{slide.index:02d}.png"
    out_path = out_dir / fname
    canvas.convert("RGB").save(str(out_path), "PNG", optimize=True)
    overlay = slide.overlay_text or ""
    ops.info(f"Slide composed: {out_path.name} [{slide.role}/{body_format}]", message=overlay[:60])
    return str(out_path)
