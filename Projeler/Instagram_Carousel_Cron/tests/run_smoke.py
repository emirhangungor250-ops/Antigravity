"""End-to-end smoke test — 3-slide mock carousel.

Akış:
  1. Mock content (Türkçe AI use case tweet)
  2. Carousel Planner → 3 slide (override SLIDE_COUNT=3)
  3. Her slide:
     - Kie image gen (3:4)
     - Vision review (max 1 retry)
     - Pillow composer
     - Local outputs/smoke/slide_NN.png
  4. Caption writer → outputs/smoke/caption.txt
  5. Notion + ImgBB skip (yerel test)

Maliyet: ~$0.15 (3 Kie call + 3-6 Gemini vision + 2 Anthropic call)
Süre: ~3-5 dakika
"""

import os
import sys
import json
from pathlib import Path

# Smoke için 3 slide
os.environ.setdefault("SLIDE_COUNT", "3")
os.environ.setdefault("VISION_MAX_RETRY", "1")
os.environ.setdefault("ENV", "production")  # DRY-RUN devre dışı

# Path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Boilerplate config (env'leri yükler)
from config import settings  # noqa
from core import carousel_planner as planner
from core import image_generator as imggen_mod
from core import vision_reviewer as vision
from core import slide_composer as composer
from core import caption_writer as caption_writer
from core.font_loader import ensure_fonts


MOCK_CONTENT = {
    "row_id": "smoke-test-row",
    "title": "AI ses üretim aracı sayesinde 5 dakikada radyo reklamı",
    "source": "AI Use Case",
    "score": 9,
    "tweet_text": (
        "İzmir'de bir butik fırın sahibi, kendi sesi yerine yapay zeka ile "
        "üretilmiş bir spiker sesi kullanarak 5 dakikada radyo reklamı hazırladı. "
        "Eskiden ajansa 15.000 TL veriyordu, şimdi aylık 25 dolar bir araç ile "
        "kendisi yapıyor. Sonuç: aynı kampanyayı 50 farklı varyasyonda test ediyor."
    ),
    "thread": (
        "1) Geçen ay 15.000 TL'lik prodüksiyon faturası geldi. Bu ay sıfır lira.\n\n"
        "2) AI ses üretim araçları artık native Türkçe konuşuyor. Telaffuz hatası bile yok.\n\n"
        "3) 5 dakikada 50 varyasyon ürettik. Hangisi viral olur diye test ediyoruz.\n\n"
        "4) En önemlisi: küçük işletme artık marketing ajansına bağımlı değil.\n\n"
        "5) Bu sadece başlangıç. Önümüzdeki 12 ayda her KOBİ kendi prodüksiyonunu yapacak."
    ),
    "linkedin_text": "",
    "source_url": "",
}


def main():
    out_dir = PROJECT_ROOT / "outputs" / "smoke"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n{'='*70}\n📦 SMOKE TEST — Instagram Carousel Cron\n{'='*70}")
    print(f"Output: {out_dir}")
    print(f"Model: {settings.KIE_MODEL}, Slides: {settings.SLIDE_COUNT}\n")

    ensure_fonts()

    # 1. Plan
    print("\n[1/4] Plan üretiliyor...")
    plans = planner.plan(MOCK_CONTENT)
    if not plans:
        print("❌ Plan üretilemedi. Çıkılıyor.")
        sys.exit(1)
    print(f"✅ {len(plans)} slide planlandı")
    for s in plans:
        print(f"   - Slide {s.index} [{s.role}]: {s.overlay_text}")

    # Plan'ı kaydet
    (out_dir / "plan.json").write_text(
        json.dumps(
            [{"index": s.index, "role": s.role, "overlay_text": s.overlay_text,
              "body_text": s.body_text, "sub_text": s.sub_text,
              "scene_description": s.scene_description}
             for s in plans],
            indent=2, ensure_ascii=False,
        )
    )

    # 2. Per-slide
    print("\n[2/4] Sahne üretimi + vision review + composer")
    imggen = imggen_mod.KieImageGenerator()
    composed_paths = []
    for s in plans:
        print(f"\n  Slide {s.index}/{len(plans)}: {s.overlay_text}")
        base_prompt = planner.enrich_scene_for_kie(s)
        scene_path, _ = imggen.generate(base_prompt, aspect_ratio="3:4")
        if not scene_path:
            print(f"   ⚠️  Kie generate fail, solid fallback")
        else:
            review = vision.review(scene_path, scene_description=s.scene_description)
            if review:
                print(f"   📊 Vision: {review['score']:.2f} ({'PASS' if review['passed'] else 'FAIL'})")
                if review.get("feedback"):
                    print(f"      → {review['feedback'][:120]}")
                if not review["passed"]:
                    print(f"   🔄 Retry...")
                    new_prompt = vision.build_retry_prompt(
                        base_prompt, review.get("feedback", ""), review.get("categories", {})
                    )
                    scene_path, _ = imggen.generate(new_prompt, aspect_ratio="3:4")
                    if scene_path:
                        review2 = vision.review(scene_path, scene_description=s.scene_description)
                        if review2:
                            print(f"   📊 Retry vision: {review2['score']:.2f} ({'PASS' if review2['passed'] else 'FAIL'})")

        composed_path = composer.compose_slide(
            s, scene_path, out_dir=out_dir, body_format=settings.BODY_FORMAT
        )
        composed_paths.append(composed_path)
        print(f"   ✅ {Path(composed_path).name}")

    # 3. Caption
    print("\n[3/4] Caption yazılıyor...")
    caption = caption_writer.write(MOCK_CONTENT, plans)
    if caption:
        (out_dir / "caption.txt").write_text(caption)
        print(f"✅ Caption ({len(caption)} char) → caption.txt")
        print(f"   Preview: {caption[:140]}…")
    else:
        print("⚠️  Caption üretilemedi")

    # 4. Özet
    print(f"\n[4/4] Özet")
    print(f"{'='*70}")
    print(f"📂 Çıktılar: {out_dir}")
    for p in composed_paths:
        size_kb = Path(p).stat().st_size // 1024
        print(f"   - {Path(p).name} ({size_kb} KB)")
    if (out_dir / "caption.txt").exists():
        print(f"   - caption.txt")
    print(f"   - plan.json")
    print(f"\n💡 Slide'ları görmek için:  open {out_dir}\n")


if __name__ == "__main__":
    main()
