"""Otomasyon filosu collector.

`_knowledge/routines.json` kaydini okur. autonomous_quality routine'lerinin
sagligini `_knowledge/autonomous_quality/logs/` klasorunden canli cikarir.
Takvim izgarasi + ozet + kayitsiz routine tespiti uretir.
"""
from __future__ import annotations

import glob
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ANTIGRAVITY_ROOT = Path(__file__).resolve().parents[3]
ROUTINES_JSON = ANTIGRAVITY_ROOT / "_knowledge" / "routines.json"
LOGS_DIR = ANTIGRAVITY_ROOT / "_knowledge" / "autonomous_quality" / "logs"

DAYS = ["Pzt", "Sal", "Car", "Per", "Cum", "Cmt", "Paz"]
DAY_FULL = {
    "Pzt": "Pazartesi", "Sal": "Sali", "Car": "Carsamba", "Per": "Persembe",
    "Cum": "Cuma", "Cmt": "Cumartesi", "Paz": "Pazar",
}


def _newest_log_date(prefix: str) -> tuple[str | None, bool]:
    """Verilen prefix icin en yeni log dosyasinin tarihini ve hata durumunu doner."""
    pattern = str(LOGS_DIR / f"{prefix}_*.json")
    files = glob.glob(pattern)
    if not files:
        return None, False
    best_date = None
    best_file = None
    for f in files:
        m = re.search(r"_(\d{4}-\d{2}-\d{2})\.json$", f)
        if not m:
            continue
        d = m.group(1)
        if best_date is None or d > best_date:
            best_date = d
            best_file = f
    has_error = False
    if best_file:
        try:
            data = json.loads(Path(best_file).read_text())
            has_error = bool(data.get("errors"))
        except Exception:
            pass
    return best_date, has_error


def _health(routine: dict) -> dict:
    """Bir routine icin saglik durumu hesaplar."""
    prefix = routine.get("log_prefix")
    aralik = routine.get("beklenen_aralik_gun", 7)

    if not prefix:
        return {
            "status": "zamanli",
            "renk": "gri",
            "son_kosu": "canli takip yok",
            "son_kosu_iso": None,
        }

    last_date, has_error = _newest_log_date(prefix)
    if not last_date:
        return {
            "status": "bekliyor",
            "renk": "sari",
            "son_kosu": "henuz kosmadi",
            "son_kosu_iso": None,
        }

    try:
        last_dt = datetime.strptime(last_date, "%Y-%m-%d")
    except ValueError:
        return {"status": "bilinmiyor", "renk": "gri", "son_kosu": last_date, "son_kosu_iso": last_date}

    gun_once = (datetime.now() - last_dt).days
    if gun_once <= 0:
        son_kosu = "bugun"
    elif gun_once == 1:
        son_kosu = "dun"
    else:
        son_kosu = f"{gun_once} gun once"

    if has_error:
        return {"status": "hatali", "renk": "kirmizi", "son_kosu": f"{son_kosu}, hata aldi", "son_kosu_iso": last_date}

    if gun_once <= aralik * 1.6:
        renk, status = "yesil", "saglikli"
    elif gun_once <= aralik * 3:
        renk, status = "sari", "gecikmis"
    else:
        renk, status = "kirmizi", "olu"

    return {"status": status, "renk": renk, "son_kosu": son_kosu, "son_kosu_iso": last_date}


def _next_run(routine: dict) -> str:
    """Bir sonraki calisma zamanini insan diliyle doner."""
    now = datetime.now()
    saat = routine.get("saat", "00:00")
    try:
        hh, mm = (int(x) for x in saat.split(":"))
    except ValueError:
        hh, mm = 0, 0

    if routine.get("aylik"):
        if now.month == 12:
            nxt = datetime(now.year + 1, 1, 1, hh, mm)
        else:
            nxt = datetime(now.year, now.month + 1, 1, hh, mm)
        return f"1 {nxt.strftime('%b')} {saat}"

    gunler = routine.get("gunler", [])
    gun_idx = {d: i for i, d in enumerate(DAYS)}
    hedef_idxler = sorted(gun_idx[g] for g in gunler if g in gun_idx)
    if not hedef_idxler:
        return "bilinmiyor"

    bugun_idx = now.weekday()
    for offset in range(0, 8):
        kontrol = (bugun_idx + offset) % 7
        if kontrol in hedef_idxler:
            if offset == 0:
                if now.hour < hh or (now.hour == hh and now.minute < mm):
                    return f"bugun {saat}"
                continue
            if offset == 1:
                return f"yarin {saat}"
            return f"{DAY_FULL[DAYS[kontrol]]} {saat}"
    return "bilinmiyor"


def collect() -> dict[str, Any]:
    if not ROUTINES_JSON.exists():
        return {"ok": False, "error": f"routines.json yok: {ROUTINES_JSON}"}

    try:
        reg = json.loads(ROUTINES_JSON.read_text())
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"routines.json bozuk: {e}"}

    routines = reg.get("routines", [])
    enriched = []
    kayitli_prefixler = set()

    for r in routines:
        if r.get("log_prefix"):
            kayitli_prefixler.add(r["log_prefix"])
        h = _health(r)
        enriched.append({
            **r,
            "health": h,
            "next_run": _next_run(r),
        })

    # Ozet
    sayac = {"yesil": 0, "sari": 0, "kirmizi": 0, "gri": 0}
    for r in enriched:
        sayac[r["health"]["renk"]] = sayac.get(r["health"]["renk"], 0) + 1

    # Takvim izgarasi — sadece haftalik (aylik olmayan) routine'ler
    haftalik = [r for r in enriched if not r.get("aylik")]
    saatler = sorted({r["saat"] for r in haftalik})
    grid = {}  # grid[saat][gun] = [routine, ...]
    for saat in saatler:
        grid[saat] = {d: [] for d in DAYS}
    for r in haftalik:
        for g in r.get("gunler", []):
            if g in DAYS and r["saat"] in grid:
                grid[r["saat"]][g].append(r)

    aylik = [r for r in enriched if r.get("aylik")]

    # Kayitsiz routine tespiti — logs/ altinda olup routines.json'da olmayan
    kayitsiz = []
    if LOGS_DIR.exists():
        gorulen = set()
        for f in glob.glob(str(LOGS_DIR / "*.json")):
            base = os.path.basename(f)
            m = re.match(r"(.+?)_\d{4}-\d{2}-\d{2}\.json$", base)
            if m:
                gorulen.add(m.group(1))
        for pre in sorted(gorulen - kayitli_prefixler):
            kayitsiz.append(pre)

    bugun_idx = datetime.now().weekday()

    return {
        "ok": True,
        "routines": enriched,
        "gunler": DAYS,
        "bugun_gun": DAYS[bugun_idx],
        "saatler": saatler,
        "grid": grid,
        "aylik": aylik,
        "ozet": sayac,
        "toplam": len(enriched),
        "kayitsiz": kayitsiz,
        "son_guncelleme": reg.get("son_guncelleme", "?"),
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(collect())
