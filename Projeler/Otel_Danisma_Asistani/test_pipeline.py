"""Medya pipeline testi (D1 + D2 + D3) — TÜM dış çağrılar STUB'lanır.

GERÇEK API YAKMA: OpenAI / Groq / ManyChat / Supabase / ağ hiçbir gerçek istek atmaz.
Çalıştır: python3 test_pipeline.py  (sıfır exit = geçti, non-zero = kaldı).

Kapsam:
  (a) classify content-type eşlemesi (audio/image/video/text + sezgisel + redirect güvenliği)
  (b) foto → vision çağrılır, ajana etiketli açıklama gider
  (c) ses → transcribe çağrılır
  (d) metin → aynen geçer
  (e) 3 mesajlık burst → TEK agent.respond + TEK deliver_answer
  (f) coalesce timing (kısa pencere env ile)
"""

from __future__ import annotations

import os
import sys
import time

# === Test ortamı: gerçek anahtarları DEVRE DIŞI bırak, pencereleri kısalt ===
# config import'tan ÖNCE set edilmeli (Config.from_env okuma anında çalışır).
os.environ["DRY_RUN"] = "1"                     # ManyChat gerçek gönderim yok
os.environ["COALESCE_INITIAL_MS"] = "200"       # test için kısa pencere
os.environ["COALESCE_STRAGGLER_MS"] = "100"
os.environ["COALESCE_MAX_ITER"] = "3"
os.environ["OPENAI_API_KEY"] = "test-key-not-real"   # vision _download'ı biz stub'larız
os.environ["GROQ_API_KEY"] = "test-key-not-real"
os.environ.setdefault("HOTELRUNNER_VERIFY_SSL", "0")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config  # noqa: E402
config.CONFIG = config.Config.from_env()  # env override'larını yeniden yükle

import media   # noqa: E402
import vision  # noqa: E402
import coalesce  # noqa: E402
import main    # noqa: E402

_FAILS: list[str] = []
_PASSES = 0


def check(cond: bool, label: str) -> None:
    global _PASSES
    if cond:
        _PASSES += 1
        print(f"  PASS  {label}")
    else:
        _FAILS.append(label)
        print(f"  FAIL  {label}")


# --------------------------------------------------------------------------- #
# Stub yardımcıları                                                           #
# --------------------------------------------------------------------------- #
class _FakeResp:
    def __init__(self, status=200, headers=None):
        self.status_code = status
        self.headers = headers or {}

    def close(self):
        pass


def _stub_probe(content_type=None, status=200):
    """media.requests.head/get'i sahte Content-Type ile değiştir."""
    def fake_head(url, **kw):
        return _FakeResp(status, {"content-type": content_type} if content_type else {})

    def fake_get(url, **kw):
        return _FakeResp(status, {"content-type": content_type} if content_type else {})
    media.requests.head = fake_head
    media.requests.get = fake_get


# --------------------------------------------------------------------------- #
# (a) classify content-type eşlemesi                                          #
# --------------------------------------------------------------------------- #
def test_classify():
    print("\n[a] classify_media_url content-type eşlemesi")

    _stub_probe("audio/mp4")
    check(media.classify_media_url("https://cdn.example.com/v.mp4") == "audio",
          "audio/* -> audio")

    _stub_probe("image/jpeg")
    check(media.classify_media_url("https://cdn.example.com/p.jpg") == "image",
          "image/* -> image")

    _stub_probe("video/mp4")
    check(media.classify_media_url("https://cdn.example.com/clip") == "image",
          "video/* -> image (vision'a)")

    # Düz metin (URL değil) → text, probe hiç çağrılmaz
    check(media.classify_media_url("merhaba fiyat öğrenebilir miyim") == "text",
          "düz metin -> text")
    check(media.classify_media_url("") == "text", "boş -> text")

    # Content-Type text/html ama uzantı ses → sezgisel ses
    _stub_probe("text/html")
    check(media.classify_media_url("https://lookaside.fbsbx.com/x.m4a") == "audio",
          "html ct + ses host -> sezgisel audio")
    check(media.classify_media_url("https://cdn.example.com/p.png") == "image",
          "html ct + görsel uzantı -> sezgisel image")
    # Hiç sinyal yok → güvenli text
    check(media.classify_media_url("https://example.com/page") == "text",
          "sinyal yok -> güvenli text")

    # Redirect (3xx) → Content-Type'a güvenme, sezgisele düş (ses uzantısı yoksa text)
    _stub_probe("audio/mp4", status=302)
    check(media.classify_media_url("https://example.com/redir") == "text",
          "redirect -> ct yok sayılır, sezgisel text")


# --------------------------------------------------------------------------- #
# (b/c/d) _resolve_message: görsel / ses / metin                              #
# --------------------------------------------------------------------------- #
def test_resolve():
    print("\n[b/c/d] _resolve_message medya çözümü")

    # (b) Görsel → vision çağrılır, etiketli açıklama döner
    _stub_probe("image/jpeg")
    vision_calls = []

    def fake_describe(url, user_hint=""):
        vision_calls.append(url)
        return "Görselde otelin açık havuzu ve şezlonglar görünüyor."
    orig_describe = vision.describe_image
    vision.describe_image = fake_describe
    try:
        text, kind = main._resolve_message("https://cdn.example.com/havuz.jpg")
        check(kind == "image" and len(vision_calls) == 1, "görsel -> vision çağrıldı")
        check(text is not None and text.startswith("[Misafir bir görsel gönderdi:"),
              "görsel -> ajana etiketli açıklama")
    finally:
        vision.describe_image = orig_describe

    # Görsel betimlenemezse None (fallback)
    _stub_probe("image/jpeg")
    vision.describe_image = lambda url, user_hint="": None
    try:
        text, kind = main._resolve_message("https://cdn.example.com/bozuk.jpg")
        check(text is None and kind == "image", "görsel betimlenemedi -> None")
    finally:
        vision.describe_image = orig_describe

    # (c) Ses → transcribe çağrılır
    _stub_probe("audio/mp4")
    transcribe_calls = []
    orig_tr = main._transcribe_audio
    main._transcribe_audio = lambda url: (transcribe_calls.append(url), "İki kişilik oda fiyatı nedir")[1]
    try:
        text, kind = main._resolve_message("https://lookaside.fbsbx.com/ses.mp4")
        check(kind == "audio" and len(transcribe_calls) == 1, "ses -> transcribe çağrıldı")
        check(text == "İki kişilik oda fiyatı nedir", "ses -> metne çevrildi")
    finally:
        main._transcribe_audio = orig_tr

    # Ses çözülemezse None
    _stub_probe("audio/mp4")
    main._transcribe_audio = lambda url: None
    try:
        text, kind = main._resolve_message("https://lookaside.fbsbx.com/bozuk.mp4")
        check(text is None and kind == "audio", "ses çözülemedi -> None")
    finally:
        main._transcribe_audio = orig_tr

    # (d) Metin → aynen
    text, kind = main._resolve_message("kahvaltı dahil mi")
    check(text == "kahvaltı dahil mi" and kind == "text", "metin -> aynen geçer")


# --------------------------------------------------------------------------- #
# (e) burst -> TEK agent.respond + TEK deliver                                #
# --------------------------------------------------------------------------- #
def test_burst_single_response():
    print("\n[e] 3 mesajlık burst -> TEK agent + TEK deliver")

    import agent
    import manychat
    import memory

    respond_calls = []
    deliver_calls = []
    saved = []

    orig_respond = agent.respond
    orig_deliver = manychat.deliver_answer
    orig_load = memory.load
    orig_save = memory.save

    def fake_respond(combined, history):
        respond_calls.append(combined)
        return {"text": "Hoş geldiniz, nasıl yardımcı olabilirim?", "link": None}

    def fake_deliver(uid, plat, msg, link=None):
        deliver_calls.append((uid, msg, link))
        return True

    agent.respond = fake_respond
    manychat.deliver_answer = fake_deliver
    memory.load = lambda uid: []
    memory.save = lambda uid, plat, role, content: saved.append((role, content))

    # Tüm 3 mesaj düz metin (probe çağrılsa bile text döner)
    _stub_probe(None)

    try:
        # FastAPI BackgroundTasks yerine: enqueue'ye senkron başlatıcı ver.
        # İlk enqueue worker'ı thread'de başlatır; sonraki ikisi kuyruğa eklenir.
        import threading
        threads = []

        def bg_add(fn, *args):
            t = threading.Thread(target=fn, args=args)
            t.start()
            threads.append(t)

        uid = "test-user-e"
        coalesce.enqueue(uid, "Instagram", "merhaba", main._process_batch, bg_add)
        coalesce.enqueue(uid, "Instagram", "fiyat öğrenebilir miyim", main._process_batch, bg_add)
        coalesce.enqueue(uid, "Instagram", "2 yetişkin 20 ağustos", main._process_batch, bg_add)

        # Pencere (200+100ms) + işleme bitsin
        for t in threads:
            t.join(timeout=5)
        time.sleep(0.3)

        check(len(respond_calls) == 1, f"TEK agent.respond (gerçek={len(respond_calls)})")
        check(len(deliver_calls) == 1, f"TEK deliver_answer (gerçek={len(deliver_calls)})")
        if respond_calls:
            combined = respond_calls[0]
            check("merhaba" in combined and "fiyat" in combined and "ağustos" in combined,
                  "3 mesaj birleştirildi")
        # user (birleşik) + assistant kaydı
        roles = [r for r, _ in saved]
        check(roles.count("assistant") == 1, "TEK assistant kaydı (teslim olunca)")
    finally:
        agent.respond = orig_respond
        manychat.deliver_answer = orig_deliver
        memory.load = orig_load
        memory.save = orig_save


# --------------------------------------------------------------------------- #
# (f) coalesce timing — kısa pencere ile artçı toplama                        #
# --------------------------------------------------------------------------- #
def test_coalesce_timing():
    print("\n[f] coalesce timing — artçı pencere içinde gelen mesaj toplanır")

    import agent
    import manychat
    import memory

    respond_calls = []
    orig_respond = agent.respond
    orig_deliver = manychat.deliver_answer
    orig_load = memory.load
    orig_save = memory.save

    agent.respond = lambda combined, history: (respond_calls.append(combined),
                                               {"text": "ok", "link": None})[1]
    manychat.deliver_answer = lambda uid, plat, msg, link=None: True
    memory.load = lambda uid: []
    memory.save = lambda uid, plat, role, content: None
    _stub_probe(None)

    try:
        import threading
        threads = []

        def bg_add(fn, *args):
            t = threading.Thread(target=fn, args=args)
            t.start()
            threads.append(t)

        uid = "test-user-f"
        coalesce.enqueue(uid, "Whatsapp", "ilk mesaj", main._process_batch, bg_add)
        # İlk pencere (200ms) içinde artçı gönder
        time.sleep(0.05)
        coalesce.enqueue(uid, "Whatsapp", "artçı mesaj", main._process_batch, bg_add)

        for t in threads:
            t.join(timeout=5)
        time.sleep(0.3)

        check(len(respond_calls) == 1, f"artçı dahil TEK işleme (gerçek={len(respond_calls)})")
        if respond_calls:
            check("ilk mesaj" in respond_calls[0] and "artçı mesaj" in respond_calls[0],
                  "ilk + artçı birleşti")
    finally:
        agent.respond = orig_respond
        manychat.deliver_answer = orig_deliver
        memory.load = orig_load
        memory.save = orig_save


def main_run():
    test_classify()
    test_resolve()
    test_burst_single_response()
    test_coalesce_timing()

    print("\n" + "=" * 50)
    print(f"GEÇTI: {_PASSES}   KALDI: {len(_FAILS)}")
    if _FAILS:
        print("Başarısız:")
        for f in _FAILS:
            print(f"  - {f}")
        sys.exit(1)
    print("TÜM TESTLER GEÇTI")
    sys.exit(0)


if __name__ == "__main__":
    main_run()
