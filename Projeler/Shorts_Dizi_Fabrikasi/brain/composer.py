"""Deterministik final video prompt'u (LLM çağrısı YOK).

Senarist LLM yapısal alanlar üretir; bu modül sabit şablonla birleştirir.
Stil bloğu her sahnede bayt-bayt aynı kalır, diyalog formatı garantilidir.
Şablon sırası SABİT: style → CONTEXT → SCENE → CAMERA → LIGHTING →
DIALOGUE → AUDIO → REFERENCES → CONSTRAINTS.
"""
import logging
from typing import Optional

from brain.sanitizer import sanitize_text
from brain.schemas import SceneSpec

log = logging.getLogger("Composer")

SEED_MOD = 2147483647

_CONSTRAINTS_BASE = (
    "Single continuous shot, no cuts. Stable, natural motion. "
    "No subtitles, no captions, no on-screen text, no watermark, no logos."
)
_CHARACTER_LOCK = (
    "must look exactly like their character references: "
    "same face, same hair, same outfit."
)


def derive_scene_seed(series_seed: int, episode_no: int, scene_no: int, attempt: int = 0) -> int:
    return (series_seed + episode_no * 1000 + scene_no * 10 + attempt) % SEED_MOD


def _character_name(speaker: str, bible: dict) -> str:
    """speaker id → /omni/character/create'e kayıtlı isim (ses-ağız eşleşmesi)."""
    if speaker == "NARRATOR":
        return "Narrator (voice-over)"
    char = next((c for c in bible.get("characters", []) if c.get("id") == speaker), None)
    return char.get("name", speaker) if char else speaker


def _references_block(refs: dict) -> str:
    lines = ["REFERENCES:"]
    char_names = [name for _, kind, name in refs["manifest"] if kind == "character"]
    if char_names:
        lines.append(f"- {', '.join(char_names)} {_CHARACTER_LOCK}")
    for slot, kind, name in refs["manifest"]:
        if kind == "environment":
            lines.append(
                f"- Reference image {slot} is the empty location plate of {name}; "
                "match this exact location, layout and time of day."
            )
        elif kind == "style_board":
            lines.append(
                f"- Reference image {slot} is the series style board; "
                "match its palette, grading and overall look."
            )
        elif kind == "prop":
            lines.append(
                f"- Reference image {slot} is the prop '{name}'; "
                "it must appear exactly as shown."
            )
    return "\n".join(lines)


def compose_scene_prompt(
    scene: SceneSpec,
    bible: dict,
    refs: dict,
    continuity_override: Optional[str] = None,
) -> str:
    style = bible.get("style") or bible.get("art_style") or {}
    style_paragraph = style.get("style_paragraph", "")
    negative_constraints = style.get("negative_constraints", [])

    action, action_hits = sanitize_text(scene.action)
    sfx, sfx_hits = sanitize_text(scene.sfx)
    if action_hits or sfx_hits:
        log.info("sahne %s: sanitizer tetiklendi: %s", scene.scene_number, action_hits + sfx_hits)

    continuity = (
        continuity_override if continuity_override is not None
        else scene.continuity_from_previous
    )
    camera = scene.camera.strip().rstrip(".")
    sfx = sfx.strip().rstrip(".")

    parts = [
        style_paragraph,
        "",
        f"CONTEXT: {continuity}",
        f"SCENE: {action}",
        f"CAMERA: {camera}. Vertical 9:16 framing, subject centered for mobile viewing.",
        f"LIGHTING: {scene.lighting}",
    ]
    if scene.dialogue:
        parts.append("DIALOGUE (all lines spoken in Turkish):")
        for line in scene.dialogue:
            name = _character_name(line.speaker, bible)
            parts.append(f'- {name} says in Turkish: "{line.line_tr}" ({line.delivery_en})')
    parts.append(f"AUDIO: {sfx}. Quiet natural ambience only. No background music.")
    parts.append(_references_block(refs))

    constraints = _CONSTRAINTS_BASE
    if negative_constraints:
        constraints += " " + " ".join(c.strip().rstrip(".") + "." for c in negative_constraints)
    parts.append(f"CONSTRAINTS: {constraints}")

    return "\n".join(parts)
