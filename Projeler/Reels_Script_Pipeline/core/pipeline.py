"""Reels Script Yazarı — uçtan uca pipeline orchestrator.

Sprint 2:
  - Notion karta yazma prod "İçerik DB" DB'sine
  - Asset üretici Anthropic native web_search ile (3-5 gerçek kaynak)
  - Drive parent altında alt-klasör + brief Doc (HTML, h1 başlık, madde aralıklı liste)
  - Notion sayfası sadece script paragrafları + divider + ManyChat bloku
  - ManyChat butonları asset listesinden otomatik beslenir (halüsinasyon yok)
  - Sanitize katmanı (core/sanitize.py) script + asset çıktılarını runtime temizler
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from core.config import Config
from core.drive import create_brief_folder
from core.llm import correct_and_analyze, generate_assets, generate_script, propose_topic
from core.notion_writer import create_reels_card
from core.retrieval import top_k_similar
from core.sanitize import assets_to_buttons, sanitize_assets, sanitize_script_output
from core.state import create_run, update_run
from core.storage import fetch_reel
from core.transcribe import transcribe
@dataclass
class PipelineResult:
    run_id: str
    notion_page_id: str | None = None
    drive_folder_url: str | None = None
    transcript_chars: int = 0
    topic_title: str | None = None
    script_chars: int = 0
    asset_count: int = 0
    stages_done: list[str] = field(default_factory=list)


def _log(prefix: str, msg: str) -> None:
    print(f"  {prefix}  {msg}", flush=True)


def _format_caption(script: dict) -> str:
    hook = (script.get("caption_hook") or "").strip()
    body = (script.get("caption_body") or "").strip()
    parts = [p for p in (hook, body) if p]
    parts.append("ücretsiz reklam")
    return "\n\n".join(parts)


def run_pipeline(
    cfg: Config,
    reels_url: str,
    *,
    source_channel: str = "manuel",
    local_file=None,
    downloader: str = "apify",
    progress: Callable[[str, str], None] | None = None,
    skip_drive: bool = False,
) -> PipelineResult:
    log = progress or _log

    log("🆕", f"Pipeline run başlatılıyor: {reels_url}")
    run = create_run(cfg, reels_url=reels_url, source_channel=source_channel)
    run_id = run["id"]
    result = PipelineResult(run_id=run_id)
    log("📝", f"run_id = {run_id}")

    log("⏬", f"Stage 1: İndirme + Supabase Storage upload (downloader={downloader})...")
    try:
        reel = fetch_reel(cfg, reels_url, local_file=local_file, downloader=downloader)
    except Exception as e:
        update_run(cfg, run_id, stage="error", error_message=f"download: {e}")
        raise
    log("✅", f"Stage 1: {reel.shortcode} → {reel.public_url}")
    update_run(cfg, run_id, stage="downloaded")
    result.stages_done.append("downloaded")

    log("🎤", "Stage 2: HappyScribe transcription...")
    try:
        t = transcribe(
            cfg, reel.public_url, name=f"reels-{reel.shortcode}",
            on_tick=lambda s, e: log("  ⏳", f"   [{e:>3}s] HappyScribe state={s}") if e % 15 == 0 else None,
        )
    except Exception as e:
        update_run(cfg, run_id, stage="error", error_message=f"transcribe: {e}")
        raise
    log("✅", f"Stage 2: transcript {len(t.text)} char (dil={t.language})")
    update_run(cfg, run_id, stage="transcribed")
    result.transcript_chars = len(t.text)
    result.stages_done.append("transcribed")

    log("🧠", "Stage 3: Sonnet — düzeltme + yapısal analiz...")
    analysis = correct_and_analyze(cfg, t.text, source_channel)
    log("✅", f"Stage 3: ana konu='{analysis.get('main_topic', '')[:60]}' | core={analysis.get('core_topic_match')}")
    update_run(cfg, run_id, stage="analyzed")
    result.stages_done.append("analyzed")

    log("💡", "Stage 4: Opus — lokalize konu önerisi...")
    topic = propose_topic(cfg, analysis, source_channel)
    log("✅", f"Stage 4: başlık='{topic.get('baslik')}' confidence={topic.get('confidence_skoru')}")
    update_run(cfg, run_id, stage="topic_proposed", confidence_score=topic.get("confidence_skoru"))
    result.topic_title = topic.get("baslik")
    result.stages_done.append("topic_proposed")

    log("🔍", "Stage 5a: Style corpus retrieval (top-5)...")
    query_text = f"{topic.get('baslik')}\n{topic.get('konu_gerekcesi')}"
    corpus = top_k_similar(cfg, query_text, k=5)
    log("✅", "Stage 5a: " + ", ".join(f"{c['title']} ({c['similarity']:.2f})" for c in corpus))

    log("✍️", "Stage 5b: Opus — Türkçe script (self-edit pass dahil)...")
    script = generate_script(cfg, topic, analysis, corpus)
    script = sanitize_script_output(script, log=lambda p, m: log(p, m))
    log("✅", f"Stage 5b: script {len(script.get('script', ''))} char (~{script.get('tahmini_sure_sn')}sn)")
    update_run(cfg, run_id, stage="script_generated")
    result.script_chars = len(script.get("script", ""))
    result.stages_done.append("script_generated")

    log("🌐", "Stage 6: Opus + web_search — 3-5 gerçek kaynak araştırma...")
    assets = generate_assets(cfg, topic, script)
    assets = sanitize_assets(assets, log=lambda p, m: log(p, m))
    log("✅", f"Stage 6: {len(assets.get('assets', []))} asset (web search ile, sanitize sonrası)")
    update_run(cfg, run_id, stage="assets_collected")
    result.asset_count = len(assets.get("assets", []))
    result.stages_done.append("assets_collected")

    drive_folder_url: str | None = None
    if not skip_drive:
        log("📁", "Stage 7: Drive klasör + Brief Doc oluştur...")
        try:
            drive_out = create_brief_folder(
                cfg,
                title=topic.get("baslik") or "brief",
                assets=assets,
                script_text=script.get("script", ""),
                source_reels_url=reels_url,
                source_channel=source_channel,
            )
            drive_folder_url = drive_out["folder_url"]
            log("✅", f"Stage 7: Drive klasör → {drive_folder_url}")
            update_run(cfg, run_id, stage="drive_created")
            result.stages_done.append("drive_created")
        except Exception as e:
            log("⚠️", f"Stage 7: Drive başarısız ({e}); Notion karta Drive linki konmadan devam edilir")
            update_run(cfg, run_id, error_message=f"drive: {e}")
    result.drive_folder_url = drive_folder_url

    log("📋", "Stage 8: Notion prod DB'ye kart yaz...")
    caption_text = _format_caption(script)
    # ManyChat butonları asset listesinden (web_search ile bulunmuş + sanitize'dan
    # geçmiş gerçek URL'ler) otomatik. LLM halüsinasyonu yerine deterministik köprü.
    manychat = {
        "manychat_trigger_word": script.get("manychat_trigger_word"),
        "manychat_message": script.get("manychat_message"),
        "manychat_buttons": assets_to_buttons(assets, max_buttons=3),
    }
    page_id = create_reels_card(
        cfg,
        title=topic.get("baslik", "(başlıksız)"),
        script_text=script.get("script", ""),
        caption_text=caption_text,
        drive_folder_url=drive_folder_url,
        source_reels_url=reels_url,
        source_channel=source_channel,
        manychat=manychat,
        icon_emoji_id=cfg.notion_emoji_claudecode_id,
    )
    log("✅", f"Stage 8: Notion kart → {page_id}")
    update_run(cfg, run_id, stage="completed", notion_page_id=page_id)
    result.notion_page_id = page_id
    result.stages_done.append("completed")

    return result
