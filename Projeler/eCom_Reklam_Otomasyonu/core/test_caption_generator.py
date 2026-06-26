"""
Mock testler: core/caption_generator.py

Çalıştır:
    cd Projeler/eCom_Reklam_Otomasyonu
    python -m unittest core.test_caption_generator -v
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from core.caption_generator import CaptionGenerator, build_brief_payload


def _fake_response(payload: dict) -> SimpleNamespace:
    """OpenAI ChatCompletion benzeri yapı (choices[0].message.content)."""
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=json.dumps(payload, ensure_ascii=False))
            )
        ]
    )


def _full_payload() -> dict:
    """Tüm platform alanları doldurulmuş örnek (strict schema'ya uygun)."""
    return {
        "tiktok": {
            "caption": "Mavi'den Yüksek Bel Mom Jeans 🔥 Yeni stilini keşfet!",
            "hashtags": ["mavi", "momjeans", "fashion", "ootd", "trend"],
        },
        "youtube": {
            "title": "Mavi Mom Jeans — Sokak Modası Şıklığı",
            "description": "Mavi'den Yüksek Bel Mom Jeans ile sokak modasının kalbinde. Linkten incele!",
            "tags": ["mavi", "fashion", "jeans", "ootd"],
        },
        "instagram": {
            "caption": "Mavi Mom Jeans — günlük şıklığın yeni adresi.",
            "hashtags": ["mavi", "ootd", "fashion", "moda", "stil"],
        },
        "x": {"caption": "Mavi Mom Jeans — şehir tarzının yeni temposu."},
        "threads": None,
        "linkedin": None,
        "facebook": None,
    }


def _build_generator(response_payload: dict | None = None) -> CaptionGenerator:
    """Mock OpenAIService ile CaptionGenerator döndür."""
    payload = response_payload if response_payload is not None else _full_payload()
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_response(payload)

    fake_oai = MagicMock()
    fake_oai.client = fake_client
    fake_oai.model = "gpt-4.1-mini"
    return CaptionGenerator(fake_oai)


SAMPLE_BRIEF = {
    "brand": "Mavi",
    "product": "Yüksek Bel Mom Jeans",
    "concept": "Sokak modası, parisian gen-z look",
    "style": "9:16 dinamik kesim",
    "language": "tr",
    "target_audience": "18-35 kadın, moda ilgilisi",
}


class CaptionGeneratorTest(unittest.TestCase):

    def test_generate_returns_all_requested_platforms(self):
        cg = _build_generator()
        out = cg.generate(SAMPLE_BRIEF, ["tiktok", "youtube"])
        self.assertEqual(set(out.keys()), {"tiktok", "youtube"})

    def test_generate_includes_brand_name(self):
        cg = _build_generator()
        out = cg.generate(SAMPLE_BRIEF, ["tiktok", "youtube", "instagram"])
        for platform, payload in out.items():
            blob = " ".join(
                str(v) for v in payload.values() if isinstance(v, str)
            ).lower()
            self.assertIn(
                "mavi", blob,
                f"Platform '{platform}' caption'unda marka adı yok: {payload}",
            )

    def test_youtube_has_title_and_description(self):
        cg = _build_generator()
        out = cg.generate(SAMPLE_BRIEF, ["youtube"])
        yt = out["youtube"]
        self.assertIn("title", yt)
        self.assertIn("description", yt)
        self.assertIsInstance(yt["title"], str)
        self.assertIsInstance(yt["description"], str)
        self.assertTrue(yt["title"])
        self.assertTrue(yt["description"])
        self.assertIsInstance(yt.get("tags"), list)

    def test_tiktok_has_caption_and_hashtags(self):
        cg = _build_generator()
        out = cg.generate(SAMPLE_BRIEF, ["tiktok"])
        tt = out["tiktok"]
        self.assertIn("caption", tt)
        self.assertIn("hashtags", tt)
        self.assertIsInstance(tt["caption"], str)
        self.assertIsInstance(tt["hashtags"], list)
        self.assertTrue(tt["caption"])
        self.assertTrue(all(isinstance(h, str) for h in tt["hashtags"]))
        # Hashtag'ler '#' OLMADAN dönmeli (clean step)
        for h in tt["hashtags"]:
            self.assertFalse(h.startswith("#"), f"Hashtag '#' içeremez: {h!r}")

    def test_unknown_platform_raises(self):
        cg = _build_generator()
        with self.assertRaises(ValueError):
            cg.generate(SAMPLE_BRIEF, ["tiktok", "snapchat"])

    def test_empty_platforms_raises(self):
        cg = _build_generator()
        with self.assertRaises(ValueError):
            cg.generate(SAMPLE_BRIEF, [])

    def test_brand_safety_net_when_llm_omits_brand(self):
        """LLM marka adını unutursa, post-process başına ekler."""
        payload = {
            "tiktok": {
                "caption": "Mom jeans şıklığı 🔥 Yeni stiline merhaba de!",
                "hashtags": ["fashion", "ootd"],
            },
            "youtube": None,
            "instagram": None,
            "x": None,
            "threads": None,
            "linkedin": None,
            "facebook": None,
        }
        cg = _build_generator(payload)
        out = cg.generate(SAMPLE_BRIEF, ["tiktok"])
        self.assertIn("mavi", out["tiktok"]["caption"].lower())

    def test_hashtag_strip_pound_prefix(self):
        """LLM '#fashion' döndürürse, post-process '#'i atar."""
        payload = {
            "tiktok": {
                "caption": "Mavi Mom Jeans şıklığı 🔥",
                "hashtags": ["#fashion", "#ootd", "trend"],
            },
            "youtube": None,
            "instagram": None,
            "x": None,
            "threads": None,
            "linkedin": None,
            "facebook": None,
        }
        cg = _build_generator(payload)
        out = cg.generate(SAMPLE_BRIEF, ["tiktok"])
        for h in out["tiktok"]["hashtags"]:
            self.assertFalse(h.startswith("#"))


class BriefPayloadTest(unittest.TestCase):

    def test_build_brief_payload_basic(self):
        payload = build_brief_payload(
            collected_data={
                "brand_name": "Mavi",
                "product_name": "Mom Jeans",
                "ad_concept": "Sokak modası",
                "target_audience": "18-35 kadın",
            },
            preferences={
                "video_format": "9:16",
                "video_style": "Sinematik Tanıtım",
                "custom_note": "tone biraz daha eğlenceli",
            },
            scenario={"narrative_hook": "Şehrin temposunu yakaladım."},
            video_url="https://example.com/video.mp4",
        )
        self.assertEqual(payload["brand"], "Mavi")
        self.assertEqual(payload["product"], "Mom Jeans")
        self.assertIn("Şehrin temposunu", payload["concept"])
        self.assertIn("eğlenceli", payload["concept"])
        self.assertIn("9:16", payload["style"])
        self.assertIn("Sinematik", payload["style"])
        self.assertEqual(payload["language"], "tr")
        self.assertEqual(payload["video_url"], "https://example.com/video.mp4")

    def test_build_brief_payload_falls_back_to_ad_concept(self):
        payload = build_brief_payload(
            collected_data={"brand_name": "X", "product_name": "Y", "ad_concept": "AC"},
            preferences={},
            scenario={},
        )
        self.assertEqual(payload["concept"], "AC")
        self.assertEqual(payload["style"], "9:16")  # default
        self.assertNotIn("video_url", payload)


if __name__ == "__main__":
    unittest.main()
