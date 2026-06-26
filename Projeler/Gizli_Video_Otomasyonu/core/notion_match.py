"""Gizli videoyu Notion'daki doğru satırla eşleştirme.

Kural: SADECE ikonu YouTube olan satırlar (Reels atlanır). Satır adı genelde kısa
bir kod adıdır ('Proje YT'); gerçek başlık sayfa gövdesinde 'BAŞLIK:' satırındadır.
Eşleştirme iki sinyali birleştirir:
  - başlık benzerliği (video başlığı ↔ BAŞLIK)
  - içerik örtüşmesi (videonun gerçek konuşması ↔ Notion scripti)  ← daha güçlü
Güven eşiğinin altındaysa körlemesine yazmaz; yöneticiye sorulur.

NOT: Notion property adları ('Name', 'Drive', 'Status') ile gövdedeki 'BAŞLIK:' /
durdurma anahtarları (_BODY_STOP) kendi Notion şemana göre değişir — TODO: bunları
kendi sütun adlarınla güncelle.
"""
import difflib
import os
import re

import requests

from config import MATCH_MIN_GAP, MATCH_MIN_SCORE, NOTION_DB

_NOTION_VER = "2022-06-28"
_STOP = set(
    "için bir bu şu çok daha ama gibi olan olarak ben sen biz siz çünkü ile hem her şey "
    "nasıl yani sonra önce kadar diye var yok bunu şimdi değil ya da ki de da mi mı".split()
)
# Notion script gövdesinde bu işaretlerden sonrası (revizyon paneli vs.) okunmaz
_BODY_STOP = ("KAPAK", "REVİZYON", "MANYCHAT")


def _token() -> str:
    return os.getenv("NOTION_SOCIAL_TOKEN") or os.getenv("NOTION_API_TOKEN") or ""


def _napi(method, url, body=None):
    r = requests.request(
        method, url,
        headers={"Authorization": f"Bearer {_token()}", "Notion-Version": _NOTION_VER,
                 "Content-Type": "application/json"},
        json=body, timeout=30,
    )
    r.raise_for_status()
    return r.json()


def _icon_name(page) -> str:
    ic = page.get("icon") or {}
    if ic.get("type") == "custom_emoji":
        return (ic.get("custom_emoji") or {}).get("name", "")
    return ""


def _title(page) -> str:
    return "".join(x.get("plain_text", "") for x in page["properties"].get("Name", {}).get("title", []))


def _page_body(page_id: str) -> tuple[str, str]:
    """(baslik, script_metni) döner; revizyon panelinden önce keser."""
    ch = _napi("GET", f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=50")
    baslik, parts = "", []
    for b in ch.get("results", []):
        txt = "".join(x.get("plain_text", "") for x in b.get(b.get("type", ""), {}).get("rich_text", []))
        up = txt.strip().upper()
        if any(s in up for s in _BODY_STOP):
            break
        if not baslik and up.startswith(("BAŞLIK", "BASLIK")):
            baslik = txt.split(":", 1)[-1].strip()
        parts.append(txt)
    return baslik, "\n".join(parts)


def youtube_rows(limit: int = 50) -> list[dict]:
    q = _napi("POST", f"https://api.notion.com/v1/databases/{NOTION_DB}/query",
              {"page_size": limit, "sorts": [{"timestamp": "created_time", "direction": "descending"}]})
    rows = []
    for p in q["results"]:
        if "youtube" not in _icon_name(p).lower():
            continue
        baslik, script = _page_body(p["id"])
        rows.append({
            "page_id": p["id"],
            "name": _title(p),
            "baslik": baslik,
            "script": script,
            "drive": (p["properties"].get("Drive", {}) or {}).get("url", "") or "",
            "status": (p["properties"].get("Status", {}).get("select") or {}).get("name", ""),
            "url": p.get("url", ""),
        })
    return rows


def _norm(s: str) -> str:
    return re.sub(r"[^a-zğüşıöç0-9 ]", "", (s or "").lower())


def _toks(s: str) -> set:
    return {w for w in re.findall(r"[a-zçğıöşü]{5,}", (s or "").lower()) if w not in _STOP}


def match(video_title: str, transcript_text: str, rows: list[dict]) -> dict:
    """En iyi satırı + güven kararını döner."""
    vtok = _toks(transcript_text + " " + video_title)
    scored = []
    for r in rows:
        title_sim = difflib.SequenceMatcher(None, _norm(video_title), _norm(r["baslik"] or r["name"])).ratio()
        rtok = _toks(r["script"])
        # script kelimelerinin ne kadarı videoda gerçekten geçiyor (güçlü sinyal)
        content = len(vtok & rtok) / max(1, len(rtok)) if rtok else 0.0
        score = 0.35 * title_sim + 0.65 * content
        scored.append({"row": r, "score": score, "title_sim": title_sim, "content": content})
    scored.sort(key=lambda x: x["score"], reverse=True)
    if not scored:
        return {"row": None, "confident": False, "score": 0.0, "second": 0.0, "title_sim": 0.0, "content": 0.0}
    best = scored[0]
    second = scored[1]["score"] if len(scored) > 1 else 0.0
    best["second"] = second
    best["confident"] = best["score"] >= MATCH_MIN_SCORE and (best["score"] - second) >= MATCH_MIN_GAP
    return best


def append_note(page_id: str, message: str) -> bool:
    """Notion sayfasına kısa bir durum notu ekler (kalıcı iz)."""
    body = {"children": [{"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": message[:1900]}}]}}]}
    try:
        r = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers={"Authorization": f"Bearer {_token()}", "Notion-Version": _NOTION_VER,
                     "Content-Type": "application/json"},
            json=body, timeout=30,
        )
        return r.status_code == 200
    except Exception:
        return False
