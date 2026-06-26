from __future__ import annotations

"""
Kie AI Gemini Omni istemcisi
=============================
Video (gemini-omni-video), gorsel (nano-banana-2), ses kimligi ve karakter
olusturma. Asenkron gorev modeli: createTask → polling → resultUrls.
"""

import json
import logging
import os
import shutil
import time
from urllib.parse import unquote, urlparse

import requests

from core.retry import retry_api_call

log = logging.getLogger("KieOmni")

# Polling: ilk 60sn 20sn aralik, sonra 12sn; maks 150 deneme (~30dk)
POLL_INTERVAL_EARLY = 20
POLL_INTERVAL_LATE = 12
POLL_EARLY_WINDOW = 60
MAX_POLL_ATTEMPTS = 150
REQUEST_TIMEOUT = 30

FILE_UPLOAD_BASE_URL = "https://kieai.redpandaai.co"

# Gemini Omni gorev kotasi: gorsel=1 birim, karakter=1 birim, toplam ≤7
MAX_QUOTA_UNITS = 7
MAX_IMAGE_URLS = 7
MAX_AUDIO_IDS = 3
MAX_CHARACTER_IDS = 3

_TERMINAL_FAIL_STATES = ("failed", "fail")
_TERMINAL_SUCCESS_STATES = ("success", "completed")


def validate_omni_quota(image_urls=None, audio_ids=None, character_ids=None) -> None:
    """Submit oncesi Gemini Omni kota/limit kontrolu. Ihlalde ValueError."""
    image_urls = image_urls or []
    audio_ids = audio_ids or []
    character_ids = character_ids or []

    if len(image_urls) > MAX_IMAGE_URLS:
        raise ValueError(f"image_urls limiti asildi: {len(image_urls)} > {MAX_IMAGE_URLS}")
    if len(audio_ids) > MAX_AUDIO_IDS:
        raise ValueError(f"audio_ids limiti asildi: {len(audio_ids)} > {MAX_AUDIO_IDS}")
    if len(character_ids) > MAX_CHARACTER_IDS:
        raise ValueError(f"character_ids limiti asildi: {len(character_ids)} > {MAX_CHARACTER_IDS}")

    total_units = len(image_urls) + len(character_ids)
    if total_units > MAX_QUOTA_UNITS:
        raise ValueError(
            f"Gorev kotasi asildi: {len(image_urls)} gorsel + "
            f"{len(character_ids)} karakter = {total_units} birim > {MAX_QUOTA_UNITS}"
        )


def _extract_field(payload, *keys):
    """Yanit govdesinde (root + data + parsed result) alan arar."""
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if payload.get(key):
            return payload[key]
    inner = payload.get("data")
    if isinstance(inner, dict):
        for key in keys:
            if inner.get(key):
                return inner[key]
    return None


class KieOmniClient:
    """Kie AI Gemini Omni API istemcisi."""

    def __init__(self, api_key: str, base_url: str = "https://api.kie.ai/api/v1/"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

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
        """Gemini Omni video gorevi olusturur, taskId doner."""
        self._validate_quota(image_urls, audio_ids, character_ids)

        input_data: dict = {
            "prompt": prompt,
            "duration": str(duration),  # API string bekler: '4'|'6'|'8'|'10'
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }
        if seed is not None:
            input_data["seed"] = int(seed)
        if image_urls:
            input_data["image_urls"] = list(image_urls)
        if audio_ids:
            input_data["audio_ids"] = list(audio_ids)
        if character_ids:
            input_data["character_ids"] = list(character_ids)

        payload = {"model": "gemini-omni-video", "input": input_data}
        task_id = self._create_task(payload)
        log.info(
            f"Omni video gorevi olusturuldu: {task_id} "
            f"({duration}s, {aspect_ratio}, {resolution}, "
            f"img={len(image_urls or [])}, aud={len(audio_ids or [])}, "
            f"chr={len(character_ids or [])}, seed={seed})"
        )
        return task_id

    def create_image(self, prompt: str, *, aspect_ratio: str = "9:16") -> str:
        """Nano Banana 2 gorsel gorevi olusturur, taskId doner."""
        payload = {
            "model": "nano-banana-2",
            "input": {"prompt": prompt, "aspect_ratio": aspect_ratio},
        }
        task_id = self._create_task(payload)
        log.info(f"Nano Banana 2 gorsel gorevi olusturuldu: {task_id} ({aspect_ratio})")
        return task_id

    # ─── Polling ─────────────────────────────────────────────────────────

    def poll_task(self, task_id: str) -> dict:
        """
        Gorev bitene kadar poll'lar.

        Returns:
            {"status": "success", "urls": [...], "result": {...}} |
            {"status": "failed", "error": "..."} |
            {"status": "timeout"}  (sahne submitted kalir, --devam yeniden poll'lar)

        Raises:
            RuntimeError: HTTP/wrapper 401/403/404 — kalici hata, aninda kesilir.
        """
        url = f"{self.base_url}/jobs/recordInfo"
        start_time = time.monotonic()
        prev_state: str | None = None

        for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
            try:
                response = requests.get(
                    url,
                    params={"taskId": task_id},
                    headers=self.headers,
                    timeout=REQUEST_TIMEOUT,
                )

                # Kalici auth/not-found → bosa polling yapma, aninda kes
                if response.status_code in (401, 403, 404):
                    raise RuntimeError(
                        f"permanent: HTTP {response.status_code} polling — "
                        f"task={task_id}, body={response.text[:200]}"
                    )

                response.raise_for_status()
                data = response.json()

                # Wrapper error kontrolu (200 OK + JSON icinde hata kodu)
                code = data.get("code")
                if code is not None and str(code) not in ("200", "0"):
                    code_int = int(code) if str(code).isdigit() else 0
                    if code_int in (401, 403, 404):
                        raise RuntimeError(
                            f"permanent: wrapper code={code} — "
                            f"{data.get('msg', 'Bilinmeyen hata')}"
                        )
                    raise ValueError(
                        f"Polling wrapper hatasi (code={code}): "
                        f"{data.get('msg', 'Bilinmeyen hata')}"
                    )

                record = data.get("data") or {}
                state = str(record.get("state", "unknown")).lower()

                if state in _TERMINAL_SUCCESS_STATES:
                    result_json = record.get("resultJson", "{}")
                    parsed = (
                        json.loads(result_json)
                        if isinstance(result_json, str)
                        else (result_json or {})
                    )
                    urls = parsed.get("resultUrls", [])
                    log.info(
                        f"Gorev tamamlandi: {task_id} — {len(urls)} cikti, "
                        f"{attempt} poll denemesi"
                    )
                    return {"status": "success", "urls": urls, "result": parsed}

                if state in _TERMINAL_FAIL_STATES:
                    fail_msg = record.get("failMsg") or record.get("failureMessage") or "Bilinmeyen hata"
                    log.error(f"Gorev basarisiz: {task_id} — {fail_msg}")
                    return {"status": "failed", "error": fail_msg}

                # pending / processing / waiting / queuing → bekle
                if state != prev_state:
                    log.info(
                        f"Polling {task_id}: state {prev_state}→{state} "
                        f"(attempt {attempt}/{MAX_POLL_ATTEMPTS})"
                    )
                    prev_state = state

            except RuntimeError as e:
                if str(e).startswith("permanent:"):
                    log.error(f"Polling kalici hata, kesiliyor: {task_id} — {e}")
                    raise
                log.error(f"Polling hatasi ({attempt}): {task_id}", exc_info=True)
            except Exception:
                log.error(f"Polling hatasi ({attempt}): {task_id}", exc_info=True)

            elapsed = time.monotonic() - start_time
            interval = POLL_INTERVAL_EARLY if elapsed < POLL_EARLY_WINDOW else POLL_INTERVAL_LATE
            time.sleep(interval)

        log.error(f"Polling timeout: {task_id} — {MAX_POLL_ATTEMPTS} deneme asildi")
        return {"status": "timeout"}

    # ─── Ses kimligi + karakter ──────────────────────────────────────────

    def create_audio_persona(
        self,
        preset_audio_id: str,
        name: str,
        voice_description: str,
        example_dialogue: str,
    ) -> str:
        """
        Preset sesten kalici ses kimligi olusturur, kieAudioId doner.
        Yanitta id yoksa ama taskId varsa async varsayip poll'a duser.
        """
        body = self._post_json(
            "omni/audio/create",
            {
                "audio_id": preset_audio_id,
                "name": name,
                "voice_description": voice_description,
                "example_dialogue": example_dialogue,
            },
            operation="Kie omni audio create",
        )

        kie_audio_id = _extract_field(body, "kieAudioId", "audioId")
        if kie_audio_id:
            log.info(f"Ses kimligi olusturuldu: {name} → {kie_audio_id}")
            return str(kie_audio_id)

        # Async savunmasi: taskId varsa poll'la
        task_id = _extract_field(body, "taskId")
        if task_id:
            log.info(f"Ses kimligi async gorundu, poll'a dusuluyor: task={task_id}")
            result = self.poll_task(str(task_id))
            if result.get("status") == "success":
                kie_audio_id = _extract_field(result.get("result") or {}, "kieAudioId", "audioId")
                if kie_audio_id:
                    log.info(f"Ses kimligi (poll) olusturuldu: {name} → {kie_audio_id}")
                    return str(kie_audio_id)
            raise RuntimeError(
                f"Ses kimligi poll sonucu cozulemedi: {name} — {result}"
            )

        raise ValueError(f"Ses kimligi yanitinda kieAudioId/taskId yok: {body}")

    def create_character(
        self,
        description: str,
        image_url: str,
        audio_ids: list[str],
        character_name: str,
    ) -> dict:
        """
        Gorunum + ses kimligini server-side baglayan karakter olusturur.
        Doner: {"characterId": ..., "imageUrl": ...}
        """
        body = self._post_json(
            "omni/character/create",
            {
                "description": description,
                "image_urls": [image_url],
                "audio_ids": list(audio_ids),
                "character_name": character_name,
            },
            operation="Kie omni character create",
        )

        character_id = _extract_field(body, "characterId")
        if character_id:
            result_image = _extract_field(body, "imageUrl") or image_url
            log.info(f"Karakter olusturuldu: {character_name} → {character_id}")
            return {"characterId": str(character_id), "imageUrl": result_image}

        # Async savunmasi: taskId varsa poll'la
        task_id = _extract_field(body, "taskId")
        if task_id:
            log.info(f"Karakter async gorundu, poll'a dusuluyor: task={task_id}")
            result = self.poll_task(str(task_id))
            if result.get("status") == "success":
                parsed = result.get("result") or {}
                character_id = _extract_field(parsed, "characterId")
                if character_id:
                    result_image = _extract_field(parsed, "imageUrl") or image_url
                    log.info(f"Karakter (poll) olusturuldu: {character_name} → {character_id}")
                    return {"characterId": str(character_id), "imageUrl": result_image}
            raise RuntimeError(
                f"Karakter poll sonucu cozulemedi: {character_name} — {result}"
            )

        raise ValueError(f"Karakter yanitinda characterId/taskId yok: {body}")

    # ─── Dosya islemleri ─────────────────────────────────────────────────

    @retry_api_call(max_retries=2, base_delay=2.0, operation_name="Kie AI file upload")
    def upload_file_from_url(self, file_url: str, file_name: str | None = None) -> str:
        """
        Harici URL'deki dosyayi Kie AI dosya sunucusuna yukler, downloadUrl doner.
        Endpoint: POST https://kieai.redpandaai.co/api/file-url-upload
        """
        if not file_name:
            parsed = urlparse(file_url)
            file_name = os.path.basename(parsed.path) or "uploaded_file"

        url = f"{FILE_UPLOAD_BASE_URL}/api/file-url-upload"
        # NOT: uploadPath zorunlu — eksikse 400 donuyor.
        payload = {
            "fileUrl": file_url,
            "fileName": file_name,
            "uploadPath": "images/user-uploads",
        }

        response = requests.post(url, headers=self.headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        code = data.get("code")
        if code is not None and str(code) not in ("200", "0"):
            code_int = int(code) if str(code).isdigit() else 400
            if code_int in {401, 408, 429} or (500 <= code_int <= 599):
                response.status_code = code_int
                raise requests.exceptions.HTTPError(
                    f"Upload API hatasi: {data.get('msg', 'Bilinmeyen hata')} (code={code})",
                    response=response,
                )
            raise ValueError(
                f"Kie AI file upload hatasi: {data.get('msg', 'Bilinmeyen hata')} (code={code})"
            )

        download_url = data.get("downloadUrl") or (data.get("data") or {}).get("downloadUrl")
        if not download_url:
            raise ValueError(f"File upload yanitinda downloadUrl bulunamadi: {data}")

        log.info(f"Dosya yuklendi: {file_name} → {download_url[:80]}...")
        return download_url

    @retry_api_call(max_retries=2, base_delay=2.0, operation_name="Kie AI download")
    def download_file(self, url: str, dest_path: str) -> str:
        """
        URL'deki dosyayi diske indirir (streaming). file:// URL ise kopyalar
        (DRY_RUN uyumu). Doner: dest_path.
        """
        dest_path = str(dest_path)
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)

        parsed = urlparse(url)
        if parsed.scheme == "file":
            src = unquote(parsed.path)
            shutil.copyfile(src, dest_path)
            log.info(f"Lokal dosya kopyalandi: {src} → {dest_path}")
            return dest_path

        tmp_path = dest_path + ".part"
        with requests.get(url, stream=True, timeout=(REQUEST_TIMEOUT, 300)) as response:
            response.raise_for_status()
            with open(tmp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        os.replace(tmp_path, dest_path)

        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        log.info(f"Dosya indirildi: {dest_path} ({size_mb:.1f} MB)")
        return dest_path

    # ─── Kredi ───────────────────────────────────────────────────────────

    def get_credit_balance(self) -> float | None:
        """Hesap bakiyesini kredi cinsinden doner; sorgulanamazsa None."""
        try:
            url = f"{self.base_url}/chat/credit"
            response = requests.get(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                log.warning(f"Kredi sorgusu HTTP {response.status_code}")
                return None
            body = response.json() or {}
            data = body.get("data")
            # data duz sayi (11090.21) ya da {"balance":...} olabilir
            if isinstance(data, (int, float)):
                return float(data)
            if isinstance(data, dict):
                for key in ("balance", "credits", "credit", "remaining"):
                    if data.get(key) is not None:
                        return float(data[key])
            return None
        except Exception:
            log.error("Kredi sorgulama hatasi", exc_info=True)
            return None

    # ─── Internal ────────────────────────────────────────────────────────

    def _validate_quota(self, image_urls=None, audio_ids=None, character_ids=None) -> None:
        validate_omni_quota(image_urls, audio_ids, character_ids)

    @retry_api_call(max_retries=2, base_delay=2.0, operation_name="Kie AI createTask")
    def _create_task(self, payload: dict) -> str:
        """createTask endpoint'ine istek gonderir, taskId doner."""
        url = f"{self.base_url}/jobs/createTask"
        input_block = payload.get("input", {})

        response = requests.post(url, headers=self.headers, json=payload, timeout=REQUEST_TIMEOUT)

        if response.status_code == 422:
            log.error(
                f"Kie AI 422 Validation Error — "
                f"payload_input={json.dumps(input_block, ensure_ascii=False)[:500]}, "
                f"response={response.text[:500]}"
            )
        if response.status_code >= 500:
            log.error(
                f"Kie AI upstream hatasi: HTTP {response.status_code} — "
                f"model={payload.get('model')}, response_body={response.text[:500]}"
            )

        response.raise_for_status()
        data = response.json()

        code = data.get("code")
        if code is not None and str(code) not in ("200", "0"):
            error_msg = data.get("msg", "Bilinmeyen hata")
            code_int = int(code) if str(code).isdigit() else 400
            if code_int in {401, 408, 429} or (500 <= code_int <= 599):
                response.status_code = code_int
                raise requests.exceptions.HTTPError(
                    f"Kie AI createTask API hatasi: {error_msg} (code={code})",
                    response=response,
                )
            raise ValueError(f"Kie AI createTask hatasi: {error_msg} (code={code})")

        task_id = (data.get("data") or {}).get("taskId")
        if not task_id:
            raise ValueError(f"Kie AI createTask yanitinda taskId bulunamadi: {data}")
        return task_id

    @retry_api_call(max_retries=2, base_delay=2.0, operation_name="Kie AI POST")
    def _post_json(self, path: str, payload: dict, operation: str = "") -> dict:
        """Ortak POST + wrapper-code kontrolu; tum yanit govdesini doner."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = requests.post(url, headers=self.headers, json=payload, timeout=REQUEST_TIMEOUT)

        if response.status_code >= 400:
            log.error(
                f"{operation or path}: HTTP {response.status_code} — "
                f"response={response.text[:300]}"
            )
        response.raise_for_status()
        data = response.json()

        code = data.get("code")
        if code is not None and str(code) not in ("200", "0"):
            error_msg = data.get("msg", "Bilinmeyen hata")
            code_int = int(code) if str(code).isdigit() else 400
            if code_int in {401, 408, 429} or (500 <= code_int <= 599):
                response.status_code = code_int
                raise requests.exceptions.HTTPError(
                    f"{operation or path} API hatasi: {error_msg} (code={code})",
                    response=response,
                )
            raise ValueError(f"{operation or path} hatasi: {error_msg} (code={code})")

        return data


def get_omni_client():
    """DRY_RUN'da FakeOmniClient, degilse gercek KieOmniClient doner."""
    from core.config import settings

    if settings.IS_DRY_RUN:
        from services.fake_omni import FakeOmniClient
        return FakeOmniClient()
    return KieOmniClient(settings.KIE_API_KEY, settings.KIE_BASE_URL)
