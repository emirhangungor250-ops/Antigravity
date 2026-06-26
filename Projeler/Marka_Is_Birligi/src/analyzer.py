#!/usr/bin/env python3
"""
Analyzer modülü — Scrape edilen reels'lerden AI marka mention'larını tespit eder.

Caption analizine dayanarak hangi markaların influencer iş birliği yaptığını bulur
ve yeni markaları keşfeder.
"""

import csv
import json
import os
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_REELS_PATH = os.path.join(BASE_DIR, "data", "raw_reels.json")
MARKALAR_CSV = os.path.join(BASE_DIR, "data", "markalar.csv")
CALISAN_MARKALAR_PATH = os.path.join(BASE_DIR, "data", "calisan_markalar.json")

# ── İş birliği belirteçleri ─────────────────────────────────────────────────
COLLAB_MARKERS_TR = [
    "işbirliği", "iş birliği", "reklam", "sponsorlu",
    "sponsor", "ortaklık", "tanıtım",
]
COLLAB_MARKERS_EN = [
    "ad ", " ad\n", "#ad ", "sponsored", "partnership",
    "collab", "collaboration", "paid partnership",
]

# ── Filtre listeleri (config/brand_filters.json'dan yüklenir) ──────────────
_BRAND_FILTERS_PATH = os.path.join(BASE_DIR, "config", "brand_filters.json")


def _load_brand_filters():
    try:
        with open(_BRAND_FILTERS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return (
            {b.lower() for b in data.get("known_ai_brands", [])},
            {b.lower() for b in data.get("false_positives", [])},
            {b.lower() for b in data.get("skip_big_companies", [])},
        )
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ANALYZER] ⚠️ brand_filters.json okunamadı ({e}); boş listelerle devam.")
        return set(), set(), set()


KNOWN_AI_BRANDS, FALSE_POSITIVES, SKIP_BIG_COMPANIES = _load_brand_filters()

AI_KEYWORDS = [
    "ai", "yapay zeka", "artificial intelligence", "machine learning",
    "deep learning", "gpt", "llm", "generative", "neural",
    "automation", "chatbot", "copilot",
]


def extract_mentions_from_caption(caption):
    """Caption metninden @mention'ları çıkarır."""
    return re.findall(r"@([\w.]+)", caption)


def normalize_mention(mention):
    """Mention'ı temizler."""
    return mention.strip().rstrip(".").lower()


def has_collab_marker(caption):
    """Caption'da iş birliği belirteci var mı?"""
    cap_lower = caption.lower()
    for marker in COLLAB_MARKERS_TR + COLLAB_MARKERS_EN:
        if marker in cap_lower:
            return True
    if "/işbirliği" in cap_lower or "/iş birliği" in cap_lower:
        return True
    return False


def extract_mentions_from_field(mentions_field):
    """Apify mentions alanından kullanıcı adlarını çıkarır."""
    results = []
    if not mentions_field:
        return results
    for m in mentions_field:
        if isinstance(m, str):
            results.append(normalize_mention(m))
        elif isinstance(m, dict):
            username = m.get("username", "")
            if username:
                results.append(normalize_mention(username))
    return results


def is_likely_ai_brand(handle, sources):
    """Bir markanın yapay zeka odaklı olup olmadığını tahmin eder.

    Öncelik: LLM verdict'i (kaynaklardan herhangi biri LLM ile AI markası
    olarak işaretlendiyse True). LLM verdict'i yoksa eski keyword/liste
    heuristic'i devreye girer (yedek yol).
    """
    handle_lower = handle.lower()

    # Ana yol — LLM bu markayı bir kaynakta AI/tech olarak işaretlediyse.
    for src in sources:
        if src.get("llm_is_ai_brand") is True:
            return True

    # Yedek yol — eski keyword/liste heuristic'i.
    if handle_lower in KNOWN_AI_BRANDS:
        return True

    for kw in ["ai", "_ai", ".ai", "yapay", "zeka"]:
        if kw in handle_lower:
            return True

    for src in sources:
        caption = src.get("caption_snippet", "").lower()
        ai_score = sum(1 for kw in AI_KEYWORDS if kw in caption)
        if ai_score >= 2 and src.get("is_collab"):
            return True

    return False


def _brand_key(name, handle):
    """Bir markayı dedup için tek anahtara indirger.

    @handle varsa onu, yoksa normalize edilmiş ismi kullanır. Böylece
    LLM'in düz yazıdan çıkardığı 'Synthix' ile @synthix etiketi aynı
    markaya gider.
    """
    if handle:
        return normalize_mention(handle.lstrip("@"))
    return name.strip().lower().replace(" ", "")


def load_existing_brands():
    """Halihazırda çalışılan markaları yükler."""
    handles = set()
    names = set()
    
    if os.path.exists(CALISAN_MARKALAR_PATH):
        with open(CALISAN_MARKALAR_PATH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        handles = set(h.lower() for h in data.get("instagram_handles_to_exclude", []))
        names = set(n.lower().strip() for n in data.get("brands", []))
    
    return handles, names


def load_existing_csv_brands():
    """Mevcut Notion'daki markaları yükler (dedup için)."""
    try:
        from src.notion_service import get_all_brands
        brands = get_all_brands()
        existing = set()
        for b in brands:
            handle = b.get("instagram_handle", "").strip().lower().lstrip("@")
            if handle:
                existing.add(handle)
        return existing
    except Exception as e:
        print(f"[ANALYZER] Notion'dan markalar alınırken hata: {e}")
        return set()


def analyze_reels(reels):
    """
    Reels verilerinden marka mention'larını analiz eder.

    Her caption önce LLM'e okutulur (ANA yol) — düz yazıyla geçen veya
    bilinen-liste dışı markalar da yakalanır. LLM cevap veremezse o reel
    için @mention regex + keyword heuristic (YEDEK yol) devreye girer.

    Returns:
        dict: {key: {mention_count, sources, instagram_handle, marka_adi}}
    """
    try:
        from src.llm_brand_extractor import extract_brands_from_caption
    except ImportError:
        extract_brands_from_caption = None

    brands = defaultdict(
        lambda: {"mention_count": 0, "sources": [], "instagram_handle": "", "marka_adi": ""}
    )

    # Kendi profil kullanıcı adlarımız — bunları filtreleyelim
    competitor_handles = set()
    for reel in reels:
        owner = (reel.get("ownerUsername") or "").lower()
        if owner:
            competitor_handles.add(owner)

    llm_used = 0
    fallback_used = 0

    for reel in reels:
        caption = reel.get("caption") or ""
        owner_username = (reel.get("ownerUsername") or "").lower()
        url = reel.get("url") or ""
        is_collab = has_collab_marker(caption)

        # ── ANA YOL: LLM caption analizi ────────────────────────────────
        analysis = None
        if extract_brands_from_caption is not None:
            analysis = extract_brands_from_caption(caption)

        if analysis is not None:
            llm_used += 1
            for eb in analysis.brands:
                handle = (eb.instagram_handle or "").lstrip("@").lower()
                if handle and handle in competitor_handles:
                    continue
                key = _brand_key(eb.name, handle)
                if key in ("", "yapayzeka", "ai", "yapayzeka"):
                    continue
                brand = brands[key]
                brand["mention_count"] += 1
                if handle:
                    brand["instagram_handle"] = handle
                if not brand["marka_adi"]:
                    brand["marka_adi"] = eb.name.strip()
                brand["sources"].append({
                    "profil": owner_username,
                    "caption_snippet": caption[:200],
                    "url": url,
                    "is_collab": is_collab or eb.is_collaboration,
                    "llm_is_ai_brand": eb.is_ai_or_tech,
                })
            continue

        # ── YEDEK YOL: @mention regex + keyword heuristic ───────────────
        fallback_used += 1
        mentions_from_field = extract_mentions_from_field(reel.get("mentions"))
        mentions_from_caption = [normalize_mention(m) for m in extract_mentions_from_caption(caption)]
        tagged_users = extract_mentions_from_field(reel.get("taggedUsers"))

        all_mentions = set(mentions_from_field + mentions_from_caption + tagged_users)
        all_mentions -= competitor_handles
        all_mentions -= {"", "yapayzeka", "ai", "yapay_zeka"}

        for mention in all_mentions:
            brand = brands[mention]
            brand["mention_count"] += 1
            brand["instagram_handle"] = mention
            brand["sources"].append({
                "profil": owner_username,
                "caption_snippet": caption[:200],
                "url": url,
                "is_collab": is_collab,
            })

    if llm_used or fallback_used:
        print(
            f"[ANALYZER] Caption analizi: {llm_used} reel LLM ile, "
            f"{fallback_used} reel keyword yedek yolu ile işlendi."
        )

    return dict(brands)


def find_new_brands(reels=None):
    """
    Ana analiz fonksiyonu. Yeni markaları keşfeder.
    
    Args:
        reels: Reel verisi listesi. None ise dosyadan okur.
    
    Returns:
        list[dict]: Yeni bulunan markaların listesi
    """
    if reels is None:
        if not os.path.exists(RAW_REELS_PATH):
            print("[ANALYZER] raw_reels.json bulunamadı!")
            return []
        with open(RAW_REELS_PATH, "r", encoding="utf-8-sig") as f:
            reels = json.load(f)

    print(f"[ANALYZER] {len(reels)} reel analiz ediliyor...")

    all_brands = analyze_reels(reels)
    print(f"[ANALYZER] {len(all_brands)} benzersiz mention tespit edildi.")

    # Filtreleme
    existing_handles, existing_names = load_existing_brands()
    csv_handles = load_existing_csv_brands()
    all_existing_handles = existing_handles | csv_handles

    new_brands = []
    seen_names = set()

    for handle, data in sorted(all_brands.items(), key=lambda x: -x[1]["mention_count"]):
        # Marka adı: LLM düz yazıdan çıkardıysa onu kullan, yoksa handle'dan türet.
        brand_name = data.get("marka_adi") or handle.replace("_", " ").replace(".", " ").title()
        # Instagram handle: LLM etiket bulduysa onu, yoksa dedup anahtarını kullan.
        ig_handle = data.get("instagram_handle") or handle

        # False positive filtresi (hem dedup anahtarı hem marka adı kontrol edilir)
        if (handle in FALSE_POSITIVES or handle in SKIP_BIG_COMPANIES
                or brand_name.lower() in FALSE_POSITIVES
                or brand_name.lower() in SKIP_BIG_COMPANIES):
            continue

        # Zaten çalışılan marka filtresi
        if handle.lower() in all_existing_handles or ig_handle.lower() in all_existing_handles:
            continue

        # AI markası kontrolü
        if not is_likely_ai_brand(handle, data["sources"]):
            continue

        # İsim bazlı dedup
        name_lower = brand_name.lower()
        if name_lower in seen_names:
            continue
        if any(ex in name_lower or name_lower in ex for ex in existing_names if len(ex) > 2):
            continue
        seen_names.add(name_lower)

        has_collab = any(s["is_collab"] for s in data["sources"])
        source_profiles = list(set(s["profil"] for s in data["sources"]))

        new_brands.append({
            "instagram_handle": ig_handle,
            "marka_adi": brand_name,
            "mention_sayisi": data["mention_count"],
            "is_collab": has_collab,
            "kaynak_profiller": source_profiles,
            "caption_samples": [s["caption_snippet"][:100] for s in data["sources"][:3]],
        })

    print(f"[ANALYZER] ✅ {len(new_brands)} yeni marka keşfedildi!")
    for b in new_brands:
        collab_icon = "🤝" if b["is_collab"] else "🤖"
        print(f"  {collab_icon} @{b['instagram_handle']} ({b['mention_sayisi']} mention)")

    return new_brands


if __name__ == "__main__":
    new = find_new_brands()
    print(f"\nToplam yeni marka: {len(new)}")
