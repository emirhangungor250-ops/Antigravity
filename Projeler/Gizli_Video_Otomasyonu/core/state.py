"""İşlenen video kaydı — aynı videoyu iki kez işlememek için.

Anahtar = YouTube video id. Railway efemera disk olduğundan kalıcılık için
durum ayrıca Notion'a da yazılır (bkz. main); bu dosya lokal/çalışma-içi hız içindir.
"""
import json
from datetime import datetime, timezone

from config import STATE_PATH


def load_seen() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def is_seen(video_id: str) -> bool:
    return video_id in load_seen()


def mark_seen(video_id: str, info: dict) -> None:
    state = load_seen()
    state[video_id] = {**info, "marked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_PATH)
