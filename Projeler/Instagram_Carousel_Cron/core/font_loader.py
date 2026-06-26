"""Inter variable font'ı fonts/ klasörüne indir (ilk run'da). Idempotent.

Tek TTF dosyası — Pillow `set_variation_by_name(...)` ile Black/Bold/Medium switch.
"""

from pathlib import Path

import requests

from ops_logger import get_ops_logger

ops = get_ops_logger("IG_Carousel_Cron", "FontLoader")

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FONTS_DIR = PROJECT_ROOT / "fonts"

INTER_VAR_FILE = "Inter-Variable.ttf"
INTER_VAR_URL = "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"


def ensure_fonts() -> bool:
    """Variable font dosyasını indir (yoksa)."""
    FONTS_DIR.mkdir(exist_ok=True)
    target = FONTS_DIR / INTER_VAR_FILE
    if target.exists() and target.stat().st_size > 100_000:
        return True

    ops.info(f"Variable font indirme: {INTER_VAR_FILE}")
    try:
        r = requests.get(INTER_VAR_URL, timeout=60)
        r.raise_for_status()
        target.write_bytes(r.content)
        ops.info(f"  ✓ {INTER_VAR_FILE} ({len(r.content)//1024}KB)")
        return True
    except Exception as e:
        ops.error("Font indirme fail", exception=e)
        return False


def font_path() -> str:
    """Variable font absolute path."""
    return str(FONTS_DIR / INTER_VAR_FILE)
