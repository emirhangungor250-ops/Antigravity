# -*- coding: utf-8 -*-
"""LLM katmanı — OpenAI direkt (data-shared bedava) / OpenRouter yönlendirmeli.

Faz 1: yorumları "cevaplanmaya değerlik" sinyaline göre sınıfla (akıllı sıralama).
  Kör otomasyon yasağı: yorumun ne olduğu (soru/dolu/övgü/spam) yargısı KELIMEYLE
  değil LLM ile verilir. LLM patlarsa güvenli varsayıma düşülür (hiçbir yorum gizlenmez).

Faz 2 cevap üretimi (reply_writer.py) bu modülün _post/_route altyapısını kullanır.
"""
import json
import time
from typing import Literal

import requests
from pydantic import BaseModel, Field

import config


def _route(model: str):
    """Model adına göre (endpoint_url, api_key, ekstra_header)."""
    if "/" in model:  # provider/model slug -> OpenRouter
        return (config.OPENROUTER_URL, config.OPENROUTER_API_KEY,
                {"X-Title": "YouTube Yorum Otomasyonu"})
    return (config.OPENAI_DIRECT_URL, config.OPENAI_DIRECT_KEY, {})


def _post(payload: dict, *, timeout: int = 90, retries: int = 2) -> dict:
    """chat/completions; geçici hatada (429/5xx/timeout) yeniden dener."""
    url, key, extra = _route(payload["model"])
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}", **extra}
    last_err = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                if "error" in data:
                    raise RuntimeError(f"LLM error: {str(data['error'])[:200]}")
                return data
            if r.status_code in (408, 429, 500, 502, 503, 504):
                last_err = RuntimeError(f"LLM {r.status_code}: {r.text[:160]}")
            else:
                raise RuntimeError(f"LLM {r.status_code}: {r.text[:200]}")
        except (requests.Timeout, requests.ConnectionError) as e:
            last_err = e
        if attempt < retries:
            time.sleep(1.5 * (attempt + 1))
    raise last_err or RuntimeError("LLM çağrısı başarısız")


def _no_emdash(t: str) -> str:
    """Em-dash kullanma kuralı (Türkçe içerik tercihi). Modele güvenme, çıktıdan temizle."""
    t = t.replace(" — ", ", ").replace("—", ", ")
    t = t.replace(" – ", " - ").replace("–", "-")
    return t.replace(" ,", ",").replace("  ", " ")


# ── Faz 1: yorum "cevaplanmaya değerlik" sınıflaması (batch) ──────────
class WorthItem(BaseModel):
    idx: int = Field(description="Girdideki yorumun sıra numarası (0-tabanlı).")
    kind: Literal["question", "substantive", "praise", "emoji_only", "spam"] = Field(
        description="question=bir şey soruyor; substantive=görüş/deneyim/dolu yorum; "
                    "praise=kısa övgü/teşekkür; emoji_only=sadece emoji/çok kısa; spam=alakasız/reklam/bot.")
    score: int = Field(description="Cevaplanmaya değerlik 0-100. Soru/dolu yüksek, kısa övgü düşük, spam ~0.")
    lang: Literal["tr", "en", "other"] = Field(description="Yorumun dili.")


class WorthBatch(BaseModel):
    items: list[WorthItem]


def _worth_schema() -> dict:
    s = WorthBatch.model_json_schema()
    # OpenAI strict: tüm alanlar required + additionalProperties false (iç içe dahil)
    def _strict(node: dict):
        if node.get("type") == "object":
            node["additionalProperties"] = False
            props = node.get("properties", {})
            if props:
                node["required"] = list(props.keys())
            for v in props.values():
                _strict(v)
        for key in ("items", "$defs", "definitions"):
            sub = node.get(key)
            if isinstance(sub, dict):
                if key in ("$defs", "definitions"):
                    for d in sub.values():
                        _strict(d)
                else:
                    _strict(sub)
    _strict(s)
    return s


_WORTH_SCHEMA = _worth_schema()

WORTH_SYSTEM = f"""Sen {config.CREATOR_NAME} adlı içerik üreticisinin ({config.CREATOR_BIO}) YouTube
yorumlarını onun adına tarayan bir asistansın. Görevin: her yorumu "cevaplanmaya değerlik" açısından
sınıflamak ki içerik üretici önce gerçekten cevap isteyenlere baksın.

Kurallar (kind):
- question: açık, somut, cevaplanabilir bir şey soruyor (yardım/bilgi istiyor).
- substantive: deneyim, görüş, eleştiri, dolu bir katkı.
- praise: kısa övgü/teşekkür ("harika video", "eline sağlık").
- emoji_only: sadece emoji veya tek-iki kelime anlamsız ("slm", "ben biliyom").
- spam: alakasız reklam, bot, link-yemi, hakaret.

score (0-100) = "Buna anlamlı, DOLU bir cevap yazılabilir mi?":
- Açık/somut soru veya dolu katkı: 70-100 (gerçekten cevap üretilebiliyorsa yüksek).
- Kısa övgü: 20-40. Emoji/anlamsız: 5-15. Spam: 0-5.
- KRİTİK: çok kısa, bağlamsız, ne sorduğu/dediği belirsiz fragmanlar ("nerde nasıl",
  "nasıl ya", "ben biliyom", tek kelime) anlamlı cevap üretmeye YETMEZ. kind question
  olsa bile score DÜŞÜK (<=35). Yüksek score yalnızca kendi içinde anlaşılır,
  dolu bir cevap verilebilecek yorumlara.

- lang: yorumun yazıldığı dil (tr/en/other).
HİÇBİR yorumu atlamadan, girdideki HER yorum için tam bir kayıt döndür (idx ile eşleştir)."""


def classify_worth_batch(comments: list[str]) -> list[dict]:
    """Yorum listesini sınıfla. Döner: [{idx,kind,score,lang}, ...] (girdiyle hizalı).
    LLM patlarsa güvenli varsayım: substantive / score=60 / lang heuristic (fail-open, hiçbir şey gizlenmez)."""
    if not comments:
        return []
    numbered = "\n".join(f"[{i}] {(c or '').strip()[:400]}" for i, c in enumerate(comments))
    payload = {
        "model": config.WORTH_MODEL,
        "max_tokens": 4000,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": WORTH_SYSTEM},
            {"role": "user", "content": f"Aşağıdaki {len(comments)} yorumu sınıfla:\n\n{numbered}"},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "worth_batch", "strict": True, "schema": _WORTH_SCHEMA},
        },
    }
    try:
        data = _post(payload)
        content = data["choices"][0]["message"]["content"]
        parsed = WorthBatch(**json.loads(content))
        by_idx = {it.idx: it for it in parsed.items}
    except Exception:
        by_idx = {}

    out = []
    for i, c in enumerate(comments):
        it = by_idx.get(i)
        if it:
            out.append({"idx": i, "kind": it.kind, "score": it.score, "lang": it.lang})
        else:
            # fail-open: sınıflama patladıysa eşik ÜSTÜ tut (60), emin değilken yorumu gizleme
            out.append({"idx": i, "kind": "substantive", "score": 60, "lang": _guess_lang(c)})
    return out


_TR_CHARS = set("çğıöşüÇĞİÖŞÜ")


def _guess_lang(text: str) -> str:
    """LLM fallback'i için kaba dil tahmini (Türkçe karakter varsa tr)."""
    t = text or ""
    if any(ch in _TR_CHARS for ch in t):
        return "tr"
    return "en"
