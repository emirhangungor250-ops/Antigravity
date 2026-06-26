"""'kur' akisi: senaryo → dizi kitabi → asset fabrikasi → kimlik karti.

Resume-safe: her asset sonrasi bible.json kaydedilir; yeniden calistirilirsa
hazir asset'ler atlanir.
"""
import logging
import shutil
from pathlib import Path

from brain import client as brain_client
from brain.schemas import BiblePlan
from core.config import settings
from pipeline import state
from services import imgbb
from services.kie_omni import get_omni_client

log = logging.getLogger("SetupSeries")

SCHEMA_VERSION = 1
EXAMPLE_DIALOGUE_MAX = 120  # Kie omni/audio/create limiti


class PipelineError(RuntimeError):
    """Kullaniciya traceback'siz gosterilecek anlasilir hata."""


def _plan_to_bible(plan: BiblePlan, slug: str) -> dict:
    style = plan.art_style
    return {
        "schema_version": SCHEMA_VERSION,
        "series": {
            "slug": slug,
            "title_tr": plan.title_tr,
            "logline_tr": plan.logline_tr,
            "tone": list(plan.tone),
        },
        "format": {
            "aspect_ratio": "9:16",
            "resolution": "1080p",
            "default_scene_duration": "8",
            "max_episode_seconds": 60,
            "scene_count_range": [6, 10],
        },
        "style": {
            "style_paragraph": style.style_paragraph,
            "negative_constraints": list(style.negative_constraints),
            "seed": plan.series_seed,
            "style_board": {
                "prompt": f"{style.style_paragraph} {style.style_board_prompt}",
                "local_path": "refs/style_board.png",
                "public_url": None,
                "task_id": None,
                "status": "pending",
            },
        },
        "characters": [
            {
                "id": c.id,
                "name": c.name,
                "age": c.age,
                "role": c.role,
                "personality": c.personality,
                "speaking_style": c.speaking_style,
                "visual_description": c.visual_description,
                "voice": {
                    "preset": c.voice.preset,
                    "name": f"{c.name} ({slug})",
                    "voice_description": c.voice.voice_description,
                    "example_dialogue": c.voice.example_dialogue_tr,
                    "kie_audio_id": None,
                },
                "ref_image": {
                    "prompt": f"{style.style_paragraph} {c.visual_description}",
                    "local_path": f"refs/char_{c.id}.png",
                    "public_url": None,
                    "task_id": None,
                },
                "kie_character_id": None,
                "status": "pending",
            }
            for c in plan.characters
        ],
        "narrator": {
            "enabled": plan.narrator.enabled,
            "preset": plan.narrator.preset,
            "voice_description": plan.narrator.voice_description,
            "example_dialogue": plan.narrator.example_dialogue_tr,
            "kie_audio_id": None,
        },
        "environments": [
            {
                "id": e.id,
                "name_tr": e.name_tr,
                "time_of_day": e.time_of_day,
                "lighting_signature": e.lighting_signature,
                "ref_image": {
                    "prompt": f"{style.style_paragraph} {e.image_prompt}",
                    "local_path": f"refs/env_{e.id}.png",
                    "public_url": None,
                    "task_id": None,
                },
                "status": "pending",
            }
            for e in plan.environments
        ],
        "props": [
            {
                "id": p.id,
                "name_tr": p.name_tr,
                "story_role": p.story_role,
                "ref_image": {
                    "prompt": f"{style.style_paragraph} {p.image_prompt}",
                    "local_path": f"refs/prop_{p.id}.png",
                    "public_url": None,
                    "task_id": None,
                },
                "status": "pending",
            }
            for p in plan.props
        ],
        "series_arc": {
            "central_question_tr": plan.series_arc.central_question_tr,
            "episode_seeds_tr": list(plan.series_arc.episode_seeds_tr),
        },
        "episodes": {"counter": 0, "produced": []},
        "continuity": {},
        "drive": {},
    }


def _generate_ref_image(omni, slug: str, asset: dict, label: str) -> None:
    """Tek referans gorseli: uret → poll → indir → ImgBB. asset in-place dolar."""
    task_id = omni.create_image(asset["prompt"], aspect_ratio="9:16")
    asset["task_id"] = task_id
    result = omni.poll_task(task_id)
    if result.get("status") != "success" or not result.get("urls"):
        raise PipelineError(
            f"{label} gorseli uretilemedi ({result.get('error') or result.get('status')}). "
            "'kur' komutunu yeniden calistir, kaldigi yerden surer."
        )
    dest = state.series_dir(slug) / asset["local_path"]
    omni.download_file(result["urls"][0], str(dest))
    asset["public_url"] = imgbb.upload_image(str(dest), name=dest.stem)


def run_setup(senaryo_path: str, slug: str, test: bool = False) -> dict:
    tag = "[TEST] " if test else ""
    sdir = state.series_dir(slug)

    bible = state.load_bible(slug)
    if bible is None:
        scenario_file = Path(senaryo_path)
        if not scenario_file.exists():
            raise PipelineError(f"Senaryo dosyasi bulunamadi: {senaryo_path}")
        scenario_text = scenario_file.read_text(encoding="utf-8")
        log.info(f"{tag}Dizi kitabi yaziliyor ({settings.BRAIN_MODEL})...")
        plan = brain_client.build_series_bible_plan(scenario_text)
        bible = _plan_to_bible(plan, slug)
        sdir.mkdir(parents=True, exist_ok=True)
        dest_md = sdir / "senaryo.md"
        if scenario_file.resolve() != dest_md.resolve():
            shutil.copyfile(scenario_file, dest_md)
        state.save_bible(slug, bible)
        log.info(f"bible.json olusturuldu: {state.bible_path(slug)}")
    else:
        log.info(f"bible.json mevcut, dizi kitabi atlandi (resume): {state.bible_path(slug)}")

    omni = get_omni_client()

    # 1) Stil panosu
    board = bible["style"]["style_board"]
    if board.get("status") != "ready":
        log.info(f"{tag}Stil panosu uretiliyor...")
        _generate_ref_image(omni, slug, board, "stil panosu")
        board["status"] = "ready"
        state.save_bible(slug, bible)

    # 2) Karakter fotograflari
    for char in bible["characters"]:
        if not char["ref_image"].get("public_url"):
            log.info(f"{tag}Karakter fotografi uretiliyor: {char['name']}")
            _generate_ref_image(omni, slug, char["ref_image"], f"karakter ({char['name']})")
            state.save_bible(slug, bible)

    # 3) Ortam + aksesuar plakalari
    plates = [(e, "ortam") for e in bible["environments"]] + [(p, "aksesuar") for p in bible["props"]]
    for item, label in plates:
        if item.get("status") != "ready":
            log.info(f"{tag}{label} plakasi uretiliyor: {item['name_tr']}")
            _generate_ref_image(omni, slug, item["ref_image"], f"{label} ({item['name_tr']})")
            item["status"] = "ready"
            state.save_bible(slug, bible)

    # 4) Ses kimlikleri
    for char in bible["characters"]:
        voice = char["voice"]
        if not voice.get("kie_audio_id"):
            log.info(f"Ses kimligi kaydediliyor: {char['name']} ({voice['preset']})")
            voice["kie_audio_id"] = omni.create_audio_persona(
                voice["preset"],
                voice["name"],
                voice["voice_description"],
                voice["example_dialogue"][:EXAMPLE_DIALOGUE_MAX],
            )
            state.save_bible(slug, bible)

    narrator = bible.get("narrator") or {}
    if narrator.get("enabled") and not narrator.get("kie_audio_id"):
        log.info(f"Anlatici ses kimligi kaydediliyor ({narrator['preset']})")
        narrator["kie_audio_id"] = omni.create_audio_persona(
            narrator["preset"],
            f"Narrator ({slug})",
            narrator["voice_description"],
            narrator["example_dialogue"][:EXAMPLE_DIALOGUE_MAX],
        )
        state.save_bible(slug, bible)

    # 5) Kie karakter kayitlari (gorunum + ses server-side baglanir)
    for char in bible["characters"]:
        if not char.get("kie_character_id"):
            log.info(f"Kie karakteri olusturuluyor: {char['name']}")
            result = omni.create_character(
                description=f"{char['visual_description']} {char['personality']}",
                image_url=char["ref_image"]["public_url"],
                audio_ids=[char["voice"]["kie_audio_id"]],
                character_name=char["name"],
            )
            char["kie_character_id"] = result["characterId"]
            char["status"] = "ready"
            state.save_bible(slug, bible)

    from pipeline.identity_card import generate_identity_card
    card_path = generate_identity_card(bible, slug)
    log.info(f"Seri kimlik karti hazir: {card_path}")
    return bible
