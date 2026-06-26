#!/usr/bin/env python3
"""
LLM Brand Extractor — Reel caption'ını bir insan gibi okuyup marka tespiti yapar.

Eski analyzer "kör" çalışıyordu: sadece @mention regex'i + hardcoded marka listesi.
Caption'da düz yazıyla geçen ("Synthix ile çalıştım") ya da listede olmayan markalar
sessizce kaçıyordu. Bu modül caption'ı GPT-4.1-nano'ya okutup yapılandırılmış
(Pydantic-doğrulanmış) çıktı alır.

Bu ANA yoldur. LLM cevap veremezse (API key yok, timeout, ValidationError) analyzer
eski keyword/mention mantığına düşer — bu modül sadece None döner.
"""

import json
import os

import requests
from pydantic import BaseModel, Field, ValidationError

OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4.1-nano"


# ── Pydantic şema ───────────────────────────────────────────────────────────
class ExtractedBrand(BaseModel):
    """Caption'da geçen tek bir marka/ürün."""

    name: str = Field(description="Markanın/ürünün adı, caption'da yazıldığı gibi.")
    instagram_handle: str = Field(
        default="",
        description=(
            "Eğer caption'da @ ile etiketlendiyse @'sız kullanıcı adı. "
            "Etiket yoksa boş string bırak."
        ),
    )
    is_ai_or_tech: bool = Field(
        description=(
            "True sadece marka bir AI/teknoloji aracı/uygulaması/yazılımı ise. "
            "Giyim, yemek, kozmetik, seyahat gibi markalar için False."
        )
    )
    is_collaboration: bool = Field(
        description=(
            "True ise içerik o markayla bir iş birliği/sponsorluk/reklam. "
            "False ise sadece geçerken bahsedilmiş."
        )
    )


class CaptionAnalysis(BaseModel):
    """Bir reel caption'ının tam analizi."""

    brands: list[ExtractedBrand] = Field(
        default_factory=list,
        description="Caption'da geçen tüm marka/ürün adları. Hiç yoksa boş liste.",
    )


_SYSTEM_PROMPT = (
    "You read Instagram reel captions and extract every brand or product name "
    "mentioned, whether it is @tagged or written in plain prose. "
    "A plain-text mention like 'Synthix ile çalıştım' counts exactly the same as "
    "an @synthix tag. For each brand decide if it is an AI/tech tool and whether "
    "the post is a paid collaboration or just a passing mention. "
    "If no brand is mentioned, return an empty list. Never invent brands."
)

# OpenAI native structured output — Pydantic'ten türetilmiş JSON schema.
_JSON_SCHEMA = {
    "name": "caption_analysis",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "brands": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "instagram_handle": {"type": "string"},
                        "is_ai_or_tech": {"type": "boolean"},
                        "is_collaboration": {"type": "boolean"},
                    },
                    "required": [
                        "name",
                        "instagram_handle",
                        "is_ai_or_tech",
                        "is_collaboration",
                    ],
                },
            }
        },
        "required": ["brands"],
    },
}


def _get_openai_key():
    """OpenAI API key'ini al (Railway env veya master.env)."""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    try:
        from env_loader import get_env as _ge

        return _ge("OPENAI_API_KEY") or None
    except ImportError:
        return None


def extract_brands_from_caption(caption, timeout=20):
    """Caption'ı LLM'e okutup yapılandırılmış marka listesi döndürür.

    Returns:
        CaptionAnalysis | None: Başarılıysa doğrulanmış analiz, aksi halde None
        (None → analyzer eski keyword/mention mantığına düşer).
    """
    caption = (caption or "").strip()
    if not caption:
        return CaptionAnalysis(brands=[])

    api_key = _get_openai_key()
    if not api_key:
        print("[LLM-EXTRACT] ⚠️ OpenAI API key yok — keyword fallback'e düşülüyor.")
        return None

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Caption:\n{caption[:1500]}"},
        ],
        "temperature": 0,
        "max_tokens": 600,
        "response_format": {"type": "json_schema", "json_schema": _JSON_SCHEMA},
    }

    try:
        resp = requests.post(
            OPENAI_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[LLM-EXTRACT] OpenAI hatası: {e} — keyword fallback'e düşülüyor.")
        return None

    # Native json_schema modunda content garanti JSON; yine de schema doğrula.
    try:
        return CaptionAnalysis.model_validate_json(content)
    except (ValidationError, json.JSONDecodeError) as e:
        print(f"[LLM-EXTRACT] ⚠️ Schema doğrulama hatası: {e} — keyword fallback'e.")
        return None
