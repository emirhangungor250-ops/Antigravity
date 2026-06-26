"""'bolum' akisi: senaryo yaz → sahneleri sirayla uret → birlestir → Drive → hafiza.

Resume omurgasi episode.json'dur; her durum gecisinde atomic kaydedilir.
Surec ortasinda kesilse bile `--devam` (veya plain `bolum`) kaldigi yerden surer.
"""
import json
import logging
import re
from datetime import datetime, timezone

from brain import client as brain_client
from brain import duration_rules, memory, qc
from brain.composer import compose_scene_prompt, derive_scene_seed
from brain.reference_selector import select_references
from brain.sanitizer import check_dialogue
from brain.schemas import EpisodeScript, SceneSpec
from core import drive_service
from core.config import settings
from pipeline import state
from pipeline.setup_series import PipelineError
from services.cost_tracker import CostTracker
from services.ffmpeg_assembler import assemble_episode, probe
from services.kie_omni import get_omni_client

log = logging.getLogger("ProduceEpisode")

MAX_SCENE_ATTEMPTS = 2
POLICY_HINTS = ("flag", "policy", "sensitive", "moderat", "unsafe", "prohibit", "nsfw")
TEST_DURATION = "4"
TEST_RESOLUTION = "720p"
TEST_SCENE_COUNT = 2


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_title(title: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", title or "", flags=re.UNICODE)
    return re.sub(r"\s+", "_", cleaned.strip())[:60] or "bolum"


def _compact_bible(bible: dict) -> str:
    """Senarist LLM'e giden kompakt bible (gorsel promptlar ve kie id'leri haric)."""
    compact = {
        "series": bible.get("series", {}),
        "characters": [
            {k: c.get(k) for k in ("id", "name", "age", "role", "personality", "speaking_style")}
            for c in bible.get("characters", [])
        ],
        "narrator": {"enabled": bool(bible.get("narrator", {}).get("enabled"))},
        "environments": [
            {k: e.get(k) for k in ("id", "name_tr", "lighting_signature", "time_of_day")}
            for e in bible.get("environments", [])
        ],
        "props": [
            {k: p.get(k) for k in ("id", "name_tr", "story_role")}
            for p in bible.get("props", [])
        ],
        "series_arc": bible.get("series_arc", {}),
    }
    return json.dumps(compact, ensure_ascii=False)


def _scene_record(scene: SceneSpec, idx: int, bible: dict, episode_no: int,
                  resolution: str, test: bool) -> dict:
    refs = select_references(scene, bible)
    prompt = compose_scene_prompt(scene, bible, refs)
    return {
        "idx": idx,
        "scene_number": scene.scene_number,
        "prompt": prompt,
        "duration": TEST_DURATION if test else str(scene.duration_s),
        "aspect_ratio": bible.get("format", {}).get("aspect_ratio", "9:16"),
        "resolution": resolution,
        "seed": derive_scene_seed(bible["style"]["seed"], episode_no, scene.scene_number, attempt=0),
        "image_urls": refs["image_urls"],
        "audio_ids": refs["audio_ids"],
        "character_ids": refs["character_ids"],
        "expect_audio": bool(scene.dialogue),
        "clip_path": "sahneler/scene_%02d.mp4" % idx,
        "status": "pending",
        "task_id": None,
        "attempts": 0,
        "result_url": None,
        "fail_msg": None,
    }


def _plan_new_episode(slug: str, bible: dict, konu: str, test: bool) -> dict:
    episode_no = bible.get("episodes", {}).get("counter", 0) + 1
    ep_slug = state.next_episode_slug(bible) + ("-test" if test else "")

    seeds = bible.get("series_arc", {}).get("episode_seeds_tr", [])
    episode_seed = seeds[min(episode_no, len(seeds)) - 1] if seeds else ""
    state_summary = memory.build_series_state_summary(state.load_series_state(slug))

    log.info(f"Bolum {episode_no} senaryosu yaziliyor ({settings.BRAIN_MODEL})...")
    script = brain_client.write_episode(
        _compact_bible(bible), state_summary, episode_no, episode_seed, konu
    )
    script.episode_number = episode_no  # bible sayaci kazanir
    script, warnings = duration_rules.validate_and_repair(script, bible)
    for w in warnings:
        log.warning(f"onarim: {w}")

    for scene in script.scenes:
        for line in scene.dialogue:
            hits = check_dialogue(line.line_tr)
            if hits:
                log.warning(f"sahne {scene.scene_number} diyalog risk tetikleri: {hits}")

    scene_specs = script.scenes[:TEST_SCENE_COUNT] if test else script.scenes
    resolution = TEST_RESOLUTION if test else bible.get("format", {}).get("resolution", "1080p")
    if test:
        log.info(f"[TEST] Sadece ilk {TEST_SCENE_COUNT} sahne, {TEST_DURATION}sn, {TEST_RESOLUTION}")

    ep = {
        "slug": ep_slug,
        "series_slug": slug,
        "episode_number": episode_no,
        "test": bool(test),
        "status": "generating",
        "script": script.model_dump(),
        "repair_warnings": warnings,
        "scenes": [
            _scene_record(sc, idx, bible, episode_no, resolution, test)
            for idx, sc in enumerate(scene_specs, 1)
        ],
        "final": {},
        "cost": {},
        "timestamps": {"created": _now()},
    }
    state.save_episode(slug, ep)
    log.info(f"episode.json olusturuldu: {state.episode_path(slug, ep_slug)} ({len(ep['scenes'])} sahne)")
    return ep


def _check_budget(omni, cost: CostTracker) -> None:
    """Submit oncesi kredi koruma: bolum harcamasi limiti gectiyse durdur."""
    if settings.MAX_EPISODE_CREDITS <= 0 or cost.credits_start is None:
        return
    balance = omni.get_credit_balance()
    if balance is None:
        return
    spent = cost.credits_start - balance
    if spent >= settings.MAX_EPISODE_CREDITS:
        raise PipelineError(
            f"Bolum kredi limiti asildi: {spent:.0f} kredi harcandi "
            f"(limit {settings.MAX_EPISODE_CREDITS:.0f}). "
            "Limiti artirip ayni komutu --devam ile calistir, kaldigi yerden surer."
        )


def _retry_seed(scene: dict, bible: dict, episode_no: int) -> int:
    return derive_scene_seed(
        bible["style"]["seed"], episode_no, scene["scene_number"], attempt=scene["attempts"]
    )


def _register_failure(slug: str, ep: dict, scene: dict, bible: dict, error: str) -> None:
    scene["attempts"] += 1
    scene["fail_msg"] = error
    scene["task_id"] = None
    if any(h in (error or "").lower() for h in POLICY_HINTS):
        log.warning(f"Sahne {scene['idx']}: icerik politikasi reddi gorunuyor, prompt sadelestiriliyor")
        try:
            scene["prompt"] = brain_client.simplify_scene_prompt(scene["prompt"], error)
        except Exception as e:
            log.warning(f"Prompt sadelestirme basarisiz, ayni promptla denenecek: {e}")
    if scene["attempts"] < MAX_SCENE_ATTEMPTS:
        scene["seed"] = _retry_seed(scene, bible, ep["episode_number"])
        scene["status"] = "pending"
    else:
        scene["status"] = "failed"
    state.save_episode(slug, ep)


def _produce_scenes(slug: str, ep: dict, bible: dict, omni, cost: CostTracker) -> str:
    """Sahne dongusu (SERI). Doner: 'ok' | 'timeout' | 'failed'."""
    ep_dir = state.episode_dir(slug, ep["slug"])
    total = len(ep["scenes"])

    for scene in ep["scenes"]:
        while True:
            if state.scene_is_complete(scene, slug, ep["slug"]):
                log.info(f"Sahne {scene['idx']}/{total} hazir, atlandi")
                break
            if scene["status"] == "completed":
                # completed ama klip diskte yok → yeniden uret
                log.warning(f"Sahne {scene['idx']}: klip dosyasi kayip, yeniden uretilecek")
                scene["status"] = "submitted" if scene.get("task_id") else "pending"
                state.save_episode(slug, ep)
                continue

            if scene["status"] == "submitted" and scene.get("task_id"):
                log.info(f"Sahne {scene['idx']}/{total}: mevcut gorev poll'laniyor ({scene['task_id']})")
                result = omni.poll_task(scene["task_id"])
            elif state.scene_needs_submit(scene, slug, ep["slug"]):
                _check_budget(omni, cost)
                log.info(
                    f"Sahne {scene['idx']}/{total} gonderiliyor "
                    f"({scene['duration']}sn, seed={scene['seed']}, deneme {scene['attempts'] + 1})"
                )
                task_id = omni.create_video(
                    scene["prompt"],
                    duration=scene["duration"],
                    aspect_ratio=scene["aspect_ratio"],
                    resolution=scene["resolution"],
                    seed=scene["seed"],
                    image_urls=scene["image_urls"] or None,
                    audio_ids=scene["audio_ids"] or None,
                    character_ids=scene["character_ids"] or None,
                )
                scene["task_id"] = task_id
                scene["status"] = "submitted"
                state.save_episode(slug, ep)
                result = omni.poll_task(task_id)
            else:
                return "failed"  # failed + attempts tukenmis

            status = result.get("status")
            if status == "timeout":
                ep["timestamps"]["last_timeout"] = _now()
                state.save_episode(slug, ep)
                return "timeout"

            if status != "success":
                _register_failure(slug, ep, scene, bible, result.get("error", "bilinmeyen hata"))
                if scene["status"] == "failed":
                    return "failed"
                continue  # pending'e dustu, dongu basa sarar

            urls = result.get("urls") or []
            if not urls:
                _register_failure(slug, ep, scene, bible, "gorev success ama sonuc URL'i bos")
                if scene["status"] == "failed":
                    return "failed"
                continue

            clip_abs = ep_dir / scene["clip_path"]
            try:
                omni.download_file(urls[0], str(clip_abs))
            except Exception as e:
                # Buyuk ihtimalle URL suresi dolmus (14 gun) → ayni task ise yaramaz
                log.warning(f"Sahne {scene['idx']}: indirme basarisiz ({e}), gorev sifirlanip yeniden uretilecek")
                scene["task_id"] = None
                scene["status"] = "pending"
                state.save_episode(slug, ep)
                continue
            scene["result_url"] = urls[0]

            ok, reason = qc.tier1_check(str(clip_abs), int(scene["duration"]), scene["expect_audio"])
            if ok:
                scene["status"] = "completed"
                scene["fail_msg"] = None
                state.save_episode(slug, ep)
                log.info(f"Sahne {scene['idx']}/{total} tamamlandi")
                break
            _register_failure(slug, ep, scene, bible, f"QC tier1: {reason}")
            if scene["status"] == "failed":
                return "failed"

    return "ok"


def _qc_expected_dims(ep: dict) -> None:
    """Test modunda (720p, gercek API) tier1 cozunurluk beklentisini ayarla.

    DRY_RUN placeholder klipleri her zaman 1080x1920 oldugundan dokunulmaz.
    """
    if settings.IS_DRY_RUN:
        return
    if ep["scenes"] and ep["scenes"][0].get("resolution") == "720p":
        qc.EXPECTED_W, qc.EXPECTED_H = 720, 1280


def _write_qc_report(slug: str, ep: dict, bible: dict) -> None:
    if settings.IS_DRY_RUN:
        log.info("[DRY-RUN] QC tier2 atlandi")
        return
    ep_dir = state.episode_dir(slug, ep["slug"])
    script_scenes = {s["scene_number"]: s for s in ep.get("script", {}).get("scenes", [])}
    report = []
    for scene in ep["scenes"]:
        spec = script_scenes.get(scene["scene_number"], {})
        char_refs = []
        for cid in spec.get("character_ids", []):
            char = next((c for c in bible.get("characters", []) if c.get("id") == cid), None)
            if char:
                ref = state.series_dir(slug) / char.get("ref_image", {}).get("local_path", "")
                if ref.exists():
                    char_refs.append(str(ref))
        verdict = qc.tier2_flag(str(ep_dir / scene["clip_path"]), char_refs, spec.get("action", ""))
        report.append({"scene": scene["scene_number"], "verdict": verdict})
    state.atomic_write_json(ep_dir / "qc_report.json", {"generated": _now(), "scenes": report})
    flagged = [r["scene"] for r in report if r["verdict"] and not all(
        (r["verdict"].get("character_match", True),
         r["verdict"].get("style_consistent", True),
         not r["verdict"].get("has_text_artifacts", False))
    )]
    if flagged:
        log.warning(f"QC tier2 bayraklari (bloklamaz): sahne(ler) {flagged} — qc_report.json'a bak")


def run_episode(slug: str, konu: str = "", devam: bool = False, test: bool = False) -> dict:
    bible = state.load_bible(slug)
    if bible is None:
        raise PipelineError(
            f"'{slug}' serisinin dizi kitabi yok. Once kur calistir:\n"
            f"  python main.py kur --senaryo <senaryo.md> --seri {slug}"
        )
    not_ready = [c["name"] for c in bible.get("characters", []) if not c.get("kie_character_id")]
    if not_ready:
        raise PipelineError(
            f"Su karakterler henuz hazir degil: {', '.join(not_ready)}. "
            f"'kur' komutunu yeniden calistir (kaldigi yerden surer)."
        )

    omni = get_omni_client()
    cost = CostTracker(omni, settings.KIE_CREDITS_PER_USD)
    cost.start()

    ep = state.find_unfinished_episode(slug)
    if ep is not None:
        log.info(f"Yarim bolum bulundu, devam ediliyor: {ep['slug']} (durum: {ep['status']})")
    elif devam:
        raise PipelineError("Devam edilecek yarim bolum yok. --devam'siz calistirip yeni bolum baslat.")
    else:
        ep = _plan_new_episode(slug, bible, konu, test)

    ep_dir = state.episode_dir(slug, ep["slug"])

    # ─── Sahne dongusu ───────────────────────────────────────────────────
    if ep["status"] in ("planning", "generating", "failed"):
        ep["status"] = "generating"
        state.save_episode(slug, ep)
    _qc_expected_dims(ep)
    outcome = _produce_scenes(slug, ep, bible, omni, cost)

    if outcome == "timeout":
        msg = (
            "Sahne uretimi hala Kie tarafinda suruyor (poll zaman asimi, gorev kaybolmadi). "
            f"Biraz sonra devam et: python main.py bolum --seri {slug} --devam"
        )
        log.warning(msg)
        ep["message"] = msg
        return ep

    if outcome == "failed":
        failed = next((s for s in ep["scenes"] if s["status"] == "failed"), {})
        ep["status"] = "failed"
        state.save_episode(slug, ep)
        msg = (
            f"Bolum durdu: sahne {failed.get('idx')} {MAX_SCENE_ATTEMPTS} denemede uretilemedi.\n"
            f"Son hata: {failed.get('fail_msg')}\n"
            f"Cozum: {state.episode_path(slug, ep['slug'])} dosyasinda o sahnenin prompt'unu duzenle, "
            f"status='pending' ve attempts=0 yap, sonra: python main.py bolum --seri {slug} --devam"
        )
        log.error(msg)
        ep["message"] = msg
        return ep

    # ─── Birlestirme ─────────────────────────────────────────────────────
    ep["status"] = "assembling"
    state.save_episode(slug, ep)
    final_rel = f"final/{ep['slug']}_final.mp4"
    final_abs = ep_dir / final_rel
    final_abs.parent.mkdir(parents=True, exist_ok=True)
    if final_abs.exists() and final_abs.stat().st_size > 0:
        log.info(f"Final dosyasi zaten var, birlestirme atlandi: {final_abs}")
        duration_s = probe(str(final_abs))["duration_s"]
    else:
        clips = [str(ep_dir / s["clip_path"]) for s in sorted(ep["scenes"], key=lambda s: s["idx"])]
        log.info(f"{len(clips)} sahne birlestiriliyor (sesli concat + loudnorm)...")
        duration_s = assemble_episode(clips, str(final_abs))["duration_s"]
    if duration_s > bible.get("format", {}).get("max_episode_seconds", 60):
        log.warning(f"UYARI: final sure {duration_s:.1f}sn > 60sn (Shorts siniri)")
    ep["final"] = {"path": final_rel, "duration_s": round(duration_s, 2)}
    state.save_episode(slug, ep)

    _write_qc_report(slug, ep, bible)

    # ─── Drive yukleme ───────────────────────────────────────────────────
    ep["status"] = "uploading"
    state.save_episode(slug, ep)
    series_title = bible.get("series", {}).get("title_tr", slug)
    folder_id, folder_url = drive_service.ensure_series_folder(series_title)
    if folder_id:
        bible.setdefault("drive", {})
        bible["drive"]["folder_id"] = folder_id
        bible["drive"]["folder_url"] = folder_url
        state.save_bible(slug, bible)

    drive_name = "B%03d_%s%s.mp4" % (
        ep["episode_number"],
        _safe_title(ep.get("script", {}).get("title_tr", "")),
        "_TEST" if ep.get("test") else "",
    )
    file_id = None
    if folder_id:
        file_id = drive_service.upload_file_to_folder(str(final_abs), folder_id, drive_name)
        card = state.series_dir(slug) / "kimlik.html"
        if card.exists() and not bible["drive"].get("identity_card_file_id"):
            bible["drive"]["identity_card_file_id"] = drive_service.upload_file_to_folder(
                str(card), folder_id, "kimlik.html", mimetype="text/html"
            )
            state.save_bible(slug, bible)
    ep["final"]["drive_file_id"] = file_id
    ep["final"]["drive_folder_url"] = folder_url
    state.save_episode(slug, ep)

    # ─── Maliyet + hafiza + kapanis ──────────────────────────────────────
    cost_summary = cost.finish()
    ep["cost"] = cost_summary
    state.atomic_write_json(ep_dir / "maliyet.json", cost_summary)

    if ep.get("test"):
        log.info("[TEST] Seri hafizasi ve bolum sayaci guncellenmedi (duman testi)")
    else:
        script = EpisodeScript.model_validate(ep["script"])
        series_state = state.load_series_state(slug)
        memory.update_series_state(series_state, script)
        state.save_series_state(slug, series_state)

        episodes = bible.setdefault("episodes", {"counter": 0, "produced": []})
        episodes["counter"] = max(episodes.get("counter", 0), ep["episode_number"])
        produced = episodes.setdefault("produced", [])
        if not any(p.get("slug") == ep["slug"] for p in produced):
            produced.append({
                "slug": ep["slug"],
                "episode_number": ep["episode_number"],
                "title_tr": ep.get("script", {}).get("title_tr", ""),
                "duration_s": ep["final"]["duration_s"],
                "drive_file_id": file_id,
                "date": _now(),
            })
        state.save_bible(slug, bible)

    ep["status"] = "done"
    ep["timestamps"]["finished"] = _now()
    state.save_episode(slug, ep)

    credits = cost_summary.get("credits_spent")
    kie_usd = cost_summary.get("kie_usd")
    print("\n" + "=" * 60)
    print(f"BOLUM HAZIR: {ep.get('script', {}).get('title_tr', ep['slug'])}")
    print(f"  Dosya     : {final_abs}")
    print(f"  Sure      : {duration_s:.1f} sn ({len(ep['scenes'])} sahne)")
    print(f"  Kie kredi : {credits if credits is not None else 'olculemedi'}"
          + (f" (~${kie_usd})" if kie_usd is not None else ""))
    print(f"  LLM       : ~${cost_summary.get('llm_usd', 0)}")
    print(f"  Drive     : {folder_url or '(DRY_RUN — yuklenmedi)'}")
    print("=" * 60 + "\n")
    return ep
