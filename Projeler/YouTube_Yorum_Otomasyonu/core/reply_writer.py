# -*- coding: utf-8 -*-
"""Faz 2 — içerik üreticinin sesinde cevap taslağı + güven üretimi.

corpus.retrieve_similar few-shot -> REPLY_MODEL ile taslak. Em-dash yasak (llm._no_emdash).
Güven: modelin öz-değeri ile retrieval sinyali (benzerlik) HARMANLANIR; benzer örnek
yoksa model ne derse desin güven düşük tutulur (uydurmaya karşı koruma)."""
from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

import config
from core import corpus as CORPUS
from core import llm


class _Draft(BaseModel):
    reply: str = Field(description="İçerik üreticinin sesinde, kısa, samimi cevap. Em-dash YOK.")
    confidence: Literal["high", "medium", "low"] = Field(
        description="Bu cevaptan ne kadar eminsin: high=net ve güvenli, "
                    "medium=fikrim var ama kontrol edilmeli, low=emin değilim.")


def _strict(node: dict):
    """OpenAI strict json_schema: her object'te additionalProperties false + tüm alanlar required."""
    if node.get("type") == "object":
        node["additionalProperties"] = False
        props = node.get("properties", {})
        if props:
            node["required"] = list(props.keys())
        for v in props.values():
            _strict(v)


_DRAFT_SCHEMA = _Draft.model_json_schema()
_strict(_DRAFT_SCHEMA)


REPLY_SYSTEM = f"""Sen {config.CREATOR_NAME}'sin: {config.CREATOR_BIO}.
Aşağıda bir izleyici yorumu ve SENİN geçmişte BENZER yorumlara verdiğin GERÇEK cevapların var.
Görevin: yeni yoruma, tam senin tarzında, kısa ve içten bir cevap yaz.

Kurallar:
- Geçmiş cevaplarındaki tonu birebir taklit et (samimi, sıcak, gerçek).
- Kısa tut: 1-2 cümle. Gereksiz uzatma, klişe pazarlama dili kullanma.
- Em-dash (—) KULLANMA. Türkçe ve doğal yaz.
- Bilmediğin/emin olmadığın bir şey sorulduysa uydurma; confidence=low ver.
- Benzer örneğin yoksa veya yorum muğlaksa confidence=low; net ve örneklerin destekliyorsa high."""


_ORDER = {"low": 0, "medium": 1, "high": 2}
_NAME = {0: "low", 1: "medium", 2: "high"}


def _blend_confidence(model_conf: str, top_sim: float, n: int) -> str:
    """Modelin öz-güveni ile retrieval sinyalini harmanla (ikisinin DÜŞÜĞÜ kazanır).
    Benzer geçmiş cevap yoksa model ne derse desin güven düşük."""
    # voyage-3 + bu corpus'ta gerçekten benzer Türkçe yorumlar ~0.5 bandında kümeleniyor;
    # eşikler buna göre kalibre (high zor kalsın -> ileride AUTO_POST yalnız çok eminleri yayınlar).
    if n == 0 or top_sim < 0.45:
        return "low"
    retr = "high" if top_sim >= 0.68 else "medium"
    return _NAME[min(_ORDER.get(model_conf, 1), _ORDER[retr])]


def generate_reply(comment_text: str, lang: str | None = None, video_title: str = "") -> dict:
    """Yeni yoruma taslak + güven üret.
    Döner: {reply, confidence, model_confidence, top_similarity, examples}.
    examples = retrieve_similar çıktısı (few-shot için kullanılan gerçek çiftler)."""
    try:
        examples = CORPUS.retrieve_similar(comment_text, k=5, lang=lang) or []
    except Exception:
        examples = []
    sims = [e.get("similarity", 0) or 0 for e in examples]
    top_sim = max(sims) if sims else 0.0

    shots = "\n".join(
        f"{i + 1}. İzleyici: \"{(e.get('comment_text') or '').strip()[:300]}\"\n"
        f"   Senin cevabın: \"{(e.get('reply_text') or '').strip()[:300]}\""
        for i, e in enumerate(examples)
    ) or "(benzer geçmiş cevap bulunamadı)"

    user = (f"Geçmişte benzer yorumlara verdiğin GERÇEK cevaplar:\n{shots}\n\n"
            f"Şimdi şu YENİ yoruma kendi tarzında cevap yaz.\n"
            f"Video: {video_title or '(bilinmiyor)'}\n"
            f"Yeni yorum: \"{comment_text.strip()[:500]}\"")

    payload = {
        "model": config.REPLY_MODEL,
        "max_tokens": 400,
        "temperature": 0.5,
        "messages": [
            {"role": "system", "content": REPLY_SYSTEM},
            {"role": "user", "content": user},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "reply_draft", "strict": True, "schema": _DRAFT_SCHEMA},
        },
    }
    data = llm._post(payload)
    parsed = _Draft(**json.loads(data["choices"][0]["message"]["content"]))
    return {
        "reply": llm._no_emdash(parsed.reply.strip()),
        "confidence": _blend_confidence(parsed.confidence, top_sim, len(examples)),
        "model_confidence": parsed.confidence,
        "top_similarity": top_sim,
        "examples": examples,
    }
