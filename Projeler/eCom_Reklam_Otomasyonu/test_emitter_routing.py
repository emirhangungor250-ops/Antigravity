"""
Emitter / dashboard substage routing testi — main.py `_run_production`.

E2E pipeline harness'ı `pipeline.produce()`'u doğrudan çağırdığı için
main.py'daki dashboard emitter mantığına HİÇ dokunmaz. Bu test o boşluğu
kapatır: GERÇEK `_run_production` fonksiyonunu sahte emitter + sahte
pipeline ile çalıştırıp 2026-05-14 stabilizasyon fix'lerini doğrular.

Kapsanan bug'lar (commit 3b61e57):
  #1 retry_no_ref / retry_safety SCENE_RETRY_STEPS'te — kapalı assets
     substage'ini yeniden AÇMAMALI, scenes substage'ine yönlenmeli.
  #2 CancelledError + Exception path'leri açık substage'leri + produce
     stage'ini + run'ı fail olarak temizlemeli (eskiden "active" donuyordu).

API çağrısı yok, maliyet ~sıfır.

Kullanım:
    set -a; source .env; set +a
    .venv313/bin/python test_emitter_routing.py
"""
from __future__ import annotations

import asyncio
import sys
import traceback

import main


# ─────────────────────────────────────────────────────────
# Sahte altyapı
# ─────────────────────────────────────────────────────────
class RecordingEmitter:
    """run_emitter yerine geçer — her çağrıyı (method, args, kwargs) kaydeder."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def _rec(self, name: str):
        def _fn(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            if name == "start_run":
                return "test-run-id"
            return None
        return _fn

    def __getattr__(self, name: str):
        return self._rec(name)

    # ── sorgu yardımcıları ──
    def count(self, method: str, *match_args) -> int:
        n = 0
        for m, a, _ in self.calls:
            if m != method:
                continue
            if match_args and a[: len(match_args)] != match_args:
                continue
            n += 1
        return n

    def methods(self) -> list[str]:
        return [m for m, _, _ in self.calls]

    def index_of(self, method: str, *match_args) -> int:
        for i, (m, a, _) in enumerate(self.calls):
            if m == method and (not match_args or a[: len(match_args)] == match_args):
                return i
        return -1


class FakeMessage:
    def __init__(self) -> None:
        self.replies: list[str] = []

    async def reply_text(self, text, *a, **kw):
        self.replies.append(text)

    async def reply_video(self, *a, **kw):
        pass


class FakeSession:
    def __init__(self) -> None:
        self.scenario = {"scenes": [{}]}  # truthy — _run_production erken çıkmaz
        self.collected_data = {"brand_name": "TestBrand", "product_name": "TestÜrün"}
        self.user_name = "routing-tester"
        self.preferences = {}
        self.production_task = None
        self.reset_called = 0

    def reset(self) -> None:
        self.reset_called += 1


class FakeConversationMgr:
    def __init__(self, session: FakeSession) -> None:
        self._session = session

    def get_session(self, user_id):
        return self._session


class FakeChatTracker:
    async def log_interaction(self, *a, **kw):
        pass


def _make_produce(steps: list[tuple[str, str]], outcome: str):
    """
    Sahte pipeline.produce — verilen step dizisini progress_callback'e basar,
    sonra `outcome`'a göre döner/raise eder.

    outcome:
      "failed"    → {"status": "failed", "error": ...}
      "cancel"    → asyncio.CancelledError raise
      "exception" → RuntimeError raise
    """
    async def _produce(*, scenario, collected_data, progress_callback,
                        user_name, preferences):
        for step, msg in steps:
            await progress_callback(step, msg)
        if outcome == "cancel":
            raise asyncio.CancelledError()
        if outcome == "exception":
            raise RuntimeError("e2e-routing-test crash")
        return {"status": "failed", "error": "e2e-routing-test failed-branch"}

    return _produce


# ─────────────────────────────────────────────────────────
# Test koşucusu
# ─────────────────────────────────────────────────────────
async def _run_case(steps, outcome) -> tuple[RecordingEmitter, FakeSession, FakeMessage, BaseException | None]:
    emitter = RecordingEmitter()
    session = FakeSession()
    message = FakeMessage()

    orig_emitter = main.run_emitter
    orig_mgr = main.conversation_mgr
    orig_pipeline = main.pipeline
    orig_tracker = main.chat_tracker

    main.run_emitter = emitter
    main.conversation_mgr = FakeConversationMgr(session)
    main.pipeline = type("P", (), {"produce": staticmethod(_make_produce(steps, outcome))})()
    main.chat_tracker = FakeChatTracker()

    raised: BaseException | None = None
    try:
        await main._run_production(message, user_id=12345)
    except BaseException as e:  # noqa: BLE001 — CancelledError dahil yakala
        raised = e
    finally:
        main.run_emitter = orig_emitter
        main.conversation_mgr = orig_mgr
        main.pipeline = orig_pipeline
        main.chat_tracker = orig_tracker

    return emitter, session, message, raised


def _check(name: str, cond: bool, detail: str = "") -> bool:
    mark = "✅" if cond else "❌"
    print(f"  {mark} {name}" + (f" — {detail}" if detail and not cond else ""))
    return cond


async def test_bug1_retry_routing() -> bool:
    """retry_no_ref kapalı assets'i yeniden açmamalı, scenes'e yönelmeli."""
    print("\n[BUG #1] retry_no_ref / retry_safety routing")
    steps = [
        ("step_voiceover", "Dış ses üretiliyor"),       # → assets açılır
        ("step_character", "Karakter görseli"),          # assets açık kalır
        ("step_1", "Video render başladı"),              # assets kapanır, scenes açılır
        ("retry_no_ref", "Referans görsel reddedildi"),  # → scenes (assets'i AÇMAMALI)
        ("retry_safety", "Güvenlik filtresi"),           # → scenes
    ]
    em, _, _, raised = await _run_case(steps, "failed")

    ok = True
    ok &= _check("assets substage 1 kez açıldı",
                 em.count("start_substage", "produce", "assets") == 1,
                 f"got {em.count('start_substage', 'produce', 'assets')}")
    ok &= _check("scenes substage 1 kez açıldı (yeniden açılmadı)",
                 em.count("start_substage", "produce", "scenes") == 1,
                 f"got {em.count('start_substage', 'produce', 'scenes')}")
    ok &= _check("step_1 assets'i kapattı",
                 em.count("end_substage", "produce", "assets") == 1,
                 f"got {em.count('end_substage', 'produce', 'assets')}")

    # Kritik: retry_no_ref'ten SONRA assets yeniden açılmamalı.
    # assets'in son start index'i, scenes'in start index'inden önce olmalı
    # ve assets sadece 1 kez açıldığı için bu zaten yeterli — ama sıralamayı da doğrula.
    assets_starts = [i for i, (m, a, _) in enumerate(em.calls)
                     if m == "start_substage" and a[:2] == ("produce", "assets")]
    scenes_start = em.index_of("start_substage", "produce", "scenes")
    ok &= _check("assets retry adımlarından sonra yeniden açılmadı",
                 len(assets_starts) == 1 and assets_starts[0] < scenes_start,
                 f"assets_starts={assets_starts} scenes_start={scenes_start}")
    ok &= _check("failed branch: produce fail edildi",
                 em.count("fail_stage", "produce") == 1)
    ok &= _check("failed branch: run fail edildi",
                 em.count("fail_run") == 1)
    ok &= _check("exception propagate olmadı",
                 raised is None, f"raised={raised!r}")
    return ok


async def test_bug2_cancel_cleanup() -> bool:
    """CancelledError açık substage + produce + run'ı temizlemeli, re-raise etmeli."""
    print("\n[BUG #2a] CancelledError cleanup")
    steps = [("step_voiceover", "Dış ses üretiliyor")]  # assets açık kalır
    em, session, _, raised = await _run_case(steps, "cancel")

    ok = True
    ok &= _check("açık assets substage fail edildi",
                 em.count("fail_substage", "produce", "assets") == 1,
                 f"got {em.count('fail_substage', 'produce', 'assets')}")
    ok &= _check("produce stage fail edildi",
                 em.count("fail_stage", "produce") == 1)
    ok &= _check("run fail edildi",
                 em.count("fail_run") == 1)
    ok &= _check("CancelledError re-raise edildi",
                 isinstance(raised, asyncio.CancelledError),
                 f"raised={raised!r}")
    return ok


async def test_bug2_exception_cleanup() -> bool:
    """Beklenmeyen Exception açık substage + produce + run'ı temizlemeli, yutmalı."""
    print("\n[BUG #2b] Exception cleanup")
    steps = [("step_1", "Video render başladı")]  # scenes açık kalır
    em, session, message, raised = await _run_case(steps, "exception")

    ok = True
    ok &= _check("açık scenes substage fail edildi",
                 em.count("fail_substage", "produce", "scenes") == 1,
                 f"got {em.count('fail_substage', 'produce', 'scenes')}")
    ok &= _check("produce stage fail edildi",
                 em.count("fail_stage", "produce") == 1)
    ok &= _check("run fail edildi",
                 em.count("fail_run") == 1)
    ok &= _check("exception yutuldu (propagate olmadı)",
                 raised is None, f"raised={raised!r}")
    ok &= _check("session reset edildi",
                 session.reset_called >= 1, f"reset_called={session.reset_called}")
    ok &= _check("kullanıcıya kritik hata mesajı gitti",
                 any("Kritik hata" in r for r in message.replies),
                 f"replies={message.replies}")
    return ok


async def main_runner() -> int:
    print("=" * 60)
    print("  EMITTER ROUTING TEST — main.py _run_production")
    print("=" * 60)
    results = []
    for fn in (test_bug1_retry_routing,
               test_bug2_cancel_cleanup,
               test_bug2_exception_cleanup):
        try:
            results.append(await fn())
        except Exception:
            print(f"  ❌ {fn.__name__} — test harness çöktü:")
            traceback.print_exc()
            results.append(False)

    passed = sum(results)
    total = len(results)
    print("\n" + "=" * 60)
    print(f"  SONUÇ: {passed}/{total} test grubu geçti")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main_runner()))
