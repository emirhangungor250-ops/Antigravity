"""
Personel Mail Hatırlatıcı — Groq LLM Client
=============================================
Groq API üzerinden LLM çağrıları yapar.
Model: openai/gpt-oss-120b
"""

import os
import re
import json
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Groq config
GROQ_MODEL = "openai/gpt-oss-120b"
MAX_RETRIES = 2


def _get_client():
    """Groq client oluştur (lazy init)."""
    from groq import Groq
    
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY tanımlanmamış. master.env'den yükle veya env'e set et."
        )
    
    return Groq(api_key=api_key, timeout=30.0)


def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    LLM çıktısından JSON objesini regex ile çıkar.
    Model bazen ```json ... ``` wrapper ekliyor veya ek açıklama yazıyor.
    """
    if not text:
        return None
    
    # 1) Direkt parse dene
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # 2) ```json ... ``` bloğu ara
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 3) Brace-depth walk: ilk { → eşleşen } arası (deep nesting destekli)
    start = text.find('{')
    if start >= 0:
        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == '\\':
                escape = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:i+1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break  # bozuk → regex fallback'a düş

    # 4) Regex fallback (1 seviye nesting) — bozuk/truncated için
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _validate_result(result: Dict[str, Any]) -> bool:
    """Sonuçta zorunlu alanların olup olmadığını kontrol et."""
    required = ["category", "confidence"]
    return all(k in result for k in required)


def analyze_thread(thread_messages: str, system_prompt: str) -> Optional[Dict[str, Any]]:
    """
    Thread mesajlarını LLM ile analiz et.
    Retry + JSON extraction fallback ile dayanıklı.
    
    Args:
        thread_messages: Thread'deki mesajların metin hali
        system_prompt: Sistem promptu (analiz talimatları)
    
    Returns:
        JSON parse edilmiş analiz sonucu veya None (hata durumunda)
    """
    client = _get_client()
    last_error = None
    
    for attempt in range(MAX_RETRIES):
        try:
            # gpt-oss-120b reasoning model — reasoning'i suppress et, max_tokens'ı
            # JSON için yeterli aralıkta tut (önceki 800 hem reasoning hem cevabı
            # sığdıramayıp truncate'ye yol açıyordu).
            kwargs = {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": thread_messages},
                ],
                "temperature": 0.1,
                "max_tokens": 3000,
            }
            try:
                response = client.chat.completions.create(
                    **kwargs,
                    reasoning_format="hidden",  # gpt-oss reasoning'ini content'e karıştırma
                )
            except TypeError:
                # SDK reasoning_format'u tanımıyorsa fallback
                response = client.chat.completions.create(**kwargs)

            content = response.choices[0].message.content
            # Reasoning model bazen content'i boş bırakıp reasoning field'a yazıyor
            if not content:
                msg_obj = response.choices[0].message
                content = (
                    getattr(msg_obj, "reasoning", None)
                    or getattr(msg_obj, "reasoning_content", None)
                    or ""
                )
            result = _extract_json_from_text(content)
            
            if result and _validate_result(result):
                logger.debug(f"LLM analiz sonucu: {result}")
                return result
            
            logger.warning(
                f"LLM yanıtı geçersiz (attempt {attempt + 1}/{MAX_RETRIES}): "
                f"{content[:200] if content else '(boş)'}"
            )
            last_error = f"Geçersiz JSON yapısı: {content[:100] if content else '(boş)'}"

        except Exception as e:
            last_error = str(e)
            logger.warning(f"Groq API hatası (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
        
        # Son denemede bekleme yapma
        if attempt < MAX_RETRIES - 1:
            time.sleep(1)
    
    logger.error(f"LLM analizi {MAX_RETRIES} denemeden sonra başarısız: {last_error}")
    return None
