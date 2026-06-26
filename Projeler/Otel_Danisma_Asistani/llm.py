"""Groq LLM sarmalayıcı — sohbet (tool-calling) + ses transkripsiyon.

Maliyet politikası: Opus/Sonnet API yasak. Groq `openai/gpt-oss-120b` ucuz workhorse.
Ses için Groq `whisper-large-v3`.
"""

from __future__ import annotations

import os

import httpx
from groq import Groq

from config import CONFIG

# Lokal SSL-kesme ortamında doğrulamayı kapatmak için (fiyat modülüyle aynı bayrak).
_VERIFY_SSL = os.getenv("HOTELRUNNER_VERIFY_SSL", "1") != "0"


def _client() -> Groq:
    if not CONFIG.groq_api_key:
        raise RuntimeError("GROQ_API_KEY tanımlı değil (master.env veya .env)")
    # base_url'i AÇIKÇA ver: master.env'deki GROQ_BASE_URL (=.../openai/v1) OpenAI-uyumlu
    # istemciler içindir; groq SDK kendisi /openai/v1 ekler, yoksa path ikiye katlanır.
    # timeout 30s + max_retries=1: tek mesajın worst-case süresini sınırla (thread-tutmayı
    # azalt). Geçici Groq hatası (429/5xx/timeout) sonunda istisna olur → main._process fallback'e düşer.
    return Groq(api_key=CONFIG.groq_api_key,
                base_url="https://api.groq.com",
                max_retries=1,
                http_client=httpx.Client(verify=_VERIFY_SSL, timeout=30.0))


def chat(messages: list[dict], tools: list[dict] | None = None,
         model: str | None = None, temperature: float = 0.2,
         max_tokens: int = 2000, tool_choice: str = "auto",
         top_p: float = 0.9, frequency_penalty: float = 0.3):
    """Groq chat completion. tool_calls için ham message nesnesini döndürür.

    top_p + frequency_penalty: açık model (gpt-oss-120b) bazı çelişkili tool
    girdilerinde tekrar döngüsüne girip bozuk metin üretiyordu ("yarım yarım yarım",
    "Üzgün Üzgün"). Uzun kuyruğu kırpıp tekrarı cezalandırınca bu çöküş engellenir;
    normal cevaplar etkilenmez (2026-06-15, canlı izleme bulgusu).
    """
    kw: dict = {
        "model": model or CONFIG.agent_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
    }
    if tools:
        kw["tools"] = tools
        kw["tool_choice"] = tool_choice
    resp = _client().chat.completions.create(**kw)
    return resp.choices[0].message


def transcribe(audio_bytes: bytes, filename: str = "audio.ogg", language: str = "tr") -> str:
    """Ses → metin (Groq whisper)."""
    r = _client().audio.transcriptions.create(
        file=(filename, audio_bytes),
        model=CONFIG.whisper_model,
        language=language,
    )
    return (r.text or "").strip()
