"""ManyChat API istemcisi — yanıtı misafire ulaştırır.

Desen: cevabı bir custom field'a yaz, sonra o field'ı gösteren ManyChat flow'unu
tetikle. Platforma (IG/FB/WP) ve linkin olup olmamasına göre farklı field/flow kullanılır.

Token: CONFIG.manychat_token (kendi ManyChat hesabınızın API token'ı). Token yoksa veya
DRY_RUN=1 ise gerçek gönderim yapılmaz (log'a yazılır) — test için.

KENDİ KURULUMUN — field/flow id eşlemesi:
ManyChat custom field ve flow id'leri HER hesaba özeldir. Aşağıdaki PLATFORMS eşlemesi
JEneriktir; gerçek id'lerinizi MANYCHAT_PLATFORMS env değişkenine JSON olarak verin
(yapı aşağıdaki _DEFAULT_PLATFORMS ile aynı). Env verilmezse placeholder id'ler kullanılır
ve gerçek gönderim çalışmaz — bu beklenen davranıştır, kendi id'lerinizi girene kadar.
ManyChat'te bu id'leri: Settings → Custom Fields (field id) ve Automation → Flow
 ("..." menü → Copy Flow Namespace) üzerinden bulabilirsiniz.
"""

from __future__ import annotations

import json
import logging
import os

import requests

from config import CONFIG

log = logging.getLogger("hotel-chat.manychat")
_VERIFY_SSL = os.getenv("HOTELRUNNER_VERIFY_SSL", "1") != "0"
_BASE = "https://api.manychat.com/fb"
_TIMEOUT = 15

# Platform -> {field/flow id'leri}. PLACEHOLDER — kendi ManyChat hesabınızın gerçek
# id'leriyle değiştirin (tercihen MANYCHAT_PLATFORMS env JSON'u ile). Anahtar, gelen
# payload'daki platform değeriyle eşleşir (Instagram / Facebook / Whatsapp).
_DEFAULT_PLATFORMS = {
    "Instagram": {
        "answer_field": "<IG_ANSWER_FIELD_ID>", "link_field": "<IG_LINK_FIELD_ID>",
        "flow_no_link": "<IG_FLOW_NO_LINK_NS>",
        "flow_with_link": "<IG_FLOW_WITH_LINK_NS>",
        "wait_field": "<IG_WAIT_FIELD_ID>", "wait_flow": "<IG_WAIT_FLOW_NS>",
    },
    "Facebook": {
        "answer_field": "<FB_ANSWER_FIELD_ID>", "link_field": "<FB_LINK_FIELD_ID>",
        "flow_no_link": "<FB_FLOW_NO_LINK_NS>",
        "flow_with_link": "<FB_FLOW_WITH_LINK_NS>",
        "wait_field": "<FB_WAIT_FIELD_ID>", "wait_flow": "<FB_WAIT_FLOW_NS>",
    },
    "Whatsapp": {
        "answer_field": "<WA_ANSWER_FIELD_ID>", "link_field": "<WA_LINK_FIELD_ID>",
        "flow_no_link": "<WA_FLOW_NO_LINK_NS>",
        "flow_with_link": "<WA_FLOW_WITH_LINK_NS>",
        "wait_field": "<WA_WAIT_FIELD_ID>", "wait_flow": "<WA_WAIT_FLOW_NS>",
    },
}


def _load_platforms() -> dict:
    """MANYCHAT_PLATFORMS env'i (JSON) verilmişse onu, yoksa placeholder eşlemeyi kullan."""
    raw = os.getenv("MANYCHAT_PLATFORMS", "").strip()
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            log.warning("MANYCHAT_PLATFORMS geçersiz JSON — placeholder eşleme kullanılıyor")
    return _DEFAULT_PLATFORMS


PLATFORMS = _load_platforms()


def _post(path: str, body: dict) -> bool:
    if CONFIG.dry_run:
        log.info("[DRY_RUN] ManyChat %s %s", path, {k: body[k] for k in body if k != "field_value"})
        return True
    # Fail-closed: prod'da token yoksa "başarı" SANMA. Token'sız sessizce True dönmek,
    # canlıya geçişte env unutulduğunda "her şey yolunda" yalanı + tam teslim kaybı demekti.
    if not CONFIG.manychat_token:
        log.error("MANYCHAT_TOKEN yok — ManyChat %s GÖNDERİLEMEDİ (misafire cevap ulaşmaz)", path)
        return False
    headers = {"Authorization": f"Bearer {CONFIG.manychat_token}",
               "Content-Type": "application/json"}
    try:
        r = requests.post(f"{_BASE}{path}", headers=headers, json=body,
                          timeout=_TIMEOUT, verify=_VERIFY_SSL)
        if r.status_code >= 300:
            log.warning("ManyChat %s -> %s %s", path, r.status_code, r.text[:200])
            return False
        return True
    except Exception as e:
        log.warning("ManyChat %s hata: %s", path, e)
        return False


def set_custom_field(subscriber_id: str, field_id: str, value: str) -> bool:
    return _post("/subscriber/setCustomField",
                 {"subscriber_id": subscriber_id, "field_id": int(field_id), "field_value": value})


def send_flow(subscriber_id: str, flow_ns: str) -> bool:
    return _post("/sending/sendFlow", {"subscriber_id": subscriber_id, "flow_ns": flow_ns})


def _cfg(platform: str) -> dict | None:
    # Büyük/küçük harf toleransı: ManyChat 'instagram'/'WHATSAPP' gönderse de eşleşsin.
    if not platform:
        return None
    return PLATFORMS.get(platform) or PLATFORMS.get(platform.strip().capitalize())


def send_wait(subscriber_id: str, platform: str, text: str) -> None:
    """'Müsaitlik ve fiyatı kontrol ediyorum...' bekleme mesajı (uzun işlemler için)."""
    c = _cfg(platform)
    if not c:
        return
    set_custom_field(subscriber_id, c["wait_field"], text)
    send_flow(subscriber_id, c["wait_flow"])


def deliver_answer(subscriber_id: str, platform: str, message: str, link: str | None = None) -> bool:
    """Nihai cevabı (ve varsa rezervasyon linkini) misafire gönderir.

    Dönüş: True yalnızca cevap GERÇEKTEN teslim edildiyse (alan yazıldı + flow tetiklendi).
    Çağıran (main._process) bu değere bakıp "handled" mı "delivery_failed" mı olduğunu doğru loglar;
    böylece sessiz teslim hatası "başarı" gibi görünmez (SILENT-01)."""
    c = _cfg(platform)
    if not c:
        log.warning("Bilinmeyen platform: %s", platform)
        return False
    # Cevap alanı yazılamazsa flow tetikleme: misafir boş/eski içerikli flow almasın.
    if not set_custom_field(subscriber_id, c["answer_field"], message):
        log.warning("answer_field yazılamadı, flow tetiklenmedi (user=%s platform=%s)",
                    subscriber_id, platform)
        return False
    if link:
        # link_field yazımı da kontrol edilir: yazılamazsa eski/boş link gösteren flow yerine
        # linksiz flow'a düş (MC-05 — misafir bayat link görmesin).
        if set_custom_field(subscriber_id, c["link_field"], link):
            return send_flow(subscriber_id, c["flow_with_link"])
        log.warning("link_field yazılamadı, linksiz flow'a düşülüyor (user=%s)", subscriber_id)
        return send_flow(subscriber_id, c["flow_no_link"])
    return send_flow(subscriber_id, c["flow_no_link"])
