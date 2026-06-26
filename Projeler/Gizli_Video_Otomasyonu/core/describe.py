"""Açıklama üretimi — YT_Aciklama motorunu ayrı süreç olarak çağırır."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from config import PROJECT_DIR

_RUNNER = PROJECT_DIR / "integrations" / "describe_runner.py"


def generate_description(*, video_name, video_url, brief, transcript, duration_sec,
                         drive_folder_url=None, dry_run=True, doc_name=None) -> dict:
    payload = {
        "video_name": video_name, "video_url": video_url, "brief": brief,
        "transcript": transcript, "duration_sec": duration_sec,
        "drive_folder_url": drive_folder_url, "dry_run": dry_run, "doc_name": doc_name,
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
        json.dump(payload, tf, ensure_ascii=False)
        path = tf.name
    try:
        proc = subprocess.run([sys.executable, str(_RUNNER), path],
                              capture_output=True, text=True, timeout=300)
    finally:
        Path(path).unlink(missing_ok=True)
    for line in proc.stdout.splitlines():
        if line.startswith("__RESULT__"):
            return json.loads(line[len("__RESULT__"):])
    return {"ok": False, "error": (proc.stderr or proc.stdout or "çıktı yok")[-600:]}
