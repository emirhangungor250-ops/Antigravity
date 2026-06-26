"""Canlı demo için generic pipeline event emitter.

Bu modül `_skills/canli-demo/` paketinin template'idir — `sync.py` her projeye
kopyalar. Projenin pipeline'ı emitter event'leri (`start_stage`, `update_stage`,
`end_stage`, vb.) tetikler. Dashboard server bu event'leri SSE ile tarayıcıya
yayar.

Stage tanımları projeye özgüdür ve `stages.py` dosyasından import edilir.
Generic kalmak için bu modül stages.py içeriğine müdahale etmez.

Stabilizasyon notları:
- Her event'e sıralı `id` verilir; client `Last-Event-ID` ile reconnect olunca
  kaçırdığı event'ler buffer'dan replay edilebilir.
- Serializer datetime/Path/set/UUID gibi tipleri otomatik repr'a düşer.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Iterable

try:
    from stages import STAGES as STAGE_DEFINITIONS  # type: ignore
except Exception:
    STAGE_DEFINITIONS: list[dict[str, Any]] = []

try:
    from stages import META as PROJECT_META  # type: ignore
except Exception:
    PROJECT_META: dict[str, Any] = {"title": "Canlı Demo", "subtitle": ""}


def _now() -> float:
    return time.time()


def _safe_default(o: Any) -> Any:
    if isinstance(o, (set, frozenset)):
        return list(o)
    if isinstance(o, Path):
        return str(o)
    if hasattr(o, "isoformat"):
        try:
            return o.isoformat()
        except Exception:
            pass
    return repr(o)


def _empty_sub_stage(sub_def: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": sub_def["id"],
        "label": sub_def.get("label", sub_def["id"]),
        "icon": sub_def.get("icon", "·"),
        "status": "pending",
        "started_at": None,
        "ended_at": None,
        "elapsed_sec": None,
        "sub_text": None,
        "progress": None,
        "payload": None,
        "error": None,
    }


def _empty_stages(definitions: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    stages: dict[str, dict[str, Any]] = {}
    for s in definitions:
        stage = {
            "id": s["id"],
            "label": s.get("label", s["id"]),
            "icon": s.get("icon", "•"),
            "status": "pending",
            "started_at": None,
            "ended_at": None,
            "elapsed_sec": None,
            "sub_text": None,
            "progress": None,
            "payload": None,
            "error": None,
        }
        if "sub_stages" in s:
            stage["sub_stages"] = {
                sub["id"]: _empty_sub_stage(sub) for sub in s["sub_stages"]
            }
            stage["sub_stage_order"] = [sub["id"] for sub in s["sub_stages"]]
        stages[s["id"]] = stage
    return stages


class RunStateEmitter:
    def __init__(self, stages: list[dict[str, Any]] | None = None) -> None:
        self._stages_def = stages if stages is not None else STAGE_DEFINITIONS
        self._subscribers: list[asyncio.Queue[str]] = []
        self._snapshot: dict[str, Any] = self._idle_snapshot()
        self._event_log: deque[dict[str, Any]] = deque(maxlen=500)
        self._next_event_id = 1
        self._lock = asyncio.Lock()

    def _idle_snapshot(self) -> dict[str, Any]:
        return {
            "run_id": None,
            "input_label": None,
            "status": "idle",
            "started_at": None,
            "ended_at": None,
            "elapsed_sec": None,
            "final_payload": None,
            "stage_order": [s["id"] for s in self._stages_def],
            "stages": _empty_stages(self._stages_def),
        }

    def snapshot(self) -> dict[str, Any]:
        return json.loads(json.dumps(self._snapshot, default=_safe_default))

    def stage_definitions(self) -> list[dict[str, Any]]:
        return list(self._stages_def)

    def replay_since(self, last_id: int) -> list[str]:
        return [
            self._serialize(ev) for ev in self._event_log if ev.get("id", 0) > last_id
        ]

    def subscribe(self) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=256)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[str]) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def _serialize(self, event: dict[str, Any]) -> str:
        try:
            return json.dumps(event, ensure_ascii=False, default=_safe_default)
        except Exception:
            return json.dumps(
                {"id": event.get("id"), "type": event.get("type", "?"), "ts": event.get("ts")}
            )

    def _publish(self, event: dict[str, Any]) -> None:
        event["ts"] = _now()
        event["id"] = self._next_event_id
        self._next_event_id += 1
        self._event_log.append(dict(event))
        line = self._serialize(event)
        for q in list(self._subscribers):
            try:
                q.put_nowait(line)
            except asyncio.QueueFull:
                pass

    def start_run(self, input_label: str | None = None, run_id: str | None = None) -> str:
        rid = run_id or uuid.uuid4().hex[:8]
        self._snapshot = self._idle_snapshot()
        self._snapshot["run_id"] = rid
        self._snapshot["input_label"] = input_label
        self._snapshot["status"] = "running"
        self._snapshot["started_at"] = _now()
        self._publish({
            "type": "run_start",
            "run_id": rid,
            "input_label": input_label,
            "started_at": self._snapshot["started_at"],
            "snapshot": self.snapshot(),
        })
        return rid

    def start_stage(self, stage_id: str, sub_text: str | None = None) -> None:
        stage = self._snapshot["stages"].get(stage_id)
        if not stage:
            return
        stage["status"] = "active"
        stage["started_at"] = _now()
        stage["sub_text"] = sub_text
        self._publish({
            "type": "stage_start",
            "stage_id": stage_id,
            "label": stage["label"],
            "sub_text": sub_text,
            "started_at": stage["started_at"],
        })

    def update_stage(
        self,
        stage_id: str,
        sub_text: str | None = None,
        progress: float | None = None,
    ) -> None:
        stage = self._snapshot["stages"].get(stage_id)
        if not stage or stage["status"] != "active":
            return
        if sub_text is not None:
            stage["sub_text"] = sub_text
        if progress is not None:
            stage["progress"] = progress
        self._publish({
            "type": "stage_update",
            "stage_id": stage_id,
            "sub_text": stage["sub_text"],
            "progress": stage["progress"],
        })

    def end_stage(self, stage_id: str, payload: dict[str, Any] | None = None) -> None:
        stage = self._snapshot["stages"].get(stage_id)
        if not stage:
            return
        ended = _now()
        stage["status"] = "completed"
        stage["ended_at"] = ended
        if stage["started_at"]:
            stage["elapsed_sec"] = round(ended - stage["started_at"], 1)
        stage["payload"] = payload
        stage["sub_text"] = None
        self._publish({
            "type": "stage_end",
            "stage_id": stage_id,
            "ended_at": ended,
            "elapsed_sec": stage["elapsed_sec"],
            "payload": payload,
        })

    def fail_stage(self, stage_id: str, error: str) -> None:
        stage = self._snapshot["stages"].get(stage_id)
        if not stage:
            return
        ended = _now()
        stage["status"] = "error"
        stage["ended_at"] = ended
        if stage["started_at"]:
            stage["elapsed_sec"] = round(ended - stage["started_at"], 1)
        stage["error"] = error
        self._publish({
            "type": "stage_fail",
            "stage_id": stage_id,
            "error": error,
            "elapsed_sec": stage["elapsed_sec"],
        })

    def _get_sub(self, stage_id: str, sub_id: str) -> dict[str, Any] | None:
        stage = self._snapshot["stages"].get(stage_id) or {}
        return (stage.get("sub_stages") or {}).get(sub_id)

    def start_substage(
        self, stage_id: str, sub_id: str, sub_text: str | None = None
    ) -> None:
        sub = self._get_sub(stage_id, sub_id)
        if not sub:
            return
        sub["status"] = "active"
        sub["started_at"] = _now()
        sub["sub_text"] = sub_text
        self._publish({
            "type": "substage_start",
            "stage_id": stage_id,
            "sub_id": sub_id,
            "sub_text": sub_text,
            "started_at": sub["started_at"],
        })

    def update_substage(
        self,
        stage_id: str,
        sub_id: str,
        sub_text: str | None = None,
        progress: float | None = None,
    ) -> None:
        sub = self._get_sub(stage_id, sub_id)
        if not sub or sub["status"] not in ("active", "pending"):
            return
        if sub_text is not None:
            sub["sub_text"] = sub_text
        if progress is not None:
            sub["progress"] = progress
        self._publish({
            "type": "substage_update",
            "stage_id": stage_id,
            "sub_id": sub_id,
            "sub_text": sub["sub_text"],
            "progress": sub["progress"],
        })

    def end_substage(
        self, stage_id: str, sub_id: str, payload: dict[str, Any] | None = None
    ) -> None:
        sub = self._get_sub(stage_id, sub_id)
        if not sub:
            return
        ended = _now()
        sub["status"] = "completed"
        sub["ended_at"] = ended
        if sub["started_at"]:
            sub["elapsed_sec"] = round(ended - sub["started_at"], 1)
        sub["payload"] = payload
        sub["sub_text"] = None
        self._publish({
            "type": "substage_end",
            "stage_id": stage_id,
            "sub_id": sub_id,
            "ended_at": ended,
            "elapsed_sec": sub["elapsed_sec"],
            "payload": payload,
        })

    def fail_substage(self, stage_id: str, sub_id: str, error: str) -> None:
        sub = self._get_sub(stage_id, sub_id)
        if not sub:
            return
        ended = _now()
        sub["status"] = "error"
        sub["ended_at"] = ended
        if sub["started_at"]:
            sub["elapsed_sec"] = round(ended - sub["started_at"], 1)
        sub["error"] = error
        self._publish({
            "type": "substage_fail",
            "stage_id": stage_id,
            "sub_id": sub_id,
            "error": error,
            "elapsed_sec": sub["elapsed_sec"],
        })

    def end_run(self, final_payload: dict[str, Any] | None = None) -> None:
        if self._snapshot["status"] != "running":
            return
        ended = _now()
        self._snapshot["status"] = "completed"
        self._snapshot["ended_at"] = ended
        self._snapshot["final_payload"] = final_payload
        if self._snapshot["started_at"]:
            self._snapshot["elapsed_sec"] = round(
                ended - self._snapshot["started_at"], 1
            )
        self._publish({
            "type": "run_end",
            "ended_at": ended,
            "elapsed_sec": self._snapshot["elapsed_sec"],
            "final_payload": final_payload,
        })

    def fail_run(self, error: str) -> None:
        ended = _now()
        self._snapshot["status"] = "error"
        self._snapshot["ended_at"] = ended
        if self._snapshot["started_at"]:
            self._snapshot["elapsed_sec"] = round(
                ended - self._snapshot["started_at"], 1
            )
        self._publish({
            "type": "run_fail",
            "error": error,
            "ended_at": ended,
        })

    def reset_idle(self) -> None:
        self._snapshot = self._idle_snapshot()
        self._publish({"type": "idle"})


emitter = RunStateEmitter()
