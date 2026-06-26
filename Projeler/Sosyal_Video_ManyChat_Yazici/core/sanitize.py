"""Defansif sanitize — LLM kuralı ihlal etse bile çıktıyı temizler ve akışı doğrular.

İki sorumluluk:
  1. Asset havuzu temizliği (yasak domain + generic landing drop, em-dash, HEAD probe).
  2. ManyChat AKIŞI çözümleme: link butonlarını gerçek URL'lere bağla (asset_ref),
     devam butonlarını mesaj id'lerine doğrula, erişilemeyen mesajları ele, metinleri temizle.

Asset HEAD probe tarayıcı UA + sadece 404/410/5xx drop (memory: railway-cloudflare-user-agent).
"""

from __future__ import annotations

import os
import re
from typing import Any

import httpx

EM_DASH_PADDED = re.compile(r"\s*—\s*")
HTML_TAG = re.compile(r"<[^>]+>")
BR_TAG = re.compile(r"<br\s*/?>", re.IGNORECASE)
RAW_URL = re.compile(r"https?://\S+", re.IGNORECASE)
# Notion'da render OLMAYAN geometrik madde işaretleri → görünür emoji (🔹). Satır başında yakala.
# (1️⃣2️⃣… emoji rakamlarına ve normal metne dokunmaz.)
DINGBAT_BULLET = re.compile(r"^[ \t]*[◇◆◊◈❖▪▫◦‣·•●○■□▸▹►▻*]\s+", re.MULTILINE)
# Kalp ailesi emoji — varsayılan tarz tercihi olarak temizlenir (istersen kaldır).
# 🫶(1faf6) heart-hands + tüm renkli kalpler + 🫀 + 🥰 😍 😘.
HEART_EMOJI = re.compile("[❤❣\U0001faf6\U0001fac0\U0001f9e1\U0001f49b\U0001f49a\U0001f499\U0001f49c"
                         "\U0001f5a4\U0001f90d\U0001f90e\U0001f495\U0001f49e\U0001f493\U0001f497"
                         "\U0001f496\U0001f498\U0001f49d\U0001f49f\U0001f48c]️?"
                         "|\U0001f970|\U0001f60d|\U0001f618")


def strip_em_dash(text: str) -> str:
    """' — ' veya '—' → ', '."""
    return EM_DASH_PADDED.sub(", ", text or "")


# ManyChat metninde istemediğin DOĞRUDAN tanıtım kelimeleri (dolaylı tanıtım ilkesi).
# Kendi topluluk/kurs/ürün adlarını buraya ekle (ya da BRAND_PROMO_PHRASES env'i ile,
# virgülle ayır). Aşağıdaki 1-2 satır yer-tutucu örnektir; kendine göre düzenle.
BRAND_PROMO_PHRASES = [
    s.strip() for s in (os.getenv("BRAND_PROMO_PHRASES") or
                        "topluluğum,kursum,eğitimim").split(",") if s.strip()
]

# Asset/buton URL'inde YASAK domain'ler (örn. üyelik/satış platformun).
# Virgülle ayrılmış BANNED_DOMAINS env'i ile override edilebilir.
BANNED_DOMAINS = [
    s.strip() for s in (os.getenv("BANNED_DOMAINS") or "").split(",") if s.strip()
]

# Generic landing pattern'leri — sadece ürün/ana sayfayı drop et, spesifik path geçer.
GENERIC_LANDING_PATTERNS = [
    re.compile(r"^https?://(www\.)?anthropic\.com/?$", re.IGNORECASE),
    re.compile(r"^https?://(www\.)?anthropic\.com/claude(-code)?/?$", re.IGNORECASE),
    re.compile(r"^https?://(www\.)?claude\.(ai|com)/?$", re.IGNORECASE),
    re.compile(r"^https?://(www\.)?claude\.com/product/[^/?#]+/?$", re.IGNORECASE),
]


# ─── Genel metin sanitize ────────────────────────────────────────────────────


def clean_message_text(text: str, log=print) -> str:
    """Tek bir mesaj balonunun metnini temizle: em-dash, HTML, ham URL."""
    if not text:
        return ""
    cleaned = strip_em_dash(text)
    cleaned = BR_TAG.sub("\n", cleaned)
    cleaned = DINGBAT_BULLET.sub("🔹 ", cleaned)
    cleaned = HEART_EMOJI.sub("", cleaned)
    no_html = HTML_TAG.sub("", cleaned)
    if no_html != cleaned:
        log("  ⚠️", "mesajda HTML etiketi vardı, temizlendi")
    # Ham URL mesaj gövdesinde olmamalı (link sadece butonda). Varsa çıkar.
    if RAW_URL.search(no_html):
        log("  ⚠️", "mesaj gövdesinde ham URL vardı, çıkarıldı (link butonda olmalı)")
        no_html = RAW_URL.sub("", no_html)
    # URL çıkınca kalan çift boşlukları sadeleştir (satır içi; \n korunur)
    lines = [re.sub(r"[ \t]{2,}", " ", ln).rstrip() for ln in no_html.split("\n")]
    return "\n".join(lines).strip()


def clean_trigger_word(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[^A-ZÇĞIİÖŞÜ]", "", text.upper())[:15]


def find_brand_promo(text: str) -> list[str]:
    if not text:
        return []
    lowered = text.lower()
    return [p for p in BRAND_PROMO_PHRASES if p.lower() in lowered]


# ─── Asset sanitize ─────────────────────────────────────────────────────────


def sanitize_assets(assets_obj: dict[str, Any], log=print) -> dict[str, Any]:
    """Asset havuzunu temizle: yasak domain + generic landing drop, em-dash temizle,
    sonra her URL'a HEAD probe (kesin 4xx/5xx drop)."""
    out = dict(assets_obj)
    cleaned: list[dict[str, Any]] = []
    for a in out.get("assets") or []:
        if not _asset_is_valid(a, log):
            continue
        a2 = dict(a)
        a2["aciklama"] = strip_em_dash(a2.get("aciklama") or "")
        bet = (a2.get("onerilen_etiket") or "").strip()
        if bet:
            bet = strip_em_dash(bet).strip()
            if len(bet) > 25:
                bet = bet[:24].rstrip() + "…"
            a2["onerilen_etiket"] = bet
        cleaned.append(a2)

    probed: list[dict[str, Any]] = []
    for a in cleaned:
        if _asset_url_reachable(a["url"], log):
            probed.append(a)

    out["assets"] = probed
    return out


def _asset_is_valid(asset: dict[str, Any], log) -> bool:
    url = (asset.get("url") or "").strip()
    if not url:
        log("  ⚠️", f"asset URL boş, drop: {asset.get('aciklama')}")
        return False
    if "youtube.com/results" in url:
        log("  ⚠️", f"asset YouTube arama linki, drop: {url}")
        return False
    if any(d in url for d in BANNED_DOMAINS):
        log("  ⚠️", f"asset yasak domain, drop: {url}")
        return False
    if any(pat.match(url) for pat in GENERIC_LANDING_PATTERNS):
        log("  ⚠️", f"asset generic landing, drop: {url}")
        return False
    return True


# Tarayıcı User-Agent — UA'sız HEAD'i Cloudflare/news siteleri 403'le eler
# (memory: railway-cloudflare-user-agent). UA ile gerçek erişilebilirlik ölçülür.
_BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def _asset_url_reachable(url: str, log) -> bool:
    """6sn HEAD probe (tarayıcı UA ile). Sadece KESİN ölü sayfa drop edilir:
    404 (yok), 410 (kalktı), 5xx (sunucu hatası). 401/403/405/429 gibi erişim/method
    kısıtları KORUNUR. Timeout/connection error → drop SAYMA."""
    try:
        r = httpx.head(url, timeout=6, follow_redirects=True, headers={"User-Agent": _BROWSER_UA})
    except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError,
            httpx.RemoteProtocolError, httpx.UnsupportedProtocol):
        log("  ⚠️", f"asset HEAD timeout/conn error (kabul): {url}")
        return True
    except Exception as e:  # noqa: BLE001 — defansif
        log("  ⚠️", f"asset HEAD bilinmeyen hata (kabul): {url} ({type(e).__name__})")
        return True
    if r.status_code in (404, 410) or 500 <= r.status_code < 600:
        log("  ⚠️", f"asset {r.status_code} (ölü) drop: {url}")
        return False
    return True


# ─── ManyChat AKIŞI çözümleme ────────────────────────────────────────────────


def resolve_flow(flow: dict[str, Any], assets_obj: dict[str, Any], log=print) -> dict[str, Any]:
    """LLM akışını gerçek URL'lere bağla + bütünlüğü doğrula.

    - link butonu: asset_ref → havuzdaki gerçek URL (bulunamazsa buton düşer).
    - devam butonu: goto → gerçek mesaj id (yoksa buton düşer).
    - metinler temizlenir (em-dash/HTML/ham URL).
    - sadece açılıştan erişilebilen mesajlar, erişim sırasıyla tutulur.
    """
    asset_by_sira = {int(a["sira"]): a for a in (assets_obj.get("assets") or []) if a.get("sira")}

    trigger = clean_trigger_word(flow.get("trigger_word") or "")
    opening_src = flow.get("opening") or {}
    messages_src = {m.get("id"): m for m in (flow.get("messages") or []) if m.get("id")}
    valid_ids = set(messages_src.keys())

    def _resolve_buttons(raw_buttons, where: str):
        resolved = []
        for b in raw_buttons or []:
            label = strip_em_dash((b.get("label") or "").strip())[:25]
            kind = b.get("kind")
            if not label or kind not in ("link", "continue"):
                continue
            if kind == "link":
                ref = b.get("asset_ref")
                asset = asset_by_sira.get(int(ref)) if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()) else None
                if not asset:
                    log("  ⚠️", f"[{where}] link butonu '{label}' geçersiz asset_ref={ref}, düştü")
                    continue
                resolved.append({"label": label or asset.get("onerilen_etiket") or "Link",
                                 "kind": "link", "url": asset["url"]})
            else:  # continue
                goto = (b.get("goto") or "").strip()
                if goto not in valid_ids:
                    log("  ⚠️", f"[{where}] devam butonu '{label}' geçersiz goto={goto!r}, düştü")
                    continue
                resolved.append({"label": label, "kind": "continue", "goto": goto})
        return resolved

    opening = {
        "text": clean_message_text(opening_src.get("text") or "", log),
        "buttons": _resolve_buttons(opening_src.get("buttons"), "açılış"),
    }

    # Erişilebilirlik: açılıştan başlayıp goto'ları izle (BFS), sırayı koru.
    order: list[str] = []
    seen: set[str] = set()
    queue = [btn["goto"] for btn in opening["buttons"] if btn["kind"] == "continue"]
    while queue:
        mid = queue.pop(0)
        if mid in seen or mid not in messages_src:
            continue
        seen.add(mid)
        order.append(mid)
        raw_btns = messages_src[mid].get("buttons")
        for b in raw_btns or []:
            if b.get("kind") == "continue" and (b.get("goto") or "").strip() in valid_ids:
                queue.append((b.get("goto") or "").strip())

    messages = []
    for mid in order:
        m = messages_src[mid]
        messages.append({
            "id": mid,
            "text": clean_message_text(m.get("text") or "", log),
            "buttons": _resolve_buttons(m.get("buttons"), f"mesaj:{mid}"),
        })

    orphans = valid_ids - seen
    if orphans:
        log("  ⚠️", f"erişilemeyen {len(orphans)} mesaj atıldı: {sorted(orphans)}")

    notes = []
    for n in flow.get("notes") or []:
        n = HEART_EMOJI.sub("", strip_em_dash(str(n))).strip()
        if n:
            notes.append(n)

    return {"trigger_word": trigger, "opening": opening, "messages": messages, "notes": notes}


def flow_all_text(resolved: dict[str, Any]) -> str:
    """Akıştaki tüm metni birleştir (marka-promo taraması için)."""
    parts = [resolved.get("opening", {}).get("text", "")]
    parts += [m.get("text", "") for m in resolved.get("messages") or []]
    return "\n".join(p for p in parts if p)
