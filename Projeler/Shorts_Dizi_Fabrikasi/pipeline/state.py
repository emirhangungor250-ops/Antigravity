"""Seri/bölüm durum dosyalari: atomic yazma + resume kurallari.

Tum state JSON'lari her gecisten sonra atomic yazilir (*.tmp + os.replace),
boylece surec ortasinda kesilse bile `--devam` kaldigi yerden surer.
"""
import json
import os
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERIES_ROOT = PROJECT_ROOT / "seriler"


def series_dir(slug: str) -> Path:
    return SERIES_ROOT / slug


def refs_dir(slug: str) -> Path:
    return series_dir(slug) / "refs"


def episodes_dir(slug: str) -> Path:
    return series_dir(slug) / "bolumler"


def episode_dir(slug: str, ep_slug: str) -> Path:
    return episodes_dir(slug) / ep_slug


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ─── Bible ────────────────────────────────────────────────────────────────

def bible_path(slug: str) -> Path:
    return series_dir(slug) / "bible.json"


def load_bible(slug: str) -> Optional[dict]:
    return load_json(bible_path(slug))


def save_bible(slug: str, bible: dict) -> None:
    atomic_write_json(bible_path(slug), bible)


# ─── Seri hafizasi ────────────────────────────────────────────────────────

def series_state_path(slug: str) -> Path:
    return series_dir(slug) / "series_state.json"


def load_series_state(slug: str) -> dict:
    return load_json(series_state_path(slug)) or {
        "series_slug": slug,
        "episodes_produced": 0,
        "applied_episodes": [],
        "season_summary_tr": "",
        "recent_episodes": [],
        "open_threads": [],
        "character_state": {},
        "canon_facts": [],
        "used_hooks": [],
    }


def save_series_state(slug: str, state: dict) -> None:
    atomic_write_json(series_state_path(slug), state)


# ─── Bölüm ────────────────────────────────────────────────────────────────

def episode_path(slug: str, ep_slug: str) -> Path:
    return episode_dir(slug, ep_slug) / "episode.json"


def load_episode(slug: str, ep_slug: str) -> Optional[dict]:
    return load_json(episode_path(slug, ep_slug))


def save_episode(slug: str, ep: dict) -> None:
    atomic_write_json(episode_path(slug, ep["slug"]), ep)


def next_episode_slug(bible: dict) -> str:
    return "b%03d" % (bible.get("episodes", {}).get("counter", 0) + 1)


def find_unfinished_episode(slug: str) -> Optional[dict]:
    """status != done olan en son bölümü döndürür (--devam otomatik tespiti)."""
    root = episodes_dir(slug)
    if not root.exists():
        return None
    for ep_dir in sorted(root.iterdir(), reverse=True):
        ep = load_json(ep_dir / "episode.json")
        if ep and ep.get("status") != "done":
            return ep
    return None


# ─── Sahne resume kurallari ───────────────────────────────────────────────

def scene_needs_submit(scene: dict, slug: str, ep_slug: str) -> bool:
    """pending veya (failed ve attempts<2) → yeniden gönderilir."""
    if scene["status"] == "pending":
        return True
    if scene["status"] == "failed" and scene.get("attempts", 0) < 2:
        return True
    return False


def scene_is_complete(scene: dict, slug: str, ep_slug: str) -> bool:
    """completed VE klip dosyasi diskte → atla."""
    if scene["status"] != "completed":
        return False
    clip = episode_dir(slug, ep_slug) / scene["clip_path"]
    return clip.exists() and clip.stat().st_size > 0
