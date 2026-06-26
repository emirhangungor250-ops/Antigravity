from __future__ import annotations

"""
Fake Omni istemcisi — DRY_RUN
==============================
KieOmniClient ile ayni arayuz; API'ye gitmeden ffmpeg lavfi placeholder
medya uretir. State machine + sesli concat sifir maliyetle gercekten calisir.
"""

import logging
import os
import shutil
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse

from services.kie_omni import validate_omni_quota

log = logging.getLogger("FakeOmni")

FAKE_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "fake"


def _fake_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class FakeOmniClient:
    """DRY_RUN icin sahte Kie Omni istemcisi (ayni arayuz)."""

    def __init__(self):
        self._tasks: dict[str, dict] = {}

    # ─── Video / Gorsel uretimi ──────────────────────────────────────────

    def create_video(
        self,
        prompt: str,
        *,
        duration: str = "8",
        aspect_ratio: str = "9:16",
        resolution: str = "1080p",
        seed: int | None = None,
        image_urls: list[str] | None = None,
        audio_ids: list[str] | None = None,
        character_ids: list[str] | None = None,
    ) -> str:
        self._validate_quota(image_urls, audio_ids, character_ids)
        task_id = _fake_id("fake-vid")
        self._tasks[task_id] = {
            "kind": "video",
            "prompt": prompt,
            "duration": str(duration),
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "seed": seed,
            "image_urls": list(image_urls or []),
            "audio_ids": list(audio_ids or []),
            "character_ids": list(character_ids or []),
        }
        log.info(f"[DRY_RUN] Fake video gorevi: {task_id} ({duration}s, seed={seed})")
        return task_id

    def create_image(self, prompt: str, *, aspect_ratio: str = "9:16") -> str:
        task_id = _fake_id("fake-img")
        self._tasks[task_id] = {
            "kind": "image",
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
        }
        log.info(f"[DRY_RUN] Fake gorsel gorevi: {task_id} ({aspect_ratio})")
        return task_id

    # ─── Polling ─────────────────────────────────────────────────────────

    def poll_task(self, task_id: str) -> dict:
        """Placeholder medyayi uretir ve aninda success doner."""
        task = self._tasks.get(task_id)
        if task is None:
            return {"status": "failed", "error": f"Bilinmeyen fake task: {task_id}"}

        # Runtime import: ffmpeg_assembler baska modulde, sadece poll'da gerekir
        from services.ffmpeg_assembler import make_placeholder_clip, make_placeholder_image

        FAKE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        label = task.get("prompt", "")[:40]

        if task["kind"] == "video":
            dest = FAKE_OUTPUT_DIR / f"{task_id}.mp4"
            make_placeholder_clip(
                str(dest),
                duration=int(task["duration"]),
                with_audio=True,
                label=label,
            )
        else:
            dest = FAKE_OUTPUT_DIR / f"{task_id}.png"
            make_placeholder_image(str(dest), text=label)

        url = f"file://{dest}"
        log.info(f"[DRY_RUN] Fake gorev tamamlandi: {task_id} → {url}")
        return {"status": "success", "urls": [url], "result": {"resultUrls": [url]}}

    # ─── Ses kimligi + karakter ──────────────────────────────────────────

    def create_audio_persona(
        self,
        preset_audio_id: str,
        name: str,
        voice_description: str,
        example_dialogue: str,
    ) -> str:
        kie_audio_id = uuid.uuid4().hex
        log.info(f"[DRY_RUN] Fake ses kimligi: {name} ({preset_audio_id}) → {kie_audio_id}")
        return kie_audio_id

    def create_character(
        self,
        description: str,
        image_url: str,
        audio_ids: list[str],
        character_name: str,
    ) -> dict:
        character_id = uuid.uuid4().hex
        log.info(f"[DRY_RUN] Fake karakter: {character_name} → {character_id}")
        return {"characterId": character_id, "imageUrl": image_url}

    # ─── Dosya islemleri ─────────────────────────────────────────────────

    def upload_file_from_url(self, file_url: str, file_name: str | None = None) -> str:
        log.info(f"[DRY_RUN] Fake upload (passthrough): {file_url[:80]}")
        return file_url

    def download_file(self, url: str, dest_path: str) -> str:
        dest_path = str(dest_path)
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)

        parsed = urlparse(url)
        if parsed.scheme == "file":
            shutil.copyfile(unquote(parsed.path), dest_path)
            log.info(f"[DRY_RUN] Lokal dosya kopyalandi: {dest_path}")
            return dest_path

        import requests
        with requests.get(url, stream=True, timeout=(30, 300)) as response:
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        return dest_path

    # ─── Kredi ───────────────────────────────────────────────────────────

    def get_credit_balance(self) -> None:
        return None

    # ─── Internal ────────────────────────────────────────────────────────

    def _validate_quota(self, image_urls=None, audio_ids=None, character_ids=None) -> None:
        validate_omni_quota(image_urls, audio_ids, character_ids)
