"""IG_Carousel_Cron — orchestrator.

Modes (RUN_MODE env):
  - cron     : Notion'dan bugün/dün üretilmiş Status=Draft satırlarını çek,
               her birini carousel olarak üret, sonra mail at. (default)
  - generate : Tek bir satırı manuel üret. NOTION_ROW_ID env zorunlu.
  - mail     : Sadece mail (zaten generated olanlar için).
  - migrate  : scripts/add_notion_columns.py çağır.

Tek bir Railway cron servisi. Schedule: 30 13 * * * (UTC) — twitter cron'undan
~6.5 saat sonra (twitter draft'lar Notion'a girmiş olur).
"""

import os
import sys
from pathlib import Path

from config import settings
from ops_logger import get_ops_logger, wait_all_loggers

ops = get_ops_logger("IG_Carousel_Cron", "Pipeline")


# ── Lazy imports (LLM/Pillow heavy modules sadece gerektiğinde load) ──
def _lazy_imports():
    from core import notion_repo as _notion
    from core import carousel_planner as _planner
    from core import image_generator as _imggen
    from core import vision_reviewer as _vision
    from core import slide_composer as _composer
    from core import imgbb_uploader as _imgbb
    from core import caption_writer as _caption
    from core.font_loader import ensure_fonts
    return _notion, _planner, _imggen, _vision, _composer, _imgbb, _caption, ensure_fonts


def generate_one_slide(slide, planner, imggen, vision, composer, out_dir):
    """Tek slide için: image gen → vision review → retry → composer → return path."""
    base_prompt = planner.enrich_scene_for_kie(slide)
    current_prompt = base_prompt
    scene_path = ""
    last_review = None

    for attempt in range(settings.VISION_MAX_RETRY + 1):
        ops.info(f"Slide {slide.index}: image gen attempt {attempt + 1}")
        scene_path, _kie_url = imggen.generate(current_prompt, aspect_ratio="3:4")
        if not scene_path:
            ops.warning(f"Slide {slide.index}: Kie generate fail (attempt {attempt + 1})")
            continue

        review = vision.review(scene_path, scene_description=slide.scene_description)
        if not review:
            ops.warning(f"Slide {slide.index}: vision review None")
            break  # vision yoksa sahneyi olduğu gibi kullan
        last_review = review
        if review.get("passed"):
            ops.info(f"Slide {slide.index}: vision PASS ({review['score']:.2f})")
            break
        # Fail → retry için prompt iyileştir
        current_prompt = vision.build_retry_prompt(
            current_prompt, review.get("feedback", ""), review.get("categories", {})
        )
        ops.info(f"Slide {slide.index}: vision FAIL, retry prompt güncellendi")

    # Compose (sahne yoksa solid fallback)
    composed_path = composer.compose_slide(
        slide, scene_path, out_dir=out_dir, body_format=settings.BODY_FORMAT
    )
    return composed_path, last_review


def generate_carousel_for_row(row: dict, modules) -> bool:
    """Tek bir Notion satırı için: plan → her slide → caption → notion update."""
    notion, planner, imggen, vision, composer, imgbb, caption_writer, ensure_fonts = modules

    row_id = row["row_id"]
    notion.update_status(row_id, "Generating")
    ensure_fonts()

    # 1. Plan
    plans = planner.plan(row)
    if not plans:
        ops.error(f"Plan üretilemedi: {row.get('title', '')[:60]}")
        notion.update_status(row_id, "Failed")
        return False

    # 2. Per-slide
    out_dir = Path("outputs") / row_id[:8]
    out_dir.mkdir(parents=True, exist_ok=True)
    slide_records = []

    for slide in plans:
        composed_path, _review = generate_one_slide(
            slide, planner, imggen, vision, composer, out_dir
        )
        if not composed_path:
            ops.error(f"Slide {slide.index} compose fail, carousel iptal")
            notion.update_status(row_id, "Failed")
            return False

        cdn_url = imgbb.upload(composed_path, name=f"{row_id[:8]}_slide{slide.index:02d}")
        if not cdn_url:
            ops.warning(f"Slide {slide.index} ImgBB fail, file:// URL kullanılıyor")
            cdn_url = f"file://{composed_path}"

        slide_records.append({
            "index": slide.index,
            "url": cdn_url,
            "overlay_text": slide.overlay_text,
            "role": slide.role,
        })

    # 3. Caption
    caption = caption_writer.write(row, plans) or "[caption üretilemedi]"

    # 4. Notion update
    notion.save_generated_carousel(row_id, slide_records, caption)
    return True


def run_cron():
    modules = _lazy_imports()
    notion = modules[0]
    candidates = notion.fetch_carousel_candidates(days=1, limit=10)
    if not candidates:
        ops.info("Cron: bugünkü carousel adayı yok, mail step'e geçiliyor")
    else:
        ops.info(f"Cron: {len(candidates)} aday bulundu")
        for row in candidates:
            try:
                ok = generate_carousel_for_row(row, modules)
                if ok:
                    ops.success(f"Carousel hazır: {row.get('title', '')[:60]}")
            except Exception as e:
                ops.error(f"Row exception: {row.get('title', '')[:60]}", exception=e)
                try:
                    notion.update_status(row["row_id"], "Failed")
                except Exception:
                    pass

    # Mail
    from core.mail_sender import send_summary_mail
    send_summary_mail()


def run_generate_one():
    row_id = os.environ.get("NOTION_ROW_ID", "").strip()
    if not row_id:
        ops.error("NOTION_ROW_ID env zorunlu (generate mode)")
        sys.exit(1)
    modules = _lazy_imports()
    notion = modules[0]
    row = notion.fetch_row(row_id)
    if not row:
        ops.error(f"Row bulunamadı: {row_id}")
        sys.exit(1)
    generate_carousel_for_row(row, modules)


def run_mail():
    from core.mail_sender import send_summary_mail
    send_summary_mail()


def run_migrate():
    from scripts.add_notion_columns import main as migrate_main
    migrate_main()


def main():
    mode = (os.environ.get("RUN_MODE") or "cron").lower()
    ops.info(
        "Başlatıldı",
        f"mode={mode} env={settings.ENV} model={settings.KIE_MODEL} "
        f"slides={settings.SLIDE_COUNT} vision_threshold={settings.VISION_SCORE_THRESHOLD}",
    )

    try:
        if mode == "cron":
            run_cron()
        elif mode == "generate":
            run_generate_one()
        elif mode == "mail":
            run_mail()
        elif mode == "migrate":
            run_migrate()
        else:
            ops.error(f"Bilinmeyen RUN_MODE: {mode}")
            sys.exit(1)
    except Exception as e:
        ops.error("Pipeline exception", exception=e)
        sys.exit(1)
    finally:
        ops.info("Container kapanıyor")
        wait_all_loggers()


if __name__ == "__main__":
    main()
