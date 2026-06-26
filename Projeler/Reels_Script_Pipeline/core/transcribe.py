"""HappyScribe transcription — upload + polling + text export."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from core.config import Config

POLL_INTERVAL = 5
POLL_TIMEOUT = 600


@dataclass
class Transcript:
    id: str
    state: str
    text: str
    language: str
    duration_sec: float | None


def _auth(cfg: Config) -> dict:
    return {"Authorization": f"Bearer {cfg.happyscribe_api_key}"}


def create_transcription(cfg: Config, name: str, public_url: str, language: str = "en-US") -> str:
    body = {
        "transcription": {
            "name": name,
            "language": language,
            "tmp_url": public_url,
            "is_subtitle": False,
            "service": "auto",
            "organization_id": cfg.happyscribe_org_id,
        }
    }
    if cfg.happyscribe_glossary_id:
        body["transcription"]["glossary_ids"] = [int(cfg.happyscribe_glossary_id)]
    r = httpx.post(
        "https://www.happyscribe.com/api/v1/transcriptions",
        headers={**_auth(cfg), "Content-Type": "application/json"},
        json=body,
        timeout=30,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"HappyScribe create HTTP {r.status_code}: {r.text[:300]}")
    return r.json()["id"]


def get_transcription(cfg: Config, tid: str) -> dict:
    r = httpx.get(
        f"https://www.happyscribe.com/api/v1/transcriptions/{tid}",
        headers=_auth(cfg),
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def wait_until_done(cfg: Config, tid: str, on_tick=None) -> dict:
    start = time.time()
    while True:
        info = get_transcription(cfg, tid)
        state = info.get("state")
        if on_tick:
            on_tick(state, int(time.time() - start))
        if state in {"automatic_done", "done", "exported"}:
            return info
        if state in {"failed", "error"}:
            raise RuntimeError(f"HappyScribe state={state}: {info}")
        if time.time() - start > POLL_TIMEOUT:
            raise TimeoutError(f"HappyScribe polling > {POLL_TIMEOUT}s, state={state}")
        time.sleep(POLL_INTERVAL)


def export_text(cfg: Config, tid: str) -> str:
    """Transcript metnini düz text olarak çek."""
    r = httpx.post(
        "https://www.happyscribe.com/api/v1/exports",
        headers={**_auth(cfg), "Content-Type": "application/json"},
        json={
            "export": {
                "format": "txt",
                "transcription_ids": [tid],
            }
        },
        timeout=30,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"HappyScribe export create HTTP {r.status_code}: {r.text[:300]}")
    export_id = r.json()["id"]
    # poll export
    deadline = time.time() + 120
    while time.time() < deadline:
        rr = httpx.get(
            f"https://www.happyscribe.com/api/v1/exports/{export_id}",
            headers=_auth(cfg),
            timeout=15,
        )
        rr.raise_for_status()
        data = rr.json()
        if data.get("state") in {"ready", "done"} and data.get("download_link"):
            content = httpx.get(data["download_link"], timeout=30, follow_redirects=True).text
            return content.strip()
        if data.get("state") in {"failed", "error"}:
            raise RuntimeError(f"Export failed: {data}")
        time.sleep(2)
    raise TimeoutError("Export polling timeout")


def transcribe(cfg: Config, public_url: str, name: str, language: str = "en-US",
               on_tick=None) -> Transcript:
    tid = create_transcription(cfg, name, public_url, language)
    info = wait_until_done(cfg, tid, on_tick=on_tick)
    text = export_text(cfg, tid)
    return Transcript(
        id=tid,
        state=info.get("state", "?"),
        text=text,
        language=info.get("language", language),
        duration_sec=info.get("duration"),
    )


if __name__ == "__main__":
    import sys
    cfg = Config.from_env()
    url = sys.argv[1]
    print(f"🎤 HappyScribe transcribing: {url}")
    t = transcribe(cfg, url, name="probe-cli",
                   on_tick=lambda s, e: print(f"   [{e:>3}s] state={s}"))
    print(f"\n✅ {len(t.text)} char")
    print(f"--- ilk 400 char ---\n{t.text[:400]}")
