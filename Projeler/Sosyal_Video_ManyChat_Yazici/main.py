"""Sosyal Video ManyChat Yazıcı — sosyal videolara otonom ManyChat AKIŞI yazıcı (manuel yedek hat).

Notion video DB'sini izler ve videonun ManyChat DM akışını üretir. Bu dosya MANUEL YEDEK
hattıdır: Anthropic API ile uçtan uca üretir. API'siz (maliyetsiz) hat için routine_io.py'a bak.

Tek mod: panel'i olmayan hedef videolara çok adımlı ManyChat akışı yaz (idempotent).
Hedef = ikonu/statüsü config'teki hedef listeye giren videolar (NOTION_TARGET_ICONS /
NOTION_TARGET_STATUSES). İstemediğin ikon/statü atlanır.

Self-improvement CHAT'ten gelir: kullanıcı feedback verir → agents/learnings.md
güncellenir → ilgili panel silinip yeniden üretilir. (Notion satırı okuma yok.)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from core import learnings, llm
from core import notion_service as ns
from core import sanitize
from core.config import Config
from core.logger import get_logger

# Opsiyonel brief içerik cache'i (page_id -> brief metni). Dosya yoksa atlanır.
# Brief metinlerini (örn. bir doküman içeriğini) elle buraya doldurup okutabilirsin.
_BRIEF_CACHE_PATH = Path(__file__).resolve().parent / "_brief_cache.json"


def _load_brief_cache() -> dict:
    if _BRIEF_CACHE_PATH.exists():
        try:
            return json.loads(_BRIEF_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def _build_extra_context(meta: dict, brief_text: str | None) -> str:
    parts: list[str] = []
    if meta.get("comments"):
        parts.append("Sayfa yorumları:\n" + "\n".join(f"- {c}" for c in meta["comments"]))
    if brief_text:
        parts.append("Marka brief (RESMİ kaynak):\n" + brief_text[:4000])
    elif meta.get("brief_url"):
        parts.append(f"Marka brief linki (içerik okunamadı): {meta['brief_url']}")
    if meta.get("extra_urls"):
        parts.append("Sayfadaki ek linkler: " + ", ".join(meta["extra_urls"]))
    return "\n\n".join(parts)


def _make_slog(log):
    def _slog(*a):
        log.info(" ".join(str(x) for x in a))
    return _slog


def _build_flow(cfg: Config, log, name: str, script: str, *, extra_context: str = "") -> tuple[dict, dict]:
    """Asset web_search → çok adımlı akış üret → çözümle/temizle. (resolved, assets)."""
    slog = _make_slog(log)
    assets = llm.generate_assets(cfg, name, script, extra_context=extra_context)
    assets = sanitize.sanitize_assets(assets, log=slog)
    trigger = ns.extract_existing_trigger(script)
    learn = learnings.load_learnings()

    flow = llm.generate_flow(cfg, name, script, assets,
                             existing_trigger=trigger, learnings_text=learn,
                             extra_context=extra_context)
    resolved = sanitize.resolve_flow(flow, assets, log=slog)
    if not resolved.get("trigger_word") and trigger:
        resolved["trigger_word"] = trigger

    promo = sanitize.find_brand_promo(sanitize.flow_all_text(resolved))
    if promo:
        log.warning(f"  ⚠️ Akış metninde marka tanıtımı sızdı: {promo}")
    return resolved, assets


def _preview(resolved: dict) -> str:
    incoming = ns._incoming_label_map(resolved)
    msgs = resolved.get("messages") or []
    id_to_card = {m["id"]: i + 2 for i, m in enumerate(msgs)}
    out = [f"  Tetik: {resolved.get('trigger_word')}"]
    for n in resolved.get("notes") or []:
        out.append(f"  ⚠️ NOT: {n}")

    def _btns(buttons, indent):
        for b in buttons or []:
            if b["kind"] == "link":
                out.append(f"{indent}🔗 [{b['label']}] → {b['url']}")
            else:
                out.append(f"{indent}▶️ [{b['label']}] → KART {id_to_card.get(b.get('goto'), '?')}")

    op = resolved.get("opening") or {}
    out.append("  ┌─ KART 1 · AÇILIŞ")
    out += [f"  │   {l}" for l in (op.get('text') or '').split("\n") if l.strip()]
    _btns(op.get("buttons"), "  │   ")
    for i, m in enumerate(msgs):
        lab = incoming.get(m["id"], m["id"])
        out.append(f"  ┌─ KART {i+2} · '{lab}' butonuna basınca")
        out += [f"  │   {l}" for l in (m.get('text') or '').split("\n") if l.strip()]
        _btns(m.get("buttons"), "  │   ")
    return "\n".join(out)


def run_generate(cfg: Config, log) -> None:
    targets = ns.query_targets(cfg.notion_token, cfg.notion_db_id)
    log.info(f"🎯 {len(targets)} hedef video (reels/ai-factory) bulundu.")
    brief_cache = _load_brief_cache()
    done = 0
    for t in targets:
        if done >= cfg.max_videos:
            log.info(f"⏹ MAX_VIDEOS_PER_RUN={cfg.max_videos} sınırına ulaşıldı, kalanlar sonraki koşumda.")
            break
        name = t["name"]
        try:
            blocks = ns.get_blocks(cfg.notion_token, t["id"])
            if ns.has_manychat_panel(blocks):
                log.info(f"⏭  '{name}': ManyChat paneli zaten var, atlandı.")
                continue
            script = ns.extract_script_text(blocks)
            if len(script) < cfg.min_script_chars:
                log.info(f"⏭  '{name}': script yok/çok kısa ({len(script)} karakter), atlandı.")
                continue

            meta = ns.get_page_meta(cfg.notion_token, t["id"])
            extra = _build_extra_context(meta, brief_cache.get(t["id"]))
            log.info(f"✍️  İşleniyor: '{name}' [{t['klass']}]"
                     + (f" (+{len(meta['comments'])} yorum)" if meta.get("comments") else ""))
            resolved, _assets = _build_flow(cfg, log, name, script, extra_context=extra)

            if cfg.dry_run:
                log.info(f"🧪 DRY_RUN — yazılacaktı:\n{_preview(resolved)}")
                done += 1
                continue

            ns.append_manychat_panel(cfg.notion_token, t["id"], resolved)
            log.info(f"✅ '{name}': ManyChat akışı eklendi (tetik: {resolved.get('trigger_word')}).")
            done += 1
        except Exception as e:  # noqa: BLE001 — video başına izolasyon
            log.error(f"❌ '{name}' işlenemedi: {e}")
    log.info(f"🏁 Tamamlandı — {done} videoya ManyChat akışı yazıldı.")


def main() -> None:
    cfg = Config.from_env()
    log = get_logger("ReelsManyChat")
    log.info(f"🚀 Başlatılıyor — model: {cfg.model} | dry_run: {cfg.dry_run}")
    try:
        run_generate(cfg, log)
    except Exception as e:
        log.error(f"💥 Pipeline hatası: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
