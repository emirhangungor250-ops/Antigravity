"""Aynı argument içeriğini 4 farklı body format'ı ile compose et.

Amaç: kullanıcıya görsel A/B/C/D karşılaştırması sunmak.
Yeni Kie call YAPMAZ — mevcut sahneyi yeniden kullanır (varsa /tmp'tan veya
outputs/smoke'tan), yoksa solid fallback.
"""

import os
import sys
import glob
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("ENV", "production")

from core.style import SlidePlan, SLIDE_ROLE
from core import slide_composer as composer


# Mock argument slide — gerçek smoke içeriğinden
TITLE = "MALİYET 600 KAT DÜŞTÜ"
BODY = (
    "Eskiden ajansa 15.000 TL veriyordu. "
    "Şimdi aylık sadece 25 dolar bir araç kullanıyor. "
    "Yıllık fark 175.000 TL'yi aşıyor. "
    "Bu para artık una, fırına, vitrin tasarımına gidiyor."
)


def _find_scene_path() -> str:
    """En yeni mevcut sahneyi bul. Kie call yok."""
    # 1) Mevcut /tmp carousel scenes
    pattern = "/var/folders/**/T/carousel_scene_*.png"
    candidates = glob.glob(pattern, recursive=True)
    if not candidates:
        # macOS alternatif
        candidates = glob.glob("/tmp/carousel_scene_*.png")
    if candidates:
        return max(candidates, key=os.path.getmtime)
    return ""


def main():
    out_dir = PROJECT_ROOT / "outputs" / "alternatives"
    out_dir.mkdir(parents=True, exist_ok=True)

    scene_path = _find_scene_path()
    print(f"📸 Sahne: {scene_path or '(solid fallback)'}")

    slide = SlidePlan(
        index=2,
        total=6,
        role=SLIDE_ROLE.ARGUMENT,
        overlay_text=TITLE,
        body_text=BODY,
    )

    formats = ["paragraph", "bullets", "numbered", "highlighted", "bullets_highlighted"]
    paths = []
    for fmt in formats:
        out = composer.compose_slide(
            slide,
            scene_path,
            out_dir=out_dir,
            body_format=fmt,
            filename=f"format_{fmt}.png",
        )
        paths.append(out)
        print(f"  ✅ {Path(out).name}")

    print(f"\n📂 Çıktılar: {out_dir}\n")
    for p in paths:
        print(f"   - {Path(p).name}")


if __name__ == "__main__":
    main()
