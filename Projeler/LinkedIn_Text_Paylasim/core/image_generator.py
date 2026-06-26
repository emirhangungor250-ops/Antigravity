"""
Görsel promptu (GPT-4.1-mini) ve Görsel Üretimi (Kie AI).
n8n'deki "Görsel Prompt", "HTTP Request (Kie AI)" ve "Download Image" node'ları.
"""
from ops_logger import get_ops_logger
ops = get_ops_logger("LinkedIn_Text_Paylasim", "ImageGenerator")
import os
import requests
import tempfile
import time
from openai import OpenAI

from config import settings


class ImageGenerator:
    """Metinden görsel promptu çıkarır ve Kie AI ile görsel üretir."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_post_image(self, post_text: str) -> str:
        """
        1. GPT-4.1-mini ile görsel promptu üretir.
        2. Kie AI API'sine istek atar.
        3. Üretilen görseli temp klasörüne indirir.
        
        Returns:
            İndirilen görselin lokal dosya yolu.
        """
        if settings.IS_DRY_RUN:
            ops.info("[DRY-RUN] Görsel prompt üretme atlanıyor.")
            ops.info("[DRY-RUN] Kie AI görsel üretme atlanıyor.")
            return None

        # Step 1: Prompt Üretimi (GPT-4o-mini)
        prompt = self._generate_image_prompt(post_text)

        # Step 2 & 3: Kie AI ile Üret ve İndir
        image_path = self._generate_and_download_from_kie(prompt)
        return image_path

    def _generate_image_prompt(self, post_text: str) -> str:
        """Post metninden İngilizce görsel promptu çıkarır."""
        system_message = (
            "You are an expert AI image prompt engineer. Your job is to read the "
            "following LinkedIn post and create a highly detailed, descriptive, "
            "and compelling image generation prompt in English that perfectly "
            "captures the essence of the post. The image should be professional, "
            "modern, and visually engaging, suitable for a LinkedIn audience."
        )

        user_message = (
            f"Here is the LinkedIn post:\n\n{post_text}\n\n"
            "Create a vivid image generation prompt based on this post. "
            "Output ONLY the prompt text, nothing else."
        )

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7
            )
            prompt = response.choices[0].message.content.strip()
            ops.info(f"Görsel promptu üretildi ({len(prompt)} karakter)")
            return prompt
        except Exception as e:
            ops.error(f"Görsel prompt üretme hatası: {e}", exception=e)
            raise

    def _generate_and_download_from_kie(self, prompt: str) -> str:
        """Kie AI'a task gönder (jobs/createTask), recordInfo ile polling, indir.
        16:9 LinkedIn formatı. Twitter projesindeki çalışan pattern'in kopyası.
        """
        KIE_BASE = "https://api.kie.ai/api/v1"
        headers = {
            "Authorization": f"Bearer {settings.KIE_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "nano-banana-2",
            "input": {
                "prompt": prompt,
                "aspect_ratio": "16:9",
            },
        }
        try:
            r = requests.post(f"{KIE_BASE}/jobs/createTask", headers=headers,
                              json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            task_id = (data.get("data") or {}).get("taskId")
            if not task_id:
                ops.error("Kie AI taskId yok", message=str(data)[:300])
                raise Exception("Kie API yanıtında taskId yok")
            ops.info(f"Kie AI task: {task_id}")
        except Exception as e:
            ops.error("Kie AI createTask hatası", exception=e)
            raise

        poll_url = f"{KIE_BASE}/jobs/recordInfo"
        for i in range(72):  # ~6 dk
            time.sleep(5)
            try:
                pr = requests.get(poll_url, headers=headers,
                                  params={"taskId": task_id}, timeout=15)
                pr.raise_for_status()
                pd = pr.json()
                d = pd.get("data") or {}
                state = (d.get("state") or "").lower()
                if state in ("success", "completed", "succeeded"):
                    result = d.get("resultJson") or d.get("result") or {}
                    if isinstance(result, str):
                        import json as _json
                        try:
                            result = _json.loads(result)
                        except Exception:
                            result = {}
                    urls = result.get("resultUrls") or result.get("urls") or []
                    if urls and isinstance(urls, list):
                        image_url = urls[0]
                        ops.info(f"Görsel URL hazır: {image_url[:80]}…")
                        img_response = requests.get(image_url, timeout=30)
                        img_response.raise_for_status()
                        fd, temp_path = tempfile.mkstemp(suffix=".png")
                        with os.fdopen(fd, "wb") as f:
                            f.write(img_response.content)
                        ops.info(f"Görsel indirildi: {temp_path}")
                        return temp_path
                    ops.error("Kie AI tamam ama URL yok", message=str(pd)[:300])
                    raise Exception("Kie AI: URL bulunamadı")
                if state in ("failed", "error"):
                    msg = d.get("failMsg") or d.get("errorMsg", "?")
                    ops.error(f"Kie AI task FAILED: {msg}")
                    raise Exception(f"Kie AI Task Failed: {msg}")
            except requests.HTTPError as e:
                ops.warning(f"Kie polling HTTP hatası: {e}")
        raise Exception("Kie AI polling zaman aşımı (6dk)")
