"""Vision Reviewer — Üretilen sahneyi style guide'a karşı puanlar.

Model: Gemini 2.5 Flash (multimodal, cost-effective)
Çıktı: {"score": float, "categories": {cat: int}, "feedback": str, "passed": bool}

Score < threshold → caller retry'a girer (max 2). Feedback prompt iyileştirme için kullanılır.
"""

import json
import re
from typing import Optional

import google.generativeai as genai

from config import settings
from core.style import VISION_RUBRIC_CATEGORIES
from ops_logger import get_ops_logger

ops = get_ops_logger("IG_Carousel_Cron", "Vision")


REVIEW_INSTRUCTIONS = """Sen bir editorial photography ve marka tasarım eleştirmenisin.
Aşağıdaki carousel slide arka plan sahnesini değerlendir.

KURALLAR (her biri 1-10 puan):

1. **photorealism**: Gerçek bir fotoğraf gibi mi görünüyor? Profesyonel kamera / cinematic.
   Cartoon, illustration, 3D render, vector art, flat design → 1-3 puan.
   Stok-foto klişe (gülen yüz, beyaz arka plan) → 4-5 puan.
   Documentary / magnum-style editorial → 9-10 puan.

2. **no_text_artifacts**: Sahnede HİÇBİR yazı/sayı/logo/tabela olmamalı.
   Görselde gerçek metin / okunabilir kelime / sayı / etiket görüyorsan → 1-4 puan.
   Tamamen text-free → 9-10 puan.

3. **subject_clarity**: Tek odak nokta öne çıkıyor mu? Depth of field var mı?
   Çok sayıda eşit ağırlıklı element / dağınık → 3-5.
   Tek figür, blur'lu arka plan → 9-10.

4. **visual_metaphor**: Sahne soyut bir kavramı somut fizik metaforla anlatıyor mu?
   "Person at laptop / staring at screen" klişesi → 2-4 puan.
   Yaratıcı somut metafor (örn: "kişi evrak çığında uyuyor") → 9-10.

5. **brand_color_palette**: Renkler deep navy / charcoal / warm cream / brass-gold yelpazesinde mi?
   Neon, pastel pembe/mor, doygun parlak renkler → 1-4.
   Dark editorial palet → 9-10.

6. **composition**: Bottom third (alt %33) görsel olarak SAKİN mi? Overlay metin oraya basılacak.
   Alt kısımda yoğun detay/figür/yazı → 3-5.
   Alt kısım koyu/sade, görsel gravite üst/orta → 9-10.

7. **lighting_quality**: Cinematic, kontrastlı, dramatik mi? Yoksa flat / fluorescent mi?
   Flat sodium / overexposed → 3-5.
   Golden hour / blue hour / chiaroscuro → 9-10.

Sadece JSON döndür, başka metin yok. Format:
{
  "categories": {
    "photorealism": 8,
    "no_text_artifacts": 10,
    "subject_clarity": 7,
    "visual_metaphor": 6,
    "brand_color_palette": 8,
    "composition": 7,
    "lighting_quality": 9
  },
  "score": 7.85,
  "feedback": "Sahne photorealistic ama metafor klişe (kişi monitör başında). Bottom-third'de masa detayı fazla, overlay alanı kalabalık. Önerim: kişiyi binlerce kağıt arasında uyumuş göster, alt kısma boş yatay zemin bırak."
}

`feedback` alanı KISA (max 250 karakter), Türkçe, somut iyileştirme önerisi içermeli.
`score` = categories ortalaması.
"""


_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _MODEL = genai.GenerativeModel(settings.VISION_MODEL)
    return _MODEL


def review(image_path: str, scene_description: str = "") -> Optional[dict]:
    """Sahne görselini puanlar.

    Returns:
      {
        "score": float,
        "categories": {cat: int, ...},
        "feedback": str,
        "passed": bool,
      }
    """
    if settings.IS_DRY_RUN:
        ops.info("[DRY-RUN] Vision review atlandı")
        return {"score": 8.0, "categories": {}, "feedback": "", "passed": True}

    if not image_path:
        return None

    try:
        from PIL import Image
        img = Image.open(image_path)
    except Exception as e:
        ops.error("PIL open exception", exception=e)
        return None

    model = _get_model()
    user_text = REVIEW_INSTRUCTIONS
    if scene_description:
        user_text += f"\n\nSahne hedefi (referans): {scene_description[:500]}"

    try:
        response = model.generate_content(
            [user_text, img],
            generation_config={"response_mime_type": "application/json"},
        )
        raw = response.text or ""
    except Exception as e:
        ops.error("Gemini vision exception", exception=e)
        return None

    # JSON parse — bazen modeller markdown code-block sarar
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

    try:
        parsed = json.loads(raw)
    except Exception as e:
        ops.error("Vision JSON parse fail", message=raw[:300])
        return None

    cats = parsed.get("categories", {}) or {}
    if not cats:
        ops.warning("Vision categories boş", details=raw[:300])
        return None

    # Eksik kategorileri default'la doldur
    for c in VISION_RUBRIC_CATEGORIES:
        cats.setdefault(c, 5)

    score = float(parsed.get("score") or sum(cats.values()) / max(len(cats), 1))
    feedback = (parsed.get("feedback") or "").strip()
    passed = score >= settings.VISION_SCORE_THRESHOLD

    ops.info(
        f"Vision skor: {score:.2f} ({'PASS' if passed else 'FAIL'})",
        message=feedback[:200],
    )
    return {
        "score": score,
        "categories": cats,
        "feedback": feedback,
        "passed": passed,
    }


def build_retry_prompt(original_prompt: str, feedback: str, prev_categories: dict) -> str:
    """Vision feedback'ini kullanarak Kie prompt'unu iyileştir."""
    weak = []
    for cat, val in (prev_categories or {}).items():
        try:
            v = int(val)
        except Exception:
            continue
        if v < 7:
            weak.append(f"{cat}={v}")
    weak_str = ", ".join(weak) if weak else "general quality"

    addendum = (
        f"\n\n--- RETRY DIRECTIVE ---\n"
        f"Previous attempt scored low on: {weak_str}.\n"
        f"Reviewer feedback (Turkish): {feedback}\n"
        f"Apply the feedback strictly. Avoid the issues mentioned. "
        f"Re-emphasize: photorealistic editorial photography, single subject, "
        f"text-free image, dark editorial color palette, bottom-third compositionally quiet."
    )
    return original_prompt + addendum
