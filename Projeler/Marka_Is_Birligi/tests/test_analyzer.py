from src import analyzer
from src import llm_brand_extractor
from src.llm_brand_extractor import CaptionAnalysis, ExtractedBrand


def test_extract_mentions_from_caption():
    cap = "Harika içerik @brand_ai @another.tool ve @brand_ai tekrar"
    out = analyzer.extract_mentions_from_caption(cap)
    assert "brand_ai" in out
    assert "another.tool" in out


def test_has_collab_marker_tr():
    assert analyzer.has_collab_marker("Bu paylaşım işbirliği içerir")
    assert analyzer.has_collab_marker("#sponsored content")
    assert not analyzer.has_collab_marker("normal post")


def test_is_likely_ai_brand_known():
    # config/brand_filters.json'daki örnek markalardan biri.
    assert analyzer.is_likely_ai_brand("ornek_marka_1", sources=[])


def test_is_likely_ai_brand_handle_heuristic():
    assert analyzer.is_likely_ai_brand("foobar_ai", sources=[])
    assert analyzer.is_likely_ai_brand("agent.ai", sources=[])


def test_is_likely_ai_brand_negative():
    assert not analyzer.is_likely_ai_brand("randomperson", sources=[{"caption_snippet": "lorem ipsum", "is_collab": False}])


def test_brand_filters_loaded():
    # config/brand_filters.json yüklendi, örnek listeler okunabiliyor.
    assert "ornek_marka_1" in analyzer.KNOWN_AI_BRANDS
    assert len(analyzer.FALSE_POSITIVES) > 0
    assert len(analyzer.SKIP_BIG_COMPANIES) > 0


# ── LLM yolu testleri ───────────────────────────────────────────────────────

def test_llm_detects_plaintext_brand_without_tag(monkeypatch):
    """Caption'da düz yazı 'Synthix' geçiyorsa, @etiket olmasa bile
    yeni marka olarak çıkmalı. LLM client mock'lanır — gerçek API çağrılmaz."""

    def fake_extract(caption, timeout=20):
        if "synthix" in caption.lower():
            return CaptionAnalysis(brands=[
                ExtractedBrand(
                    name="Synthix",
                    instagram_handle="",  # ETİKETSİZ — eski kör mantık bunu kaçırırdı
                    is_ai_or_tech=True,
                    is_collaboration=True,
                ),
            ])
        return CaptionAnalysis(brands=[])

    monkeypatch.setattr(llm_brand_extractor, "extract_brands_from_caption", fake_extract)
    # Notion dedup'ı dış çağrı yapmasın
    monkeypatch.setattr(analyzer, "load_existing_csv_brands", lambda: set())
    monkeypatch.setattr(analyzer, "load_existing_brands", lambda: (set(), set()))

    reels = [{
        "caption": "Bu hafta Synthix ile çalıştım, harika bir yapay zeka aracı. #işbirliği",
        "ownerUsername": "rakip_influencer",
        "url": "https://instagram.com/reel/abc",
    }]

    new_brands = analyzer.find_new_brands(reels)
    names = {b["marka_adi"].lower() for b in new_brands}
    assert "synthix" in names, f"Synthix düz yazıdan tespit edilemedi: {new_brands}"
    synthix = next(b for b in new_brands if b["marka_adi"].lower() == "synthix")
    assert synthix["is_collab"] is True


def test_llm_failure_falls_back_to_keyword(monkeypatch):
    """LLM None dönerse (API hatası/timeout), eski @mention + keyword
    yedek yolu devreye girmeli."""

    monkeypatch.setattr(llm_brand_extractor, "extract_brands_from_caption",
                        lambda caption, timeout=20: None)
    monkeypatch.setattr(analyzer, "load_existing_csv_brands", lambda: set())
    monkeypatch.setattr(analyzer, "load_existing_brands", lambda: (set(), set()))

    reels = [{
        "caption": "Harika içerik @ornek_marka_1 ile, reklam.",
        "ownerUsername": "rakip_influencer",
        "url": "https://instagram.com/reel/xyz",
    }]

    new_brands = analyzer.find_new_brands(reels)
    handles = {b["instagram_handle"].lower() for b in new_brands}
    assert "ornek_marka_1" in handles, f"Keyword fallback çalışmadı: {new_brands}"
