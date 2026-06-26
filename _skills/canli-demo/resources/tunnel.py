"""Cloudflared quick tunnel sarmalayıcı.

cloudflared'i background process olarak başlatır, stdout'tan
`*.trycloudflare.com` URL'ini parse eder ve döner.
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import sys
from pathlib import Path

TUNNEL_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")

_PACKAGE_BIN = Path(__file__).resolve().parents[1] / "bin" / "cloudflared"


def cloudflared_path() -> str | None:
    """PATH'te varsa onu, yoksa paket-relative bin/ altındakini döndürür."""
    p = shutil.which("cloudflared")
    if p:
        return p
    if _PACKAGE_BIN.exists() and os.access(_PACKAGE_BIN, os.X_OK):
        return str(_PACKAGE_BIN)
    return None


def cloudflared_available() -> bool:
    return cloudflared_path() is not None


async def start_quick_tunnel(local_port: int, timeout_sec: float = 60.0) -> tuple[asyncio.subprocess.Process, str]:
    """cloudflared quick tunnel başlat, URL'i döndür.

    Returns (process, url). Caller process.terminate() ile kapatmaktan sorumlu.
    """
    binary = cloudflared_path()
    if not binary:
        raise RuntimeError(
            "cloudflared bulunamadı. `bash _skills/canli-demo/install.sh` ile kur."
        )

    proc = await asyncio.create_subprocess_exec(
        binary,
        "tunnel",
        "--no-autoupdate",
        "--url",
        f"http://localhost:{local_port}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    url: str | None = None
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout_sec

    try:
        while loop.time() < deadline:
            if proc.stdout is None:
                break
            try:
                line_bytes = await asyncio.wait_for(proc.stdout.readline(), timeout=2.0)
            except asyncio.TimeoutError:
                continue
            if not line_bytes:
                break
            line = line_bytes.decode(errors="replace")
            print(f"  [cloudflared] {line.rstrip()}", file=sys.stderr)
            m = TUNNEL_URL_RE.search(line)
            if m:
                url = m.group(0)
                break
    except asyncio.CancelledError:
        proc.terminate()
        raise

    if not url:
        proc.terminate()
        raise RuntimeError("cloudflared tunnel URL'i alınamadı (timeout)")

    return proc, url
