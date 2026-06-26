"""Notion writer — "İçerik DB" production DB'ye kart yazar.

Sprint 2: pipeline-özel ayrı DB YOK. Mevcut prod DB'nin property'lerini doldur.
Sayfa içine sadece okunacak script paragrafları girer (heading yok).
"""

from __future__ import annotations

import httpx

from core.config import Config

NOTION_VERSION = "2022-06-28"

EXPECTED_PROPS: dict[str, str] = {
    "Name": "title",
    "Status": "select",
    "Caption": "rich_text",
    "Breif link": "url",
    "Collab, #, @, vs.": "rich_text",
    "Drive": "url",
}
EXPECTED_STATUS_OPTION = "Çekime Hazır"


def _hdr(cfg: Config) -> dict:
    return {
        "Authorization": f"Bearer {cfg.notion_token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _rt(text: str) -> list[dict]:
    """Notion rich_text yardımcı — 2000 char chunking."""
    chunks = []
    for i in range(0, len(text), 1900):
        chunks.append({"type": "text", "text": {"content": text[i : i + 1900]}})
    return chunks or [{"type": "text", "text": {"content": ""}}]


def _p(text: str) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": _rt(text)}}


def verify_prod_schema(cfg: Config) -> None:
    """Pre-flight: prod DB property adları + type'ları + Status enum'unda
    'Script Onayı Bekliyor' var mı kontrol et. Drift varsa pipeline durur,
    Notion'a yazma denemesi yapılmaz."""
    r = httpx.get(
        f"https://api.notion.com/v1/databases/{cfg.notion_reels_prod_db_id}",
        headers=_hdr(cfg),
        timeout=20,
    )
    if r.status_code >= 300:
        raise RuntimeError(
            f"Notion prod DB schema okunamadı (HTTP {r.status_code}): {r.text[:300]}"
        )
    db = r.json()
    title = "".join(t.get("plain_text", "") for t in db.get("title", []))
    props = db.get("properties", {})
    drift: list[str] = []
    for name, want_type in EXPECTED_PROPS.items():
        prop = props.get(name)
        if prop is None:
            drift.append(f"eksik property: {name!r}")
            continue
        if prop.get("type") != want_type:
            drift.append(f"property {name!r} type {prop.get('type')!r} (beklenen {want_type!r})")
    status_prop = props.get("Status")
    if status_prop and status_prop.get("type") == "select":
        opt_names = {o.get("name") for o in status_prop.get("select", {}).get("options", [])}
        if EXPECTED_STATUS_OPTION not in opt_names:
            drift.append(f"Status enum'unda {EXPECTED_STATUS_OPTION!r} yok")
    if drift:
        raise RuntimeError(
            f"Notion prod DB schema drift ({title!r}): " + "; ".join(drift)
        )


def _post_write_verify(
    cfg: Config,
    page_id: str,
    *,
    expected_title: str,
    expected_source_url: str,
) -> None:
    """Self-review: kartı GET'le geri oku, Name/Status/Breif link beklenenle uyuşuyor mu."""
    r = httpx.get(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=_hdr(cfg),
        timeout=20,
    )
    if r.status_code >= 300:
        raise RuntimeError(
            f"Notion kart geri okunamadı (HTTP {r.status_code}, page={page_id}): {r.text[:300]}"
        )
    props = r.json().get("properties", {})
    diffs: list[str] = []
    name_parts = props.get("Name", {}).get("title", [])
    got_title = "".join(p.get("plain_text", "") for p in name_parts)
    if got_title != expected_title:
        diffs.append(f"Name {got_title!r} ≠ {expected_title!r}")
    status_name = (props.get("Status", {}).get("select") or {}).get("name")
    if status_name != EXPECTED_STATUS_OPTION:
        diffs.append(f"Status {status_name!r} ≠ {EXPECTED_STATUS_OPTION!r}")
    got_url = props.get("Breif link", {}).get("url")
    if got_url != expected_source_url:
        diffs.append(f"Breif link {got_url!r} ≠ {expected_source_url!r}")
    if diffs:
        raise RuntimeError(
            f"Notion kart self-review başarısız (page={page_id}): " + "; ".join(diffs)
        )


def create_reels_card(
    cfg: Config,
    *,
    title: str,
    script_text: str,
    caption_text: str,
    drive_folder_url: str | None,
    source_reels_url: str,
    source_channel: str,
    manychat: dict | None = None,
    icon_emoji_id: str | None = None,
) -> str:
    """Prod Reels DB'sine kart yarat. page_id döndürür.

    Şema (mevcut prod DB):
      - Name (title)
      - Drive (url) — editör asset Doc'una giden klasör URL'i
      - Caption (text) — hook + body + "ücretsiz reklam"
      - Status (select) — "Script Onayı Bekliyor"
      - Breif link (url) — kaynak reels URL'i
      - Collab, #, @, vs. (text) — kaynak kanal handle'ı
    """
    verify_prod_schema(cfg)

    properties: dict = {
        "Name": {"title": _rt(title)[:1]},
        "Status": {"select": {"name": EXPECTED_STATUS_OPTION}},
        "Caption": {"rich_text": _rt(caption_text)},
        "Breif link": {"url": source_reels_url},
        "Collab, #, @, vs.": {"rich_text": _rt(source_channel)},
    }
    if drive_folder_url:
        properties["Drive"] = {"url": drive_folder_url}

    children = _build_script_body(script_text, manychat=manychat)

    body: dict = {
        "parent": {"database_id": cfg.notion_reels_prod_db_id},
        "properties": properties,
        "children": children,
    }
    if icon_emoji_id:
        body["icon"] = {"type": "custom_emoji", "custom_emoji": {"id": icon_emoji_id}}

    r = httpx.post("https://api.notion.com/v1/pages", headers=_hdr(cfg), json=body, timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(f"Notion create_page HTTP {r.status_code}: {r.text[:400]}")
    page_id = r.json()["id"]
    _post_write_verify(
        cfg, page_id,
        expected_title=title,
        expected_source_url=source_reels_url,
    )
    return page_id


def _build_script_body(script_text: str, *, manychat: dict | None = None) -> list[dict]:
    """Script paragrafları + (opsiyonel) altta ManyChat 3-satır cevap akışı.
    Heading kullanmaz — divider + bold-prefixed paragraflar ile ayırır."""
    blocks: list[dict] = []
    for para in (script_text or "").split("\n\n"):
        para = para.strip()
        if para:
            blocks.append(_p(para))
    if not blocks:
        blocks = [_p("(script üretilemedi)")]

    if manychat:
        trigger = (manychat.get("manychat_trigger_word") or "").strip()
        message = (manychat.get("manychat_message") or "").strip()
        buttons = manychat.get("manychat_buttons") or []
        if trigger or message or buttons:
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            blocks.append(_bold_para(f"ManyChat — yoruma {trigger or '(...)'} yazana DM"))
            if message:
                import re as _re
                clean = _re.sub(r"<br\s*/?>", "\n", message, flags=_re.IGNORECASE)
                for line in clean.split("\n"):
                    line = line.strip()
                    if line:
                        blocks.append(_p(line))
            for j, btn in enumerate(buttons):
                btn_text = (btn.get("text") or "").strip()
                btn_url = (btn.get("url") or "").strip()
                label_prefix = f"Buton {j+1}: " if len(buttons) > 1 else "Buton: "
                if btn_text and btn_url:
                    blocks.append(_labeled_para(label_prefix, f"{btn_text} → {btn_url}"))

    return blocks[:95]


def _bold_para(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": text[:1900]},
                "annotations": {"bold": True},
            }],
        },
    }


def _labeled_para(label: str, value: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": label}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": value[:1900]}},
            ],
        },
    }
