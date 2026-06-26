"""Notion servisi — video DB'sini sorgular, script okur, ManyChat panelini yazar.

Sorumluluklar:
  - query_targets: ikon ile hedef videoları seç (hedef ikon/statü listesi config'ten gelir).
  - extract_script_text: sayfadaki insan script'ini al (panellerden önce).
  - has_manychat_panel: ManyChat paneli zaten var mı (idempotent atlama).
  - build_panel_blocks / append_manychat_panel: çok adımlı akışı KART KART (callout) göster + yaz.
  - delete_manychat_panel: eski paneli silip yeniden yaz.

Gösterim "management arayüzü" hissinde: her mesaj balonu renkli bir KART (Notion callout).
Kartlar numaralı (KART 1 = açılış); butonlar "→ KART N'e gider" diye hedef kartı söyler, böylece
hangi butona basınca ne geleceği net olur.

Tip ayrımı page-level custom_emoji (sayfa ikonu) adıyla yapılır.
"""

from __future__ import annotations

import os
import re

import httpx

NOTION_VERSION = "2022-06-28"
API = "https://api.notion.com/v1"

# Yeni panel başlığı (bu projenin yazdığı). Eski format ("ManyChat — yoruma …") da
# silme/atlama tespiti için tanınır (eski tohum panelleri temizlenebilsin).
PANEL_HEADER = "📨 ManyChat akışı"
_OLD_PANEL_PREFIX = "ManyChat — yoruma"
COVER_PANEL_MARKERS = ("REVİZYON PANEL", "KAPAK REVİZYON")

def _env_set(key: str, default: set[str]) -> set[str]:
    """Virgülle ayrılmış env değerini set'e çevir; boşsa default kullan."""
    raw = (os.getenv(key) or "").strip()
    if not raw:
        return default
    return {x.strip() for x in raw.split(",") if x.strip()}


# Hedef SINIF = sayfa ikonunun (custom emoji) classify_icon çıktısı.
# Kendi Notion şemana göre NOTION_TARGET_ICONS ile değiştir (virgülle ayır).
# Örnek varsayılan: sadece "reels" ve "ai-factory" ikonlu kartlar işlenir.
TARGET_CLASSES = _env_set("NOTION_TARGET_ICONS", {"reels", "ai-factory"})

# Sadece bu olgunluk statülerindeki videolara ManyChat yazılır.
# Video bu aşamaya gelince (script kesinleşmiş, çekilmiş/draft) araya girip metni yazıyoruz.
# Kendi statü adlarınla NOTION_TARGET_STATUSES env'i ile değiştir (virgülle ayır).
TARGET_STATUSES = _env_set("NOTION_TARGET_STATUSES", {
    "Çekime Hazır",
    "Çekildi - Edit YOK",
    "Çekildi - Edit TAMAM",
    "Draft Onayı Bekliyor",
})

# Kart renkleri (Notion callout background).
_OPENING_COLOR = "blue_background"
_MSG_COLOR = "gray_background"
_TITLE_COLOR = "brown_background"

# Scriptte söz verilen tetik kelimeyi yakala: "yoruma GÖNDER yaz" / "GÖNDER yazana" / "GÖNDER yaz".
# RE3 IGNORECASE DEĞİL: tetik tokenı büyük harf olmalı (normal cümlede "X yaz" eşleşmesin).
_TRIGGER_RE = re.compile(r"yoru\w*\s+([A-ZÇĞIİÖŞÜ]{2,15})\s+yaz", re.IGNORECASE | re.UNICODE)
_TRIGGER_RE2 = re.compile(r"\b([A-ZÇĞIİÖŞÜ]{3,15})\s+yazana", re.UNICODE)
_TRIGGER_RE3 = re.compile(r"\b([A-ZÇĞIİÖŞÜ]{3,15})\s+yaz\b", re.UNICODE)


def _hdr(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


# ─── İkon sınıflama ──────────────────────────────────────────────────────────


def classify_icon(item: dict) -> str:
    """Sayfa ikonunun (custom emoji) adından kategori slug'ı üretir.

    Aşağıdaki eşleme ÖRNEKtir; kendi Notion ikon adlandırmana göre düzenle.
    Döner: youtube | claudecode | reels | ai-factory | other. Hangi slug'ların hedef
    sayılacağı TARGET_CLASSES (NOTION_TARGET_ICONS env'i) ile ayarlanır.
    """
    icon = item.get("icon") or {}
    if icon.get("type") != "custom_emoji":
        return "other"
    name = ((icon.get("custom_emoji") or {}).get("name") or "").lower()
    if "youtube" in name:
        return "youtube"
    if "claude" in name:
        return "claudecode"
    if name == "reels":
        return "reels"
    if name.startswith("ai-factory") or name.startswith("ai_factory") or name == "aifactory":
        return "ai-factory"
    return "other"


def _page_name(item: dict) -> str:
    np_ = item.get("properties", {}).get("Name", {}).get("title", [])
    return np_[0].get("plain_text", "İsimsiz") if np_ else "İsimsiz"


def _page_status(item: dict) -> str | None:
    sel = (item.get("properties", {}).get("Status", {}) or {}).get("select") or {}
    return sel.get("name")


def query_targets(token: str, db_id: str) -> list[dict]:
    """Hedef videoları döndür: reels/ai-factory ikonlu VE statüsü TARGET_STATUSES'ta olanlar.
    Statü filtresi server-side (payload), ikon filtresi client-side (ikon property değil).
    Liste: {id, name, klass, status}. Tüm sayfalar paginate edilir."""
    out: list[dict] = []
    cursor = None
    status_filter = {"or": [{"property": "Status", "select": {"equals": s}} for s in TARGET_STATUSES]}
    while True:
        payload: dict = {"page_size": 100, "filter": status_filter}
        if cursor:
            payload["start_cursor"] = cursor
        r = httpx.post(f"{API}/databases/{db_id}/query", headers=_hdr(token), json=payload, timeout=40)
        if r.status_code >= 300:
            raise RuntimeError(f"Notion DB query HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        for item in data.get("results", []):
            klass = classify_icon(item)
            if klass in TARGET_CLASSES:
                out.append({"id": item["id"], "name": _page_name(item),
                            "klass": klass, "status": _page_status(item)})
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return out


# ─── Sayfa içeriği ───────────────────────────────────────────────────────────


def get_blocks(token: str, page_id: str) -> list[dict]:
    """Sayfanın tüm üst-seviye bloklarını döndür (paginate)."""
    blocks: list[dict] = []
    cursor = None
    while True:
        url = f"{API}/blocks/{page_id}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"
        r = httpx.get(url, headers=_hdr(token), timeout=40)
        if r.status_code >= 300:
            raise RuntimeError(f"Notion blocks HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return blocks


def _block_text(block: dict) -> str:
    """Bloğun düz metni. Notion'dan OKUNAN bloklar 'plain_text' taşır; lokal İNŞA edilen
    bloklar 'text.content' taşır — ikisini de destekle (round-trip tespiti çalışsın)."""
    t = block.get("type")
    payload = block.get(t)
    if isinstance(payload, dict):
        return "".join(
            x.get("plain_text") or (x.get("text") or {}).get("content") or ""
            for x in payload.get("rich_text", [])
        )
    return ""


def _is_panel_header_text(txt: str) -> bool:
    t = (txt or "").strip()
    return ("ManyChat akışı" in t) or t.startswith(_OLD_PANEL_PREFIX)


def _is_header_block(block: dict) -> bool:
    """Blok, ManyChat panel başlığı mı (paragraf VEYA callout VEYA heading olabilir)."""
    if block.get("type") in ("paragraph", "callout", "heading_1", "heading_2", "heading_3"):
        return _is_panel_header_text(_block_text(block))
    return False


def _is_panel_start(block: dict) -> bool:
    """Blok bir panelin başlangıcı mı (ManyChat paneli veya kapak revizyon paneli)."""
    if _is_header_block(block):
        return True
    if block.get("type") in ("heading_1", "heading_2", "heading_3"):
        up = _block_text(block).upper()
        if any(m in up for m in COVER_PANEL_MARKERS):
            return True
    return False


def extract_script_text(blocks: list[dict]) -> str:
    """İnsan script'ini al: panel (ManyChat veya kapak) başlayana kadar olan paragraflar.
    Divider tek başına sınır DEĞİL (script içinde divider olabilir); panel başlığı sınırdır."""
    lines: list[str] = []
    for b in blocks:
        if _is_panel_start(b):
            break
        if b.get("type") in ("paragraph", "heading_1", "heading_2", "heading_3",
                             "bulleted_list_item", "numbered_list_item", "quote"):
            txt = _block_text(b)
            if txt.strip():
                # reels pipeline'ın "🎬 Açılış cümlesi" hook bloğunu script'e karıştırma
                if txt.strip().startswith("🎬 Açılış"):
                    continue
                lines.append(txt.strip())
    return "\n".join(lines).strip()


def has_manychat_panel(blocks: list[dict]) -> bool:
    return any(_is_header_block(b) for b in blocks)


def extract_existing_trigger(script_text: str) -> str | None:
    for rx in (_TRIGGER_RE, _TRIGGER_RE2, _TRIGGER_RE3):
        m = rx.search(script_text or "")
        if m:
            return m.group(1).upper()
    return None


def get_page_meta(token: str, page_id: str) -> dict:
    """Sayfa properties + yorumlarını oku — ekstra kaynak (kupon, affiliate link, marka brief) için.

    Döner: {brief_url, extra_urls, comments}. Yorumlarda kupon kodu/indirim/resmi link
    olabilir (örn. bir markanın indirim kodu). Brief URL'i markanın resmi doküman linki olabilir.
    Drive ASSET klasörü (drive.google.com/.../folders) atlanır — DM kaynağı değil.
    """
    brief_url: str | None = None
    extra_urls: list[str] = []
    comments: list[str] = []
    try:
        pr = httpx.get(f"{API}/pages/{page_id}", headers=_hdr(token), timeout=30)
        if pr.status_code < 300:
            for name, p in (pr.json().get("properties") or {}).items():
                if p.get("type") == "url":
                    val = (p.get("url") or "").strip()
                    if not val.startswith("http"):
                        continue
                    if "brei" in name.lower() or "brief" in name.lower():
                        brief_url = val
                    elif "drive.google.com/drive/folders" not in val:
                        extra_urls.append(val)
    except Exception:  # noqa: BLE001 — meta opsiyonel, asla pipeline'ı düşürme
        pass
    try:
        cr = httpx.get(f"{API}/comments?block_id={page_id}", headers=_hdr(token), timeout=30)
        if cr.status_code < 300:
            for c in cr.json().get("results", []):
                txt = "".join(x.get("plain_text", "") for x in c.get("rich_text", [])).strip()
                if txt:
                    comments.append(txt)
    except Exception:  # noqa: BLE001
        pass
    return {"brief_url": brief_url, "extra_urls": extra_urls, "comments": comments}


# ─── Notion blok kurucuları ──────────────────────────────────────────────────


def _rt(text: str) -> list[dict]:
    chunks = []
    for i in range(0, len(text), 1900):
        chunks.append({"type": "text", "text": {"content": text[i:i + 1900]}})
    return chunks or [{"type": "text", "text": {"content": ""}}]


def _rt_bold(text: str, color: str = "default") -> list[dict]:
    return [{"type": "text", "text": {"content": text[:1900]},
             "annotations": {"bold": True, "color": color}}]


def _p(text: str) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": _rt(text)}}


def _callout(title_rt: list[dict], icon: str, color: str, children: list[dict]) -> dict:
    return {"object": "block", "type": "callout", "callout": {
        "rich_text": title_rt, "icon": {"type": "emoji", "emoji": icon},
        "color": color, "children": children}}


def _code(text: str) -> dict:
    """Notion code bloğu — Notion otomatik 'kopyala' butonu koyar (tek tık kopya)."""
    return {"object": "block", "type": "code", "code": {
        "rich_text": _rt(text or ""), "language": "plain text"}}


def _label(text: str, color: str = "default") -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {
        "rich_text": [{"type": "text", "text": {"content": text[:1900]},
                       "annotations": {"bold": True, "color": color}}]}}


def _incoming_label_map(resolved: dict) -> dict[str, str]:
    """Her takip mesajı id'sine, ona giden devam butonunun etiketini eşle (ilk gelen)."""
    out: dict[str, str] = {}
    sources = [resolved.get("opening", {})] + list(resolved.get("messages") or [])
    for src in sources:
        for b in src.get("buttons") or []:
            if b.get("kind") == "continue":
                goto = b.get("goto")
                if goto and goto not in out:
                    out[goto] = b.get("label") or goto
    return out


def _card_children(text: str, buttons: list[dict], id_to_card: dict[str, int]) -> list[dict]:
    """Kart içeriği: kopyalanabilir code blokları. Her copy-edilecek parça ayrı code bloğu."""
    children: list[dict] = [_label("Mesaj"), _code(text or "")]
    for b in buttons or []:
        if b.get("kind") == "link":
            children.append(_label("Buton adı", color="blue"))
            children.append(_code(b["label"]))
            children.append(_label("Buton linki", color="blue"))
            children.append(_code(b["url"]))
        else:
            tgt = id_to_card.get(b.get("goto"), "?")
            children.append(_label(f"Buton adı  ·  ▶ KART {tgt} açılır", color="purple"))
            children.append(_code(b["label"]))
    return children


def build_panel_blocks(resolved: dict) -> list[dict]:
    """Akışı KART KART (callout) göster, her kopyalanabilir parça code bloğu (tek-tık kopya).

    divider + tetik kartı + KART 1 (açılış) + her takip mesajı için numaralı kart.
    """
    trigger = (resolved.get("trigger_word") or "").strip() or "(...)"
    opening = resolved.get("opening") or {}
    messages = resolved.get("messages") or []
    incoming = _incoming_label_map(resolved)
    id_to_card = {m["id"]: i + 2 for i, m in enumerate(messages)}  # KART 1 = açılış

    blocks: list[dict] = [{"object": "block", "type": "divider", "divider": {}}]

    # Tetik kartı — sadece yoruma yazılan kelime (kopyalanabilir)
    blocks.append(_callout(
        _rt_bold(f"{PANEL_HEADER} · Tetik kelime"), "🎯", _TITLE_COLOR, [_code(trigger)],
    ))

    # Not kartı — kullanıcı kopyalamadan önce kontrol etsin (varsa)
    notes = [n for n in (resolved.get("notes") or []) if str(n).strip()]
    if notes:
        blocks.append(_callout(
            _rt_bold("Kopyalamadan önce kontrol et"), "⚠️", "yellow_background",
            [_p(f"• {n}") for n in notes],
        ))

    # KART 1 — açılış
    blocks.append(_callout(
        _rt_bold("KART 1 · AÇILIŞ"), "📣", _OPENING_COLOR,
        _card_children(opening.get("text"), opening.get("buttons"), id_to_card),
    ))

    # Takip kartları (erişim sırasıyla)
    for i, m in enumerate(messages):
        n = i + 2
        lab = incoming.get(m["id"], m["id"])
        blocks.append(_callout(
            _rt_bold(f'KART {n} · "{lab}"'), "💬", _MSG_COLOR,
            _card_children(m.get("text"), m.get("buttons"), id_to_card),
        ))

    return blocks


def append_manychat_panel(token: str, page_id: str, resolved: dict) -> bool:
    blocks = build_panel_blocks(resolved)
    r = httpx.patch(f"{API}/blocks/{page_id}/children", headers=_hdr(token),
                    json={"children": blocks}, timeout=40)
    if r.status_code >= 300:
        raise RuntimeError(f"Notion panel append HTTP {r.status_code}: {r.text[:300]}")
    return True


def delete_manychat_panel(token: str, page_id: str, blocks: list[dict]) -> int:
    """ManyChat panelini sil: başlığından (önündeki divider dahil) sayfa sonuna kadar.
    Panel her zaman sayfanın sonunda olduğu için aralık güvenle silinir. Silinen blok sayısı.
    (Callout'lar silinince Notion alt bloklarını da otomatik siler.)"""
    start = None
    for i, b in enumerate(blocks):
        if _is_header_block(b):
            start = i
            break
    if start is None:
        return 0
    if start > 0 and blocks[start - 1].get("type") == "divider":
        start -= 1
    deleted = 0
    for b in blocks[start:]:
        rr = httpx.delete(f"{API}/blocks/{b['id']}", headers=_hdr(token), timeout=30)
        if rr.status_code < 300:
            deleted += 1
    return deleted
