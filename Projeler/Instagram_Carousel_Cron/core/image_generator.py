"""Kie AI image generator — text-free arka plan üretimi.

Twitter_Text_Paylasim/core/image_generator.py adapt edildi:
  - Aspect ratio: 3:4 (Kie native), Pillow ile 1080x1350'a normalize
  - Negative prompt: text/letters/numbers/logos
  - Polling: 6dk timeout
  - Model env switchable (default nano-banana-2; gpt-image-2-text-to-image düzelirse override)
"""

import os
import json
import time
import tempfile
from typing import Optional

import requests

from config import settings
from ops_logger import get_ops_logger

ops = get_ops_logger("IG_Carousel_Cron", "ImageGen")

KIE_BASE = "https://api.kie.ai/api/v1"


class KieImageGenerator:
    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.KIE_MODEL
        self.headers = {
            "Authorization": f"Bearer {settings.KIE_API_KEY}",
            "Content-Type": "application/json",
        }

    def generate(self, prompt: str, aspect_ratio: str = "3:4") -> tuple[str, str]:
        """Prompt'tan görsel üret. Returns (local_path, kie_url) or ('', '')."""
        if settings.IS_DRY_RUN:
            ops.info("[DRY-RUN] Kie generate atlandı", message=prompt[:120])
            return ("", "")

        kie_url = self._create_and_poll(prompt, aspect_ratio)
        if not kie_url:
            return ("", "")
        local_path = self._download(kie_url)
        return (local_path, kie_url)

    def _create_and_poll(self, prompt: str, aspect_ratio: str) -> str:
        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
            },
        }
        try:
            r = requests.post(
                f"{KIE_BASE}/jobs/createTask",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            task_id = (data.get("data") or {}).get("taskId")
            if not task_id:
                ops.error("Kie taskId yok", message=str(data)[:300])
                return ""
            ops.info(f"Kie task: {task_id}", message=f"model={self.model}")
        except Exception as e:
            ops.error("Kie createTask exception", exception=e)
            return ""

        # Polling
        poll_url = f"{KIE_BASE}/jobs/recordInfo"
        for i in range(72):  # 6 dk
            time.sleep(5)
            try:
                pr = requests.get(
                    poll_url,
                    headers=self.headers,
                    params={"taskId": task_id},
                    timeout=15,
                )
                pr.raise_for_status()
                pd = pr.json()
                d = pd.get("data") or {}
                state = (d.get("state") or "").lower()

                if state in ("success", "completed", "succeeded"):
                    result = d.get("resultJson") or d.get("result") or {}
                    if isinstance(result, str):
                        try:
                            result = json.loads(result)
                        except Exception:
                            result = {}
                    urls = result.get("resultUrls") or result.get("urls") or []
                    if urls and isinstance(urls, list):
                        ops.info(f"Kie URL: {urls[0][:80]}…")
                        return urls[0]
                    ops.error("Kie OK ama URL yok", message=str(pd)[:300])
                    return ""

                if state in ("failed", "error"):
                    fail_msg = d.get("failMsg") or d.get("errorMsg") or "?"
                    fail_code = d.get("failCode") or "?"
                    ops.error(f"Kie task FAILED [{fail_code}]", message=str(fail_msg)[:300])
                    return ""
                # processing / wait / waiting / generating → continue
            except Exception as e:
                ops.warning(f"Kie polling hatası", details=str(e)[:200])

        ops.error("Kie polling timeout (6dk)")
        return ""

    def _download(self, url: str) -> str:
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            fd, path = tempfile.mkstemp(suffix=".png", prefix="carousel_scene_")
            with os.fdopen(fd, "wb") as f:
                f.write(r.content)
            ops.info(f"Sahne indirildi: {path} ({len(r.content)//1024}KB)")
            return path
        except Exception as e:
            ops.error("Sahne indirme exception", exception=e)
            return ""


# Module-level facade — main.py ve sibling core modülleri (vision_reviewer,
# carousel_planner, caption_writer, imgbb_uploader) modül-seviyesi fonksiyon
# çağırıyor. Tek bir KieImageGenerator instance'ı lazy oluşturulur.
_generator: Optional[KieImageGenerator] = None


def generate(prompt: str, aspect_ratio: str = "3:4") -> tuple[str, str]:
    """Modül-seviyesi generate facade'ı. Returns (local_path, kie_url)."""
    global _generator
    if _generator is None:
        _generator = KieImageGenerator()
    return _generator.generate(prompt, aspect_ratio)
