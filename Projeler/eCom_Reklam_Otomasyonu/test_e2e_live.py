"""
E2E LIVE test — Telegram bypass, full pipeline + caption + Upload-Post (TikTok).

3 yeni davranışı uçtan uca doğrular:
  1) Dinamik sahne süreleri (duration_seconds 4-10)
  2) Voice +2.5x boost (audio_volume default 2.5)
  3) Bot diagnostic logging + bug fallback (production_pipeline çıktısı)

Kullanım:
    set -a; source .env; set +a
    .venv/bin/python test_e2e_live.py

Çıktı: e2e_live_result.json + e2e_live_test.log
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime

# ── ffprobe/ffmpeg path injection (static_ffmpeg) ──
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

import config  # fail-fast env validation
from logger import get_logger

from services.openai_service import OpenAIService
from services.perplexity_service import PerplexityService
from services.imgbb_service import ImgBBService
from services.kie_api import KieAIService
from services.elevenlabs_service import ElevenLabsService
from services.replicate_service import ReplicateService
from services.notion_service import NotionService
from services.firecrawl_service import FirecrawlService
from services.upload_post_service import UploadPostService

from core.scenario_engine import ScenarioEngine
from core.production_pipeline import ProductionPipeline
from core.url_data_extractor import URLDataExtractor
from core.caption_generator import CaptionGenerator, build_brief_payload

settings = config.settings
log = get_logger("e2e_live")

# ── Test parametreleri ──
TEST_URL = "https://www.apple.com/tr/shop/buy-airpods/airpods-pro"
TEST_PREFERENCES = {
    "video_format": "9:16",  # TikTok
    "video_style": "Dönüşüm Hikayesi",
    "custom_note": "[E2E TEST — silinecek]",
}
TEST_USER_NAME = "e2e-live-tester"
RESULT_PATH = "e2e_live_result.json"
DOWNLOAD_PATH = "e2e_live_final.mp4"


def _build_services():
    openai_svc = OpenAIService(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
    perplexity_svc = PerplexityService(api_key=settings.PERPLEXITY_API_KEY, base_url=settings.PERPLEXITY_BASE_URL)
    imgbb_svc = ImgBBService(api_key=settings.IMGBB_API_KEY)
    kie_svc = KieAIService(api_key=settings.KIE_API_KEY, base_url=settings.KIE_BASE_URL)
    elevenlabs_svc = ElevenLabsService(api_key=settings.ELEVENLABS_API_KEY, model_id=settings.ELEVENLABS_MODEL)
    replicate_svc = ReplicateService(api_token=settings.REPLICATE_API_TOKEN)
    notion_svc = NotionService(token=settings.NOTION_TOKEN, database_id=settings.NOTION_DB_ID)
    firecrawl_svc = FirecrawlService(api_key=settings.FIRECRAWL_API_KEY)
    upload_post_svc = UploadPostService(
        api_key=settings.UPLOAD_POST_API_KEY,
        profile_name=settings.UPLOAD_POST_PROFILE,
    )

    extractor = URLDataExtractor(openai_service=openai_svc, firecrawl_service=firecrawl_svc)
    engine = ScenarioEngine(openai_service=openai_svc, perplexity_service=perplexity_svc)
    pipeline = ProductionPipeline(
        kie_service=kie_svc,
        elevenlabs_service=elevenlabs_svc,
        replicate_service=replicate_svc,
        notion_service=notion_svc,
        imgbb_service=imgbb_svc,
        is_dry_run=False,
    )
    caption_gen = CaptionGenerator(openai_service=openai_svc)
    return extractor, engine, pipeline, caption_gen, upload_post_svc, openai_svc


async def _progress(step: str, msg: str):
    print(f"  ▸ [{step}] {msg}", flush=True)


def _ffprobe(path: str) -> dict:
    """ffprobe ile format + streams JSON döndürür."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_format", "-show_streams",
        "-print_format", "json",
        path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return {"error": out.stderr}
    return json.loads(out.stdout)


def _ffmpeg_volumedetect(path: str) -> dict:
    """ffmpeg volumedetect ile mean_volume + max_volume (dB)."""
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", path,
        "-af", "volumedetect",
        "-f", "null", "-"
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    log_text = out.stderr  # ffmpeg volumedetect prints to stderr
    res = {"raw_lines": []}
    for line in log_text.splitlines():
        if "mean_volume" in line or "max_volume" in line or "histogram" in line:
            res["raw_lines"].append(line.strip())
            if "mean_volume" in line:
                try:
                    res["mean_volume_db"] = float(line.split("mean_volume:")[1].split("dB")[0].strip())
                except Exception:
                    pass
            if "max_volume" in line:
                try:
                    res["max_volume_db"] = float(line.split("max_volume:")[1].split("dB")[0].strip())
                except Exception:
                    pass
    return res


def _ffprobe_keyframes(path: str, max_frames: int = 200) -> dict:
    """Video stream'in I-frame sayısını ve toplam frame sayısını döndürür."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_frames", "-show_entries", "frame=pict_type,pkt_pts_time,best_effort_timestamp_time",
        "-print_format", "json",
        path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        return {"error": out.stderr}
    try:
        data = json.loads(out.stdout or "{}")
    except Exception:
        return {"error": "json parse failed"}
    frames = data.get("frames") or []
    i_frames = [f for f in frames if f.get("pict_type") == "I"]
    return {
        "total_frames": len(frames),
        "i_frame_count": len(i_frames),
        "i_frame_times": [f.get("best_effort_timestamp_time") for f in i_frames[:20]],
    }


def _download(url: str, target: str) -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=180) as r, open(target, "wb") as f:
            shutil.copyfileobj(r, f)
        return True
    except Exception as e:
        log.error(f"Video indirilemedi: {e}")
        return False


async def main():
    started_at = datetime.utcnow().isoformat() + "Z"
    t0 = time.time()
    report: dict = {
        "started_at_utc": started_at,
        "test_url": TEST_URL,
        "preferences": TEST_PREFERENCES,
        "stages": {},
    }

    extractor, engine, pipeline, caption_gen, upload_svc, openai_svc = _build_services()

    print("=" * 72, flush=True)
    print(f"  E2E LIVE TEST — started {started_at}", flush=True)
    print(f"  URL: {TEST_URL}", flush=True)
    print("=" * 72, flush=True)

    # ────────────────────────────────────────────────────
    # STAGE 1 — URL extract
    # ────────────────────────────────────────────────────
    print("\n[1/7] URL extract — Firecrawl + OpenAI vision", flush=True)
    extract_t = time.time()
    extracted = await extractor.extract(TEST_URL)
    extract_dur = time.time() - extract_t
    report["stages"]["1_extract"] = {
        "elapsed_sec": round(extract_dur, 2),
        "brand_name": extracted.get("brand_name"),
        "product_name": extracted.get("product_name"),
        "ad_concept": (extracted.get("ad_concept") or "")[:300],
        "target_audience": extracted.get("target_audience"),
        "best_image_count": len(extracted.get("best_image_urls") or []),
    }
    print(f"  brand={extracted.get('brand_name')!r}  product={extracted.get('product_name')!r}  ({extract_dur:.1f}s)", flush=True)

    # ────────────────────────────────────────────────────
    # STAGE 2 — Scenario (research + generate)
    # ────────────────────────────────────────────────────
    print("\n[2/7] Research + Scenario (dinamik sahne süresi)", flush=True)
    scen_t = time.time()
    research = await asyncio.to_thread(engine.research, extracted)
    scenario = await asyncio.to_thread(engine.generate_scenario, extracted, research, TEST_PREFERENCES)
    scen_dur = time.time() - scen_t

    scenes = scenario.get("scenes") or []
    durations = [s.get("duration_seconds") for s in scenes]
    total_duration = sum(d for d in durations if isinstance(d, (int, float)))
    report["stages"]["2_scenario"] = {
        "elapsed_sec": round(scen_dur, 2),
        "scene_count": len(scenes),
        "scene_durations": durations,
        "scenario_total_duration_seconds": scenario.get("total_duration_seconds"),
        "scenario_duration_field": scenario.get("duration"),
        "computed_sum_durations": total_duration,
        "narrative_hook": scenario.get("narrative_hook"),
        "narrative_pattern": scenario.get("narrative_pattern"),
        "voiceover_text": scenario.get("voiceover_text"),
        "voiceover_word_count": len((scenario.get("voiceover_text") or "").split()),
        "voice_name": scenario.get("voice_name"),
        "language": scenario.get("language"),
        "aspect_ratio": scenario.get("aspect_ratio"),
        "cost": scenario.get("cost"),
    }
    print(f"  scenes={len(scenes)}  durations={durations}  total={total_duration}s", flush=True)
    print(f"  hook={scenario.get('narrative_hook')!r}", flush=True)
    print(f"  voiceover_words={report['stages']['2_scenario']['voiceover_word_count']}", flush=True)

    # ────────────────────────────────────────────────────
    # STAGE 3 — Production pipeline
    # ────────────────────────────────────────────────────
    print("\n[3/7] Production pipeline (Kie + Seedance + ElevenLabs + Replicate merge)", flush=True)
    prod_t = time.time()
    result = await pipeline.produce(
        scenario=scenario,
        collected_data=extracted,
        progress_callback=_progress,
        user_name=TEST_USER_NAME,
        preferences=TEST_PREFERENCES,
    )
    prod_dur = time.time() - prod_t
    report["stages"]["3_pipeline"] = {
        "elapsed_sec": round(prod_dur, 2),
        "status": result.get("status"),
        "video_url": result.get("video_url"),
        "raw_video_url": result.get("raw_video_url"),
        "audio_url": result.get("audio_url"),
        "notion_page_url": result.get("notion_page_url"),
        "error": result.get("error"),
        "cost": result.get("cost"),
        "brief_payload_present": bool(result.get("brief_payload")),
    }
    print(f"  status={result.get('status')}  ({prod_dur:.1f}s)", flush=True)
    print(f"  video_url={result.get('video_url')}", flush=True)
    print(f"  notion={result.get('notion_page_url')}", flush=True)

    if result.get("status") != "success":
        report["fatal"] = "Pipeline failed — sonraki aşamalar atlandı."
        with open(RESULT_PATH, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        print("\n❌ Pipeline başarısız — rapor kaydedildi.", flush=True)
        return

    video_url = result.get("video_url")
    brief_payload = result.get("brief_payload") or build_brief_payload(
        collected_data=extracted,
        preferences=TEST_PREFERENCES,
        scenario=scenario,
        video_url=video_url,
        language="tr",
    )

    # ────────────────────────────────────────────────────
    # STAGE 4 — Caption (TikTok)
    # ────────────────────────────────────────────────────
    print("\n[4/7] Caption üretimi — TikTok", flush=True)
    cap_t = time.time()
    try:
        captions = await asyncio.to_thread(caption_gen.generate, brief_payload, ["tiktok"])
        cap_dur = time.time() - cap_t
        report["stages"]["4_caption"] = {
            "elapsed_sec": round(cap_dur, 2),
            "captions": captions,
            "error": None,
        }
        print(f"  tiktok caption: {captions.get('tiktok')}", flush=True)
    except Exception as cap_err:
        report["stages"]["4_caption"] = {
            "elapsed_sec": round(time.time() - cap_t, 2),
            "captions": None,
            "error": f"{type(cap_err).__name__}: {cap_err}",
        }
        captions = {"tiktok": {"caption": "Test post", "hashtags": ["test"]}}
        print(f"  ⚠️ caption hata: {cap_err}", flush=True)

    # ────────────────────────────────────────────────────
    # STAGE 5 — Upload-Post → TikTok (test post)
    # ────────────────────────────────────────────────────
    print("\n[5/7] Upload-Post (TikTok) — test post", flush=True)
    up_t = time.time()
    upload_resp = None
    poll_outcome = None
    try:
        # Connected platform pre-check
        connected = await asyncio.to_thread(upload_svc.list_connected_platforms)
        tiktok_info = connected.get("tiktok") or {}
        report["stages"]["5_upload_post"] = {
            "tiktok_connected": tiktok_info.get("connected"),
            "tiktok_username": tiktok_info.get("username"),
        }
        if not tiktok_info.get("connected"):
            raise RuntimeError(f"TikTok bağlı değil — profil={settings.UPLOAD_POST_PROFILE}")

        upload_resp = await asyncio.to_thread(
            upload_svc.upload_video,
            video_url,
            ["tiktok"],
            captions,
            True,
        )
        report["stages"]["5_upload_post"]["upload_response"] = upload_resp
        request_id = upload_resp.get("request_id")
        print(f"  upload OK → request_id={request_id}", flush=True)

        # Polling — TikTok upload genelde 30-90s sürer; biraz cömert ver.
        poll_t = time.time()
        poll_outcome = await asyncio.to_thread(upload_svc.poll_status, request_id, 240, 10)
        poll_dur = time.time() - poll_t
        report["stages"]["5_upload_post"]["polling_elapsed_sec"] = round(poll_dur, 2)
        report["stages"]["5_upload_post"]["poll_outcome"] = poll_outcome
        print(f"  poll → status={poll_outcome.get('status')}  ({poll_dur:.1f}s)", flush=True)
        # Post URL extraction
        tiktok_result = (poll_outcome.get("results") or {}).get("tiktok", {})
        report["stages"]["5_upload_post"]["tiktok_post_url"] = tiktok_result.get("post_url")
    except Exception as up_err:
        report["stages"].setdefault("5_upload_post", {})["error"] = f"{type(up_err).__name__}: {up_err}"
        report["stages"]["5_upload_post"]["traceback"] = traceback.format_exc()[-1500:]
        print(f"  ⚠️ upload hata: {up_err}", flush=True)
    report["stages"]["5_upload_post"]["elapsed_sec_total"] = round(time.time() - up_t, 2)

    # ────────────────────────────────────────────────────
    # STAGE 6 — Final video download + ffprobe + volumedetect
    # ────────────────────────────────────────────────────
    print("\n[6/7] Final video indir + ffprobe", flush=True)
    if _download(video_url, DOWNLOAD_PATH):
        size_bytes = os.path.getsize(DOWNLOAD_PATH)
        probe = _ffprobe(DOWNLOAD_PATH)
        vol = _ffmpeg_volumedetect(DOWNLOAD_PATH)
        kf = _ffprobe_keyframes(DOWNLOAD_PATH)

        # Stream summary
        streams_summary = []
        format_info = probe.get("format") or {}
        for s in probe.get("streams") or []:
            entry = {
                "type": s.get("codec_type"),
                "codec": s.get("codec_name"),
                "duration_sec": float(s.get("duration") or 0) if s.get("duration") else None,
            }
            if s.get("codec_type") == "video":
                entry.update({
                    "width": s.get("width"),
                    "height": s.get("height"),
                    "fps": s.get("r_frame_rate"),
                })
            elif s.get("codec_type") == "audio":
                entry.update({
                    "sample_rate": s.get("sample_rate"),
                    "channels": s.get("channels"),
                })
            streams_summary.append(entry)

        report["stages"]["6_video_analysis"] = {
            "downloaded_path": DOWNLOAD_PATH,
            "size_mb": round(size_bytes / 1_048_576, 2),
            "format_duration_sec": float(format_info.get("duration") or 0) if format_info.get("duration") else None,
            "format_size": format_info.get("size"),
            "format_bitrate": format_info.get("bit_rate"),
            "streams": streams_summary,
            "audio_levels": vol,
            "keyframes": kf,
            "scenario_planned_total_seconds": total_duration,
        }
        # Console özet
        print(f"  size={size_bytes/1e6:.1f}MB  format_duration={format_info.get('duration')}", flush=True)
        for s in streams_summary:
            print(f"  stream {s['type']}: {s}", flush=True)
        print(f"  audio levels: mean={vol.get('mean_volume_db')}dB  max={vol.get('max_volume_db')}dB", flush=True)
        print(f"  keyframes: total={kf.get('total_frames')}  I={kf.get('i_frame_count')}", flush=True)
    else:
        report["stages"]["6_video_analysis"] = {"error": "download failed"}

    # ────────────────────────────────────────────────────
    # STAGE 7 — Wrap-up
    # ────────────────────────────────────────────────────
    elapsed_total = time.time() - t0
    report["finished_at_utc"] = datetime.utcnow().isoformat() + "Z"
    report["total_elapsed_sec"] = round(elapsed_total, 1)

    with open(RESULT_PATH, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n📄 Sonuç kaydedildi: {RESULT_PATH}", flush=True)
    print(f"⏱  Toplam süre: {elapsed_total:.1f}s", flush=True)

    # Kompakt JSON yazdır (parent agent için)
    print("\n=== JSON REPORT ===", flush=True)
    print(json.dumps({
        "pipeline_status": report["stages"]["3_pipeline"]["status"],
        "scenario_durations": report["stages"]["2_scenario"]["scene_durations"],
        "scenario_total_seconds": total_duration,
        "video_format_duration": report["stages"].get("6_video_analysis", {}).get("format_duration_sec"),
        "audio_mean_db": report["stages"].get("6_video_analysis", {}).get("audio_levels", {}).get("mean_volume_db"),
        "audio_max_db": report["stages"].get("6_video_analysis", {}).get("audio_levels", {}).get("max_volume_db"),
        "tiktok_post_url": report["stages"].get("5_upload_post", {}).get("tiktok_post_url"),
        "cost": report["stages"]["3_pipeline"]["cost"],
    }, indent=2, ensure_ascii=False, default=str), flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
        sys.exit(2)
