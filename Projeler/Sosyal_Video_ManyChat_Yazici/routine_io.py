"""Deterministik I/O yardımcısı — Notion ile TÜM deterministik alışveriş burada.

Bu hat Anthropic API'ye HİÇ dokunmaz (maliyetsiz). Yaratıcı işi (web araması + akış metni)
dışarıdan bir model yapar (örn. bir cloud routine'in kendi modeli); bu script Notion
okuma/yazmayı ve defansif temizliği üstlenir.

Kullanım (proje klasöründen):
  python routine_io.py targets
      Hedef videoları JSON listesi olarak stdout'a yazar (max MAX_VIDEOS_PER_RUN).
      Her öğe: {page_id, name, klass, status, script, existing_trigger,
                comments, brief_url, extra_urls}
  python routine_io.py write <page_id> < flow.json
      stdin'den ÇÖZÜMLENMİŞ akışı okur, temizler/doğrular, Notion'a kart panelini yazar.
      flow.json şeması: {"trigger_word": str, "opening": {"text": str, "buttons":
      [{"label": str, "kind": "link", "url": str} | {"label": str, "kind": "continue",
      "goto": str}]}, "messages": [{"id": str, "text": str, "buttons": [...]}],
      "notes": [str]}

Env: NOTION_SOCIAL_TOKEN (veya NOTION_TOKEN) + NOTION_DB_REELS_KAPAK (veya NOTION_DB_ID).
Çıkış kodları: 0 OK · 2 kullanım/giriş hatası · 3 panel zaten var (idempotent atlama).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import notion_service as ns  # noqa: E402
from core import sanitize  # noqa: E402

MAX_VIDEOS = int(os.getenv("MAX_VIDEOS_PER_RUN", "5"))
MIN_SCRIPT_CHARS = int(os.getenv("MIN_SCRIPT_CHARS", "150"))


def _env(key: str, *alts: str) -> str:
    for k in (key, *alts):
        val = os.getenv(k)
        if val:
            return val
    print(f"HATA: env eksik: {key}", file=sys.stderr)
    sys.exit(2)


def _log(*a) -> None:
    print(" ".join(str(x) for x in a), file=sys.stderr)


def cmd_targets(token: str, db_id: str) -> None:
    out = []
    for t in ns.query_targets(token, db_id):
        if len(out) >= MAX_VIDEOS:
            break
        try:
            blocks = ns.get_blocks(token, t["id"])
            if ns.has_manychat_panel(blocks):
                _log(f"atla (panel var): {t['name']}")
                continue
            script = ns.extract_script_text(blocks)
            if len(script) < MIN_SCRIPT_CHARS:
                _log(f"atla (script kısa/{len(script)}): {t['name']}")
                continue
            meta = ns.get_page_meta(token, t["id"])
            out.append({
                "page_id": t["id"],
                "name": t["name"],
                "klass": t["klass"],
                "status": t["status"],
                "script": script,
                "existing_trigger": ns.extract_existing_trigger(script),
                "comments": meta.get("comments") or [],
                "brief_url": meta.get("brief_url"),
                "extra_urls": meta.get("extra_urls") or [],
            })
        except Exception as e:  # noqa: BLE001 — video başına izolasyon
            _log(f"atla (okuma hatası): {t['name']}: {e}")
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()


def _clean_buttons(raw, valid_ids: set[str], where: str) -> list[dict]:
    """Model çıktısındaki butonları doğrula: link → canlı http URL, devam → gerçek id."""
    cleaned = []
    for b in raw or []:
        label = sanitize.strip_em_dash((b.get("label") or "").strip())[:25]
        kind = b.get("kind")
        if not label or kind not in ("link", "continue"):
            continue
        if kind == "link":
            url = (b.get("url") or "").strip()
            asset = {"url": url, "aciklama": label}
            if not url.startswith("http") or not sanitize._asset_is_valid(asset, _log):
                _log(f"[{where}] link butonu '{label}' geçersiz/yasak URL, düştü")
                continue
            if not sanitize._asset_url_reachable(url, _log):
                _log(f"[{where}] link butonu '{label}' ölü URL, düştü: {url}")
                continue
            cleaned.append({"label": label, "kind": "link", "url": url})
        else:
            goto = (b.get("goto") or "").strip()
            if goto not in valid_ids:
                _log(f"[{where}] devam butonu '{label}' geçersiz goto={goto!r}, düştü")
                continue
            cleaned.append({"label": label, "kind": "continue", "goto": goto})
    return cleaned


def _resolve(flow: dict) -> dict:
    """Routine modelinin akışını temizle + bütünlüğü doğrula (URL'ler zaten gerçek)."""
    messages_src = {m.get("id"): m for m in (flow.get("messages") or []) if m.get("id")}
    valid_ids = set(messages_src.keys())

    opening = {
        "text": sanitize.clean_message_text((flow.get("opening") or {}).get("text") or "", _log),
        "buttons": _clean_buttons((flow.get("opening") or {}).get("buttons"), valid_ids, "açılış"),
    }

    # Açılıştan erişilebilen mesajları sırayla topla (BFS) — kopuk mesaj panele girmez.
    order, seen = [], set()
    queue = [b["goto"] for b in opening["buttons"] if b["kind"] == "continue"]
    while queue:
        mid = queue.pop(0)
        if mid in seen or mid not in messages_src:
            continue
        seen.add(mid)
        order.append(mid)
        for b in messages_src[mid].get("buttons") or []:
            if b.get("kind") == "continue":
                queue.append((b.get("goto") or "").strip())

    messages = []
    for mid in order:
        m = messages_src[mid]
        messages.append({
            "id": mid,
            "text": sanitize.clean_message_text(m.get("text") or "", _log),
            "buttons": _clean_buttons(m.get("buttons"), valid_ids, f"mesaj:{mid}"),
        })
    if valid_ids - seen:
        _log(f"erişilemeyen {len(valid_ids - seen)} mesaj atıldı: {sorted(valid_ids - seen)}")

    notes = []
    for n in flow.get("notes") or []:
        n = sanitize.HEART_EMOJI.sub("", sanitize.strip_em_dash(str(n))).strip()
        if n:
            notes.append(n[:90])

    return {
        "trigger_word": sanitize.clean_trigger_word(flow.get("trigger_word") or ""),
        "opening": opening,
        "messages": messages,
        "notes": notes,
    }


def cmd_write(token: str, page_id: str) -> None:
    try:
        flow = json.load(sys.stdin)
    except Exception as e:  # noqa: BLE001
        print(f"HATA: stdin flow.json okunamadı: {e}", file=sys.stderr)
        sys.exit(2)

    resolved = _resolve(flow)
    if not resolved["opening"]["text"]:
        print("HATA: açılış metni boş, panel yazılmadı", file=sys.stderr)
        sys.exit(2)

    promo = sanitize.find_brand_promo(sanitize.flow_all_text(resolved))
    if promo:
        _log(f"⚠️ akış metninde marka tanıtımı sızdı: {promo}")

    # Yarış güvenliği: yazmadan hemen önce panel var mı diye bir daha bak.
    if ns.has_manychat_panel(ns.get_blocks(token, page_id)):
        _log("panel zaten var, yazılmadı (idempotent)")
        sys.exit(3)

    ns.append_manychat_panel(token, page_id, resolved)
    print(json.dumps({"ok": True, "trigger": resolved["trigger_word"],
                      "cards": 1 + len(resolved["messages"]),
                      "notes": len(resolved["notes"])}, ensure_ascii=False))


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("targets", "write"):
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    token = _env("NOTION_SOCIAL_TOKEN", "NOTION_REELS_TOKEN", "NOTION_TOKEN")
    if sys.argv[1] == "targets":
        db_id = _env("NOTION_DB_REELS_KAPAK", "NOTION_DB_REELS", "NOTION_DB_ID")
        cmd_targets(token, db_id)
    else:
        if len(sys.argv) < 3:
            print("HATA: write <page_id> gerekli", file=sys.stderr)
            sys.exit(2)
        cmd_write(token, sys.argv[2])


if __name__ == "__main__":
    main()
