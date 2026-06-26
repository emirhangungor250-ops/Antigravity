"""Defansif sanitize katmanı — LLM şema kurallarını ihlal etse bile çıktıyı temizler.

Pipeline Stage 5b (script) ve Stage 6 (asset) sonrası bu modül çalıştırılır.
Sızıntıları sessizce yutmaz, mantıklı yerlerde warn-log basar.
"""

from __future__ import annotations

import re
from typing import Any

# ─── Sabit blacklist'ler ───────────────────────────────────────────────────

EM_DASH = "—"
EM_DASH_PADDED = re.compile(r"\s*—\s*")


def _strip_em_dash(text: str) -> str:
    """' — ' veya '—' → ', ' (etrafındaki boşluğa hassas)."""
    return EM_DASH_PADDED.sub(", ", text or "")

# Script + caption_body + manychat_message'da arananlar.
# Yakalanırsa warn-log; sessizce silmeyiz çünkü context kaybedebiliriz.
BANNED_WORDS_INFORMATIVE = [
    "layout", "spacing", "tipografi", "motion", "easing",
    "workflow", "framework", "pipeline", "fine-tune",
    "prompt engineering", "deployment", "render", "B-roll", "jump-cut",
]

# Manychat message ve caption'da YASAK olan marka tanıtım kelimeleri.
# Yakalanırsa loud-warn (pipeline raporu görsün). Kendi marka/topluluk
# adlarınızı buraya ekleyin (örn. "topluluk", "kursum", "eğitimim").
BRAND_PROMO_PHRASES: list[str] = []

# Manychat buton URL'inde + asset URL'inde YASAK domain'ler.
# Kendi marka domain'inizi buraya ekleyin (kendi reklamınızı yapmasın diye).
BANNED_DOMAINS: list[str] = []

GENERIC_LANDING_HOSTS = [
    "anthropic.com/claude-code",
    "www.anthropic.com/claude-code",
    "anthropic.com/",  # Anthropic ana sayfa
    "claude.ai/",
    "www.claude.com/product/claude-code",
]

SCRIPT_LABEL_PREFIXES = re.compile(
    r"^(HOOK|KONU|CTA|GİRİŞ|GIRIS|SONUÇ|SONUC|AÇILIŞ|ACILIS|KAPANIŞ|KAPANIS)\s*:\s*",
    re.IGNORECASE | re.MULTILINE,
)
HTML_TAG = re.compile(r"<[^>]+>")
BR_TAG = re.compile(r"<br\s*/?>", re.IGNORECASE)


# ─── Script sanitize ───────────────────────────────────────────────────────


def sanitize_script_output(script_obj: dict[str, Any], log=print) -> dict[str, Any]:
    """LLM'in script_output tool çıktısını runtime sanitize eder.
    Geri döndüğünde Pipeline güvenle Notion'a yazabilir."""
    out = dict(script_obj)

    out["script"] = _clean_script_text(out.get("script", ""), log)
    out["caption_hook"] = _clean_caption_field(out.get("caption_hook", ""), log)[:80]
    out["caption_body"] = _clean_caption_field(out.get("caption_body", ""), log)
    out["manychat_message"] = _clean_manychat_message(out.get("manychat_message", ""), log)
    out["manychat_trigger_word"] = _clean_trigger_word(out.get("manychat_trigger_word", ""))

    _warn_banned_words("script", out["script"], log)
    _warn_banned_words("caption_body", out["caption_body"], log)
    _warn_brand_promo("caption_hook", out["caption_hook"], log)
    _warn_brand_promo("caption_body", out["caption_body"], log)
    _warn_brand_promo("manychat_message", out["manychat_message"], log)
    _warn_brand_promo("script", out["script"], log)

    return out


def _clean_script_text(text: str, log) -> str:
    """Em-dash → virgül, HOOK:/KONU:/CTA: gibi etiketleri kaldır."""
    if not text:
        return ""
    cleaned = _strip_em_dash(text)
    stripped = SCRIPT_LABEL_PREFIXES.sub("", cleaned)
    if stripped != cleaned:
        log("  ⚠️", "script'te HOOK:/KONU:/CTA: etiketi vardı, temizlendi")
    return stripped.strip()


def _clean_caption_field(text: str, log) -> str:
    if not text:
        return ""
    cleaned = _strip_em_dash(text)
    no_html = HTML_TAG.sub("", cleaned)
    if no_html != cleaned:
        log("  ⚠️", "caption alanında HTML etiketi vardı, temizlendi")
    return no_html.strip()


def _clean_manychat_message(text: str, log) -> str:
    if not text:
        return ""
    cleaned = _strip_em_dash(text)
    # önce <br>'leri \n'e çevir, sonra kalan tag'leri at
    with_breaks = BR_TAG.sub("\n", cleaned)
    no_html = HTML_TAG.sub("", with_breaks)
    if no_html != cleaned:
        log("  ⚠️", "manychat_message'da HTML etiketi vardı, temizlendi")
    return no_html.strip()


def _clean_trigger_word(text: str) -> str:
    if not text:
        return ""
    # Türkçe büyük harf koruyacak şekilde upper + boşlukları temizle
    return re.sub(r"[^A-ZÇĞIİÖŞÜ]", "", text.upper())[:15]


def _warn_banned_words(field: str, text: str, log) -> None:
    if not text:
        return
    hits = [w for w in BANNED_WORDS_INFORMATIVE if re.search(rf"\b{re.escape(w)}\b", text, re.IGNORECASE)]
    if hits:
        log("  ⚠️", f"{field}: yasak/jargon kelime sızdı → {hits}")


def _warn_brand_promo(field: str, text: str, log) -> None:
    if not text:
        return
    lowered = text.lower()
    hits = [p for p in BRAND_PROMO_PHRASES if p.lower() in lowered]
    if hits:
        log("  ⚠️", f"{field}: marka tanıtım kelimesi sızdı → {hits}")


# ─── Asset sanitize ────────────────────────────────────────────────────────


def sanitize_assets(assets_obj: dict[str, Any], log=print) -> dict[str, Any]:
    """LLM'in asset_pool çıktısını runtime sanitize eder.
    youtube search link / topluluk / generic landing yakalanırsa o asset DROP edilir.
    Açıklamadaki em-dash (—) virgüle çevrilir (Drive Doc + ManyChat buton text'ine sızıyor)."""
    out = dict(assets_obj)
    cleaned: list[dict[str, Any]] = []
    for a in out.get("assets") or []:
        if not _asset_is_valid(a, log):
            continue
        a2 = dict(a)
        a2["aciklama"] = _strip_em_dash(a2.get("aciklama") or "")
        cleaned.append(a2)
    out["assets"] = cleaned
    if (ozet := out.get("ozet")):
        out["ozet"] = _strip_em_dash(ozet)
    return out


def _asset_is_valid(asset: dict[str, Any], log) -> bool:
    url = (asset.get("url") or "").strip()
    if not url:
        log("  ⚠️", f"asset URL boş, drop edildi: {asset.get('aciklama')}")
        return False
    if "youtube.com/results" in url:
        log("  ⚠️", f"asset YouTube search link içeriyor, drop: {url}")
        return False
    if any(d in url for d in BANNED_DOMAINS):
        log("  ⚠️", f"asset yasak domain (topluluk vb.), drop: {url}")
        return False
    if any(g in url for g in GENERIC_LANDING_HOSTS):
        log("  ⚠️", f"asset generic landing page, drop: {url}")
        return False
    return True


# ─── Asset → ManyChat Buttons köprüsü ──────────────────────────────────────


def assets_to_buttons(assets_obj: dict[str, Any], *, max_buttons: int = 3) -> list[dict[str, str]]:
    """Asset listesinden ManyChat butonları üret.

    Asset'ler zaten web_search ile bulunmuş, topluluk/generic landing filtrelenmiş,
    scriptte vaat edilen şeylerle eşleşmiş gerçek kaynaklar. ManyChat'in butonları
    bu havuzdan otomatik beslenir; LLM'in halüsinasyonu işin içine girmez.
    """
    buttons: list[dict[str, str]] = []
    for asset in (assets_obj.get("assets") or [])[:max_buttons]:
        text = _short_button_label(asset.get("aciklama") or "", asset.get("tip") or "")
        url = (asset.get("url") or "").strip()
        if url and text:
            buttons.append({"text": text, "url": url})
    return buttons


def _short_button_label(description: str, tip: str) -> str:
    """Asset açıklamasından buton yazısı türet (max 25 char)."""
    if not description:
        return ""
    text = description.split(",")[0].split("(")[0].split(":")[0].strip()
    text = re.sub(r"\s+(resmi sayfası|resmi sitesi|GitHub|GitHub repo|reposu|kaynak kod|skill|page)\b.*", "", text, flags=re.IGNORECASE)
    text = text.strip(" -—,.")
    if len(text) > 25:
        text = text[:24].rstrip() + "…"
    return text or (description[:24] + "…")
