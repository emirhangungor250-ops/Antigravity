"""
JARVIS Screen Awareness — see what's on the user's screen.

Two capabilities:
1. Window/app list via AppleScript (fast, text-based)
2. Screenshot via screencapture → Claude vision API (sees everything)
"""

import asyncio
import base64
import json
import logging
import tempfile
from pathlib import Path

log = logging.getLogger("jarvis.screen")

from llm_compat import chat, LLM_MODEL, LLM_SMALL_MODEL


async def get_active_windows() -> list[dict]:
    """Get list of visible windows with app name, window title, and position.

    Uses AppleScript + System Events to enumerate windows.
    Returns list of {"app": str, "title": str, "frontmost": bool}.
    """
    # Use a simpler approach that's more permission-friendly
    script = """
set windowList to ""
tell application "System Events"
    set frontApp to name of first application process whose frontmost is true
    set visibleApps to every application process whose visible is true
    repeat with proc in visibleApps
        set appName to name of proc
        try
            set winCount to count of windows of proc
            if winCount > 0 then
                repeat with w in (windows of proc)
                    try
                        set winTitle to name of w
                        if winTitle is not "" and winTitle is not missing value then
                            set windowList to windowList & appName & "|||" & winTitle & "|||" & (appName = frontApp) & linefeed
                        end if
                    end try
                end repeat
            end if
        end try
    end repeat
end tell
return windowList
"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)

        if proc.returncode != 0:
            log.warning(f"get_active_windows failed: {stderr.decode()[:200]}")
            return []

        windows = []
        for line in stdout.decode().strip().split("\n"):
            parts = line.strip().split("|||")
            if len(parts) >= 3:
                windows.append({
                    "app": parts[0].strip(),
                    "title": parts[1].strip(),
                    "frontmost": parts[2].strip().lower() == "true",
                })
        return windows

    except asyncio.TimeoutError:
        log.warning("get_active_windows timed out")
        return []
    except Exception as e:
        log.warning(f"get_active_windows error: {e}")
        return []


async def get_running_apps() -> list[str]:
    """Get list of running application names (visible only)."""
    script = """
tell application "System Events"
    set appNames to name of every application process whose visible is true
    set output to ""
    repeat with a in appNames
        set output to output & a & linefeed
    end repeat
    return output
end tell
"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        if proc.returncode == 0:
            return [a.strip() for a in stdout.decode().strip().split("\n") if a.strip()]
        return []
    except Exception as e:
        log.warning(f"get_running_apps error: {e}")
        return []


async def take_screenshot(display_only: bool = True) -> str | None:
    """Take a screenshot and return base64-encoded PNG.

    Args:
        display_only: If True, capture main display only. If False, all displays.

    Returns:
        Base64-encoded PNG string, or None on failure.
    """
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name

    try:
        cmd = ["screencapture", "-x"]  # -x = no sound
        if display_only:
            cmd.append("-m")  # main display only
        cmd.append(tmp_path)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=10)

        if proc.returncode != 0 or not Path(tmp_path).exists():
            log.warning("Screenshot capture failed")
            return None

        data = Path(tmp_path).read_bytes()
        log.info(f"Screenshot captured: {len(data)} bytes")
        return base64.b64encode(data).decode()

    except asyncio.TimeoutError:
        log.warning("Screenshot timed out")
        return None
    except Exception as e:
        log.warning(f"Screenshot error: {e}")
        return None
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


async def take_all_displays(max_displays: int = 4) -> list[str]:
    """Capture EVERY connected display. Returns a list of base64 PNGs (one per monitor).

    macOS screencapture fills the provided filenames in display order and ignores
    extras, so we can pass more paths than displays and keep only what got written.
    """
    import os
    tmpdir = tempfile.mkdtemp(prefix="jarvis_scrn_")
    paths = [os.path.join(tmpdir, f"d{i}.png") for i in range(max_displays)]
    try:
        proc = await asyncio.create_subprocess_exec(
            "screencapture", "-x", *paths,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=12)
        shots = []
        for p in paths:
            try:
                if Path(p).exists() and Path(p).stat().st_size > 0:
                    shots.append(base64.b64encode(Path(p).read_bytes()).decode())
            except Exception:
                pass
        log.info(f"Captured {len(shots)} display(s)")
        return shots
    except Exception as e:
        log.warning(f"take_all_displays error: {e}")
        return []
    finally:
        for p in paths:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass
        try:
            os.rmdir(tmpdir)
        except Exception:
            pass


async def describe_screen(anthropic_client, user_query: str = "") -> str:
    """Describe what's on the user's screen.

    Tries screenshot + vision first. Falls back to window list + LLM summary.
    user_query: what the user actually asked, so the answer stays relevant.
    """
    # Try screenshot + vision — capture ALL monitors, not just the main one.
    shots = await take_all_displays()
    if shots and anthropic_client:
        try:
            content = [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                for b64 in shots
            ]
            many = len(shots) > 1
            ask = (user_query or "").strip() or "Ekranımda ne var?"
            mon_note = f"{len(shots)} monitör var, her görsel bir monitör. " if many else ""
            content.append({
                "type": "text",
                "text": (
                    f'efendim şunu sordu: "{ask}". {mon_note}'
                    "Buna SADECE Türkçe, en fazla iki kısa cümleyle cevap ver."
                ),
            })
            response = await chat(anthropic_client,
                model=LLM_MODEL,
                max_tokens=160,
                system=(
                    "Sen JARVIS'sin, efendim'in ekran görüntülerine bakıyorsun. "
                    "SADECE TÜRKÇE konuş. Sesli asistan gibi, en fazla iki kısa cümle. Markdown yok. "
                    "ÇOK ÖNEMLİ — KENDİNİ TANI: Ekranda koyu zeminli, ortasında parlayan mavi parçacık "
                    "küresi (orb) olan web arayüzü SENSİN, senin kendi yüzün. Onu ASLA ayrı bir uygulama "
                    "gibi anlatma, 'bir JARVIS arayüzü açık' deme, kendini tarif etme, onu görmezden gel. "
                    "Birden fazla monitör olabilir. efendim'in sorusuyla İLGİLİ olanı söyle; "
                    "ekrandaki her şeyi tek tek sayıp dökme. İlgili bir şey göremezsen kısaca onu söyle."
                ),
                messages=[{"role": "user", "content": content}],
            )
            return response.choices[0].message.content
        except Exception as e:
            log.warning(f"Vision call failed, falling back to window list: {e}")

    # Fallback: get window list and have LLM summarize
    windows = await get_active_windows()
    apps = await get_running_apps()

    if not windows and not apps:
        return "Ekranı göremedim, efendim. Ekran kaydı izni gerekebilir."

    # Build a text description for LLM to summarize
    context_parts = []
    if windows:
        for w in windows:
            marker = " (ACTIVE)" if w["frontmost"] else ""
            context_parts.append(f"{w['app']}: {w['title']}{marker}")

    if apps:
        window_apps = set(w["app"] for w in windows) if windows else set()
        bg_apps = [a for a in apps if a not in window_apps]
        if bg_apps:
            context_parts.append(f"Background apps: {', '.join(bg_apps)}")

    if anthropic_client and context_parts:
        try:
            response = await chat(anthropic_client,
                model=LLM_SMALL_MODEL,
                max_tokens=100,
                system=(
                    "Sen JARVIS'sin. efendim'in açık pencere ve uygulamalarına bakarak "
                    "ne üzerinde çalıştığını SADECE Türkçe, bir iki kısa cümleyle özetle. "
                    "Doğal konuşma, markdown yok. Koyu zeminli parlayan orb arayüzü SENSİN, onu sayma."
                ),
                messages=[{"role": "user", "content": "Açık pencereler:\n" + "\n".join(context_parts)}],
            )
            return response.choices[0].message.content
        except Exception:
            pass

    # Raw fallback (Türkçe)
    if windows:
        active = next((w for w in windows if w["frontmost"]), None)
        app_count = len(set(w['app'] for w in windows))
        result = f"{app_count} uygulamada {len(windows)} pencere açık, efendim."
        if active:
            result += f" Şu an {active['app']} önde."
        return result

    return f"Açık uygulamalar: {', '.join(apps)}. Pencere başlıklarını okuyamadım, efendim."


def format_windows_for_context(windows: list[dict]) -> str:
    """Format window list as context string for the LLM."""
    if not windows:
        return ""
    lines = ["Currently open on your desktop:"]
    for w in windows:
        marker = " (active)" if w["frontmost"] else ""
        lines.append(f"  - {w['app']}: {w['title']}{marker}")
    return "\n".join(lines)
