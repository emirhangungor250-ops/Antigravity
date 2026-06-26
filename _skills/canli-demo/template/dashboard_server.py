"""FastAPI canlı demo dashboard servisi.

Bu dosya `_skills/canli-demo/` paketinin template'idir; sync.py her projeye
overwrite eder. Yalnızca DASHBOARD_ENABLED=1 ortam değişkeni set edilince
ana proje tarafından arka plan task'ı olarak başlatılır.

Stabilizasyon:
- SSE response'da `retry: 3000` (tarayıcı 3s'de tekrar bağlanır)
- `Last-Event-ID` header'ı veya `?last_id=` query param ile event replay
- Robust serializer (emitter tarafında, datetime/Path/set güvenli)
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from core.run_state import PROJECT_META, emitter

PUBLIC_URL = os.getenv("DASHBOARD_PUBLIC_URL") or ""

_ROOT = Path(__file__).resolve().parent
_DASHBOARD_DIR = _ROOT / "dashboard"

app = FastAPI(title=f"{PROJECT_META.get('title', 'Canlı Demo')} — Canlı Dashboard")

app.mount("/static", StaticFiles(directory=str(_DASHBOARD_DIR)), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(str(_DASHBOARD_DIR / "index.html"))


@app.get("/api/state")
async def get_state() -> JSONResponse:
    return JSONResponse({
        "meta": {**PROJECT_META, "public_url": PUBLIC_URL},
        "snapshot": emitter.snapshot(),
        "stages": emitter.stage_definitions(),
    })


@app.get("/qr.svg")
async def qr_svg() -> Response:
    if not PUBLIC_URL:
        return Response("no public url configured", status_code=404)
    try:
        import qrcode
        from qrcode.image.svg import SvgPathImage
    except ImportError:
        return Response("qrcode library yok", status_code=503)
    img = qrcode.make(PUBLIC_URL, image_factory=SvgPathImage, box_size=10, border=2)
    import io
    buf = io.BytesIO()
    img.save(buf)
    return Response(buf.getvalue(), media_type="image/svg+xml")


def _parse_last_id(request: Request) -> int:
    header = request.headers.get("last-event-id") or ""
    query = request.query_params.get("last_id") or ""
    raw = header or query
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


@app.get("/events")
async def events(request: Request) -> StreamingResponse:
    last_id = _parse_last_id(request)
    queue = emitter.subscribe()

    async def generator():
        try:
            yield "retry: 3000\n\n"

            if last_id > 0:
                for line in emitter.replay_since(last_id):
                    event_id = json.loads(line).get("id", 0)
                    yield f"id: {event_id}\ndata: {line}\n\n"

            initial = {
                "type": "hydrate",
                "snapshot": emitter.snapshot(),
            }
            yield f"data: {json.dumps(initial, ensure_ascii=False)}\n\n"

            while True:
                if await request.is_disconnected():
                    break
                try:
                    line = await asyncio.wait_for(queue.get(), timeout=15.0)
                    try:
                        event_id = json.loads(line).get("id", 0)
                    except Exception:
                        event_id = 0
                    yield f"id: {event_id}\ndata: {line}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            raise
        finally:
            emitter.unsubscribe(queue)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def start_dashboard() -> None:
    """Dashboard server'ı arka plan task'ı olarak başlat."""
    port = int(os.getenv("DASHBOARD_PORT", "8000"))
    host = os.getenv("DASHBOARD_HOST", "127.0.0.1")
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(start_dashboard())
