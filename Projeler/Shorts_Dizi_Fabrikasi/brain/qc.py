"""Kalite kapisi.

Tier 1: deterministik ffprobe kontrolleri — BLOKLAYICI.
Tier 2: haiku vision bayragi — SADECE RAPOR, asla bloklamaz
        (herhangi bir hatada None = auto-pass).
"""
import base64
from pathlib import Path

from core.config import settings
from brain import client
from brain.schemas import QCVerdict

MIN_CLIP_BYTES = 100 * 1024
DURATION_TOLERANCE_S = 1.0
EXPECTED_W, EXPECTED_H = 1080, 1920

_MEDIA_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _field(info, key):
    """probe ciktisi dict de olsa nesne de olsa calissin."""
    if isinstance(info, dict):
        return info.get(key)
    return getattr(info, key, None)


def tier1_check(clip_path, expected_duration: int, expect_audio: bool):
    """(ok, sebep) doner. DRY_RUN'da da ayni calisir (placeholder gercek surede/cozunurlukte)."""
    path = Path(clip_path)
    if not path.exists():
        return False, f"clip file missing: {path}"
    size = path.stat().st_size
    if size <= MIN_CLIP_BYTES:
        return False, f"clip too small: {size} bytes (min {MIN_CLIP_BYTES})"

    from services.ffmpeg_assembler import probe
    info = probe(str(path))

    duration = _field(info, "duration_s")
    if duration is None:
        duration = _field(info, "duration")
    if duration is None:
        return False, "probe returned no duration"
    if abs(float(duration) - float(expected_duration)) > DURATION_TOLERANCE_S:
        return False, f"duration {float(duration):.2f}s, expected {expected_duration}s (±{DURATION_TOLERANCE_S}s)"

    width, height = _field(info, "width"), _field(info, "height")
    if width != EXPECTED_W or height != EXPECTED_H:
        return False, f"resolution {width}x{height}, expected {EXPECTED_W}x{EXPECTED_H}"

    if expect_audio and not _field(info, "has_audio"):
        return False, "dialogue scene has no audio stream"

    return True, "ok"


def _image_block(path: Path) -> dict:
    media_type = _MEDIA_TYPES.get(path.suffix.lower(), "image/png")
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}}


def tier2_flag(clip_path, char_ref_paths, scene_desc: str):
    """Haiku vision karsilastirmasi. Sonuc dict (QCVerdict) veya None (auto-pass)."""
    if settings.IS_DRY_RUN:
        return None
    try:
        from services.ffmpeg_assembler import extract_frame
        frame_path = Path(extract_frame(str(clip_path), str(clip_path) + ".qc.png", 1.0))

        content = [
            {"type": "text", "text": "FRAME FROM GENERATED CLIP (t=1s):"},
            _image_block(frame_path),
        ]
        for i, ref in enumerate(char_ref_paths, 1):
            content.append({"type": "text", "text": f"CHARACTER REFERENCE {i}:"})
            content.append(_image_block(Path(ref)))
        content.append({
            "type": "text",
            "text": f"SCENE DESCRIPTION:\n{scene_desc}\n\nCompare the clip frame against the references and the description.",
        })

        system_text = client._load_prompt("qc_vision.md")
        response = client._client().messages.parse(
            model=settings.QC_MODEL,
            max_tokens=1000,
            system=system_text,
            messages=[{"role": "user", "content": content}],
            output_format=QCVerdict,
        )
        client._log_usage(settings.QC_MODEL, response)
        verdict = response.parsed_output
        return verdict.model_dump() if verdict is not None else None
    except Exception:
        return None
