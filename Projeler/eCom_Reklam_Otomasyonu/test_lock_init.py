"""Test: UserSession.lock eager-init + ElevenLabs voice 404 fallback path.

WHY: defensive checks for the four-pack fix:
- Lock attribute exists on session right after __init__ (no lazy property)
- ElevenLabs fallback dispatch logic catches 404/voice_not_found
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.conversation_manager import UserSession


def test_session_lock_eager_init():
    """Session lock should be initialized at construction time."""
    s = UserSession(user_id=42, user_name="test")
    assert isinstance(s._lock, asyncio.Lock), f"_lock is {type(s._lock)}"
    assert s.lock is s._lock, "lock property should expose _lock"
    print("✅ UserSession.lock eager-init OK")


async def test_session_lock_acquire():
    """Session lock should acquire/release inside an event loop."""
    s = UserSession(user_id=43, user_name="test2")
    async with s.lock:
        assert s.lock.locked()
    assert not s.lock.locked()
    print("✅ UserSession.lock acquire/release OK")


def test_elevenlabs_fallback_dispatch():
    """ElevenLabs.generate_speech should dispatch fallback on 404."""
    from services.elevenlabs_service import ElevenLabsService, DEFAULT_VOICES
    import requests

    svc = ElevenLabsService(api_key="dummy")
    calls = []

    class FakeResp:
        status_code = 404
        text = '{"detail":{"status":"voice_not_found"}}'

    fake_404 = requests.HTTPError(response=FakeResp())

    def fake_call(url, payload):
        calls.append(url)
        if "/text-to-speech/" in url and DEFAULT_VOICES["Ahu"] in url:
            return b"\x00" * 200  # success on Ahu
        raise fake_404

    svc._call_tts_api = fake_call
    out = svc.generate_speech("merhaba", voice_name="Adam")
    assert out == b"\x00" * 200, "fallback to Ahu should succeed"
    assert len(calls) == 2, f"expected 2 calls (orig + fallback), got {len(calls)}"
    assert DEFAULT_VOICES["Ahu"] in calls[1], "second call should use Ahu voice id"
    print("✅ ElevenLabs voice 404 fallback OK")


if __name__ == "__main__":
    test_session_lock_eager_init()
    asyncio.run(test_session_lock_acquire())
    test_elevenlabs_fallback_dispatch()
    print("\n🎉 All lock + fallback tests passed")
