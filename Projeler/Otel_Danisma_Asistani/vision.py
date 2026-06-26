"""Görsel betimleme — misafirin gönderdiği görseli kısa Türkçe metne çevirir.

Maliyet politikası (ZORUNLU): SADECE gpt-4o-mini + OPENAI_API_KEY.
gpt-4o / Opus / Sonnet YASAK (pahalı modeller varsayılan yapılmaz).

ManyChat CDN URL'leri imzalı + User-Agent bloklu olabilir; OpenAI'nin URL'i kendi çekmesi
sık başarısız olur. Bu yüzden görseli BİZ indirip base64 data URI olarak gömeriz.
Hata/None her zaman güvenlidir: betimleme alınamazsa ajan yine de nazik cevap verir.
"""

from __future__ import annotations

import base64
import logging
import os

import httpx

from config import CONFIG

log = logging.getLogger("hotel-chat.vision")
_VERIFY_SSL = os.getenv("HOTELRUNNER_VERIFY_SSL", "1") != "0"

_DOWNLOAD_TIMEOUT = 8.0  # ManyChat CDN gecikme toleransı
_API_TIMEOUT = 30.0
_API_URL = "https://api.openai.com/v1/chat/completions"
# Bazı CDN'ler (Wikimedia, bazı Meta uçları) User-Agent'sız isteği 403'ler. Tarayıcı UA'sı gönder.
_UA = "Mozilla/5.0 (compatible; HotelChatBot/2.0)"

# Maliyet politikası SERT KİLİDİ: yalnızca bu modellere izin var. VISION_MODEL env'i
# yanlışlıkla/kasıtla gpt-4o gibi pahalı bir modele set edilse bile gpt-4o-mini'ye düşülür
# (yorumun vaat ettiği güvence kodda gerçektir). Yeni ucuz model eklenecekse buraya yazılır.
_ALLOWED_MODELS = {"gpt-4o-mini"}
_DEFAULT_MODEL = "gpt-4o-mini"

VISION_SYSTEM = (
    "Sen bir tesisin müşteri temsilcisisin. Misafirin gönderdiği görseli kısa Türkçe "
    "açıklayacaksın. Amaç: bir sonraki cevabı üretirken konuyu bilmek. Spekülasyon yapma, "
    "görselde net ne varsa söyle. 2-4 cümle yeterli."
)


def _download_as_data_uri(url: str) -> str | None:
    """Görseli indir, image/* doğrula, boyut sınırla, base64 data URI döndür.

    Dönüş: 'data:image/jpeg;base64,...' veya başarısızsa None (log + güvenli)."""
    max_bytes = CONFIG.vision_max_mb * 1024 * 1024
    try:
        with httpx.Client(timeout=_DOWNLOAD_TIMEOUT, verify=_VERIFY_SSL,
                          follow_redirects=True, headers={"User-Agent": _UA}) as client:
            res = client.get(url)
            res.raise_for_status()
            ct = (res.headers.get("content-type", "") or "").split(";")[0].strip().lower()
            if not ct.startswith("image/"):
                log.warning("[vision] beklenmeyen content-type: %s", ct or "yok")
                return None
            buf = res.content
            if len(buf) > max_bytes:
                log.warning("[vision] görsel çok büyük: %d bayt (sınır %d)", len(buf), max_bytes)
                return None
            b64 = base64.b64encode(buf).decode("ascii")
            return f"data:{ct};base64,{b64}"
    except Exception as e:
        log.warning("[vision] indirme hatası: %s", e)
        return None


def describe_image(image_url: str, user_hint: str = "") -> str | None:
    """Görseli betimle, 2-4 cümlelik Türkçe açıklama döndür (veya None).

    None = anahtar yok / indirme başarısız / API hatası. Çağıran bunu nazik fallback ile karşılar.
    """
    if not CONFIG.openai_api_key:
        log.warning("[vision] OPENAI_API_KEY yok — görsel betimlenemiyor")
        return None

    data_uri = _download_as_data_uri(image_url)
    if not data_uri:
        return None

    user_text = (
        f'Misafir şu metni de yazdı: "{user_hint}". Bunu görseli yorumlarken dikkate al.'
        if user_hint and len(user_hint) > 1
        else "Misafir sadece görseli gönderdi, başka metin yok."
    )

    # Maliyet güvenliği SERT KİLİT: model beyaz listede değilse gpt-4o-mini'ye düşülür.
    # Böylece VISION_MODEL=gpt-4o set edilse bile pahalı model API'den tüketilemez.
    model = CONFIG.vision_model if CONFIG.vision_model in _ALLOWED_MODELS else _DEFAULT_MODEL
    if CONFIG.vision_model not in _ALLOWED_MODELS:
        log.warning("[vision] izinsiz model '%s' istendi → %s'ye düşüldü (maliyet kilidi)",
                    CONFIG.vision_model, _DEFAULT_MODEL)
    try:
        with httpx.Client(timeout=_API_TIMEOUT, verify=_VERIFY_SSL) as client:
            resp = client.post(
                _API_URL,
                headers={
                    "Authorization": f"Bearer {CONFIG.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 400,
                    "messages": [
                        {"role": "system", "content": VISION_SYSTEM},
                        {"role": "user", "content": [
                            {"type": "image_url", "image_url": {"url": data_uri}},
                            {"type": "text", "text": user_text},
                        ]},
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                log.warning("[vision] API error: %s", data.get("error"))
                return None
            text = (data.get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()
            return text or None
    except Exception as e:
        log.warning("[vision] API çağrı hatası: %s", e)
        return None
