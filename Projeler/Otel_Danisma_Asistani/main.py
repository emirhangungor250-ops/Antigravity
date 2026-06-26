"""Otel Danışma Asistanı — FastAPI servisi.

Endpoint'ler:
  GET  /health   — sağlık
  POST /price    — (Phase 1) müsaitlik + konaklama fiyatı (iç kullanım / köprü)
  POST /webhook  — (Phase 2) ManyChat'ten gelen misafir mesajı; bot cevabı ManyChat ile döner

ManyChat deseni: webhook anında 200 döner, mesaj arka planda işlenir, cevap ManyChat
API'siyle (custom field + flow) misafire gönderilir.

Çalıştırma (Railway): uvicorn main:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import logging
import os

import requests
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

import hotelrunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("hotel-chat")

PRICE_SHARED_SECRET = os.getenv("PRICE_SHARED_SECRET", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
_VERIFY_SSL = os.getenv("HOTELRUNNER_VERIFY_SSL", "1") != "0"
_AUDIO_FAIL = "Sesli mesajınızı anlayamadım, kısaca yazabilir misiniz?"
_IMAGE_FAIL = "Gönderdiğiniz görseli şu an inceleyemedim. Sormak istediğinizi kısaca yazabilir misiniz?"
_MEDIA_FAIL = "Gönderdiğiniz içeriği şu an inceleyemedim. Sormak istediğinizi kısaca yazabilir misiniz?"

app = FastAPI(title="Otel Danışma Asistanı", version="2.0")


# --------------------------------------------------------------------------- #
# /health + /price (Phase 1)                                                   #
# --------------------------------------------------------------------------- #
class RoomIn(BaseModel):
    adult_count: int = 2
    child_count: int = 0
    child_ages: list[int] = Field(default_factory=list)


class PriceRequest(BaseModel):
    checkin_date: str
    checkout_date: str
    rooms: list[RoomIn] | None = None
    adult_count: int | None = None
    child_count: int | None = None
    child_ages: list[int] | None = None
    room_count: int | None = None


def _rooms_from_request(req: PriceRequest) -> list[dict]:
    if req.rooms:
        return [r.model_dump() for r in req.rooms]
    adult = req.adult_count if req.adult_count is not None else 2
    child = req.child_count or 0
    ages = req.child_ages or []
    n = req.room_count or 1
    return [{"adult_count": adult, "child_count": child, "child_ages": ages} for _ in range(max(n, 1))]


@app.get("/health")
def health() -> dict:
    # Liveness için status hep "ok". delivery_ready: cutover'da ManyChat token'ı set mi —
    # False ise bot ayakta ama misafire cevap GÖNDEREMEZ (sessiz felaket erken görünür).
    from config import CONFIG
    delivery_ready = CONFIG.dry_run or bool(CONFIG.manychat_token)
    return {"status": "ok", "service": "hotel-chat",
            "delivery_ready": delivery_ready, "dry_run": CONFIG.dry_run}


@app.post("/price")
def price(req: PriceRequest, x_price_key: str | None = Header(default=None)) -> dict:
    if PRICE_SHARED_SECRET and x_price_key != PRICE_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="invalid key")
    rooms = _rooms_from_request(req)
    try:
        result = hotelrunner.quote(req.checkin_date, req.checkout_date, rooms)
        log.info("price ok %s->%s rooms=%d available=%s",
                 req.checkin_date, req.checkout_date, len(rooms), result["available"])
        return result
    except hotelrunner.HotelRunnerError as e:
        log.warning("price fallback: %s", e)
        link = hotelrunner.booking_link(
            *hotelrunner._shift_past_dates(req.checkin_date, req.checkout_date),
            hotelrunner._norm_rooms(rooms),
        )
        return {"available": None, "checkin": req.checkin_date, "checkout": req.checkout_date,
                "link": link, "rooms": [],
                "message": ("Şu an anlık fiyatı getiremedim. Güncel müsaitlik ve fiyatı şu "
                            "bağlantıdan görebilirsiniz.")}


# --------------------------------------------------------------------------- #
# /webhook (Phase 2 — ManyChat botu)                                          #
# --------------------------------------------------------------------------- #
def _extract(payload: dict) -> tuple[str | None, str | None, str | None]:
    """ManyChat payload'ından (user_id, message, platform) çıkar. Düz veya body-altı."""
    b = payload.get("body") if isinstance(payload.get("body"), dict) else payload
    user_id = b.get("kullanici_id") or b.get("subscriber_id") or b.get("user_id")
    message = b.get("last_text_input") or b.get("message") or b.get("text")
    platform = b.get("platform")
    return user_id, message, platform


def _transcribe_audio(url: str) -> str | None:
    """Ses URL'ini indir + Groq whisper ile metne çevir. Çözülemezse None."""
    try:
        import llm
        r = requests.get(url, timeout=20, verify=_VERIFY_SSL,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; HotelChatBot/2.0)"})
        r.raise_for_status()
        text = llm.transcribe(r.content, filename="audio.mp4", language="tr")
        log.info("audio transcribed: %s", (text or "")[:80])
        return text or None
    except Exception as e:
        log.warning("transcribe failed: %s", e)
        return None


def _resolve_message(raw: str) -> tuple[str | None, str]:
    """Tek bir ham mesajı sınıfla + ajana verilecek metne çöz.

    Dönüş: (resolved_text | None, kind). None = çözülemeyen medya (ses indi ama whisper
    boş, ya da görsel betimlenemedi) → çağıran nazik fallback yollar, hafızayı kirletmez.
    text/normal mesaj her zaman (metin, "text") döner.
    """
    import media
    kind = media.classify_media_url(raw)

    if kind == "audio":
        text = _transcribe_audio(raw)
        return (text, "audio")  # None ise çözülemedi

    if kind == "image":
        import vision
        desc = vision.describe_image(raw)
        if not desc:
            return (None, "image")  # betimlenemedi → fallback
        # Ajana etiketli metin: görsel olduğunu + içeriğini bilsin.
        return (f"[Misafir bir görsel gönderdi: {desc}]", "image")

    # Düz metin: aynen geçer.
    return (raw, "text")


def _process_batch(user_id: str, platform: str, raw_messages: list[str]) -> None:
    """Coalesce worker'ın TEK işleme callback'i.

    Her ham mesaj media.classify ile sınıflanır (ses→whisper, görsel→vision, metin→aynen),
    çözülen metinler birleştirilir, TEK agent.respond + TEK deliver_answer yapılır.
    Çözülemeyen medya varsa (ses/görsel hepsi başarısız ve hiç metin yoksa) nazik fallback gönderilir.

    Korunan sözleşmeler: deliver_answer BOOL kontrolü, asistan cevabı yalnızca teslim olunca
    hafızaya yazılır, agent.FALLBACK_TEXT ile sessizlik engellenir."""
    import agent
    import manychat
    import memory

    resolved: list[str] = []
    failed_kinds: set[str] = set()
    for raw in raw_messages:
        try:
            text, kind = _resolve_message(raw)
        except Exception as e:
            log.exception("resolve error user=%s: %s", user_id, e)
            text, kind = None, "text"
        if text:
            resolved.append(text)
        elif kind in ("audio", "image"):
            failed_kinds.add(kind)  # bu öğe bir medyaydı ama çözülemedi

    # Hiç çözülmüş metin yok: başarısız medyaysa MEDYA TÜRÜNE uygun nazik açıklama yolla
    # (görsel başarısızlığında "sesli mesaj" deme).
    if not resolved:
        if failed_kinds:
            msg = (_AUDIO_FAIL if failed_kinds == {"audio"}
                   else _IMAGE_FAIL if failed_kinds == {"image"}
                   else _MEDIA_FAIL)
            try:
                manychat.deliver_answer(user_id, platform, msg, None)
            except Exception as e:
                log.warning("media-fail deliver error user=%s: %s", user_id, e)
        else:
            log.info("boş batch user=%s — işleme yok", user_id)
        return

    combined = " ".join(resolved)

    # Ajan cevabı (hata olursa fallback'e düş — sessizlik YOK).
    try:
        history = memory.load(user_id)
        result = agent.respond(combined, history)
        answer = (result.get("text") or "").strip() or agent.FALLBACK_TEXT
        link = result.get("link")
    except Exception as e:
        log.exception("agent error user=%s: %s", user_id, e)
        answer, link = agent.FALLBACK_TEXT, None

    # Teslim + hafıza.
    try:
        delivered = manychat.deliver_answer(user_id, platform, answer, link)
        # Misafir mesaj(lar)ını her durumda kaydet (aldık). Birleştirilmiş metni tek
        # 'user' satırı olarak yaz (ajanın gördüğü girdiyle hafıza tutarlı kalsın).
        memory.save(user_id, platform, "user", combined)
        if delivered:
            memory.save(user_id, platform, "assistant", answer)
            log.info("handled user=%s platform=%s parts=%d link=%s",
                     user_id, platform, len(resolved), bool(link))
        else:
            log.error("delivery_failed user=%s platform=%s — misafire cevap ULAŞMADI", user_id, platform)
    except Exception as e:
        log.exception("deliver/save error user=%s: %s", user_id, e)


@app.post("/webhook")
async def webhook(request: Request,
                  x_webhook_secret: str | None = Header(default=None)) -> dict:
    if WEBHOOK_SECRET and x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="invalid secret")
    payload = await request.json()
    user_id, message, platform = _extract(payload)
    # Ham giriş logu (gözlemlenebilirlik + Reel/medya teşhisi): ManyChat'in last_text_input'a
    # ne koyduğunu birebir gör (örn Reel paylaşımında bağlantı/referans ne geliyor).
    log.info("inbound user=%s platform=%s msg=%r", user_id, platform, (message or "")[:200])
    if not user_id or not message or not platform:
        log.warning("eksik payload: user=%s msg=%s platform=%s", user_id, bool(message), platform)
        return {"status": "ignored", "reason": "missing fields"}
    # Burst coalesce: mesajı kuyruğa ekle; worker yoksa AYRILMIŞ havuzda başlat, varsa sadece
    # sıraya. background_add geçilmez → coalesce kendi ThreadPoolExecutor'unu kullanır; böylece
    # uzun-bloklayan worker'lar anyio'nun ortak webhook/Phase-1 thread havuzunu açlığa düşürmez.
    import coalesce
    coalesce.enqueue(user_id, platform, message, _process_batch)
    return {"status": "received"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
