"""Sadece hook slide'ı yeni absürt direktiflerle üret + aç."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("ENV", "production")

from core.style import SlidePlan, SLIDE_ROLE
from core import carousel_planner as planner
from core import image_generator as imggen_mod
from core import vision_reviewer as vision
from core import slide_composer as composer
from config import settings


# Aynı senaryo (AI ses + ajans), ama hook'a planner'dan absürt sahne istiyoruz
HOOK_SLIDE = SlidePlan(
    index=1,
    total=6,
    role=SLIDE_ROLE.HOOK,
    overlay_text="AJANSA VEDA",
    body_text="",
    scene_description=(
        "An angry small business owner standing in front of a marketing agency "
        "office, dramatically throwing a stack of invoices into the air, papers "
        "exploding mid-frame, freeze-frame action moment, fire flickering in the "
        "background, dusk lighting"
    ),
)


def main():
    out_dir = PROJECT_ROOT / "outputs" / "hook_test"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📦 HOOK ONLY TEST\n  Output: {out_dir}\n")

    composer.ensure_fonts()

    prompt = planner.enrich_scene_for_kie(HOOK_SLIDE)
    print("PROMPT:\n" + prompt[:600] + "…\n")

    imggen = imggen_mod.KieImageGenerator()
    scene_path, _ = imggen.generate(prompt, aspect_ratio="3:4")
    if not scene_path:
        print("❌ Kie fail")
        sys.exit(1)

    review = vision.review(scene_path, scene_description=HOOK_SLIDE.scene_description)
    if review:
        print(f"📊 Vision: {review['score']:.2f} ({'PASS' if review['passed'] else 'FAIL'})")
        print(f"   {review.get('feedback', '')[:200]}")

    out_path = composer.compose_slide(
        HOOK_SLIDE, scene_path, out_dir=out_dir, body_format="paragraph"
    )
    print(f"\n✅ {out_path}")


if __name__ == "__main__":
    main()
