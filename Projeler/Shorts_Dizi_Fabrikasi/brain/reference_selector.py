"""Kota-bilinçli referans seçimi (kod, LLM değil).

Gemini Omni görev başına 7 birim referans alır (görsel=1, karakter=1).
Öncelik: kimlik > mekân > stil > obje. audio_ids kota tüketmez (sadece anlatıcı).
"""
from typing import List, Optional, Tuple

from brain.schemas import SceneSpec

UNITS = 7

# kota taşarsa alttan atma sırası (karakter ASLA atılmaz)
_DROP_ORDER = ("prop", "style_board", "environment")


def _by_id(items: List[dict], item_id: str) -> Optional[dict]:
    return next((i for i in items if i.get("id") == item_id), None)


def _public_url(item: Optional[dict]) -> Optional[str]:
    return ((item or {}).get("ref_image") or {}).get("public_url")


def select_references(scene: SceneSpec, bible: dict) -> dict:
    """Sahne için Kie createTask referanslarını seçer.

    Returns: {"character_ids", "image_urls", "audio_ids", "manifest"}
    manifest: [(slot, kind, name)] — kind: character/environment/style_board/prop.
    Karakterler için slot = character_ids sırası, görseller için slot = image_urls sırası.
    """
    # 1) sahne karakterleri → kie character id'leri (her biri 1 birim, maks 3)
    characters: List[Tuple[str, str]] = []  # (kie_character_id, name)
    for cid in scene.character_ids[:3]:
        char = _by_id(bible.get("characters", []), cid)
        if char and char.get("kie_character_id"):
            characters.append((char["kie_character_id"], char.get("name", cid)))

    # 2-3-5) görsel slotları: ortam plakası → stil panosu → aksesuarlar (sahne sırası)
    images: List[Tuple[str, str, str]] = []  # (url, kind, name)
    env = _by_id(bible.get("environments", []), scene.environment_id)
    env_url = _public_url(env)
    if env_url:
        images.append((env_url, "environment", (env or {}).get("name_tr", scene.environment_id)))
    style_url = ((bible.get("style") or {}).get("style_board") or {}).get("public_url")
    if style_url:
        images.append((style_url, "style_board", "series style board"))
    for pid in scene.prop_ids:
        prop = _by_id(bible.get("props", []), pid)
        prop_url = _public_url(prop)
        if prop_url:
            images.append((prop_url, "prop", (prop or {}).get("name_tr", pid)))

    # 4) anlatıcı sesi (kota tüketmez)
    audio_ids: List[str] = []
    if any(line.speaker == "NARRATOR" for line in scene.dialogue):
        narrator = bible.get("narrator") or {}
        if narrator.get("enabled") and narrator.get("kie_audio_id"):
            audio_ids = [narrator["kie_audio_id"]]

    # kota: taşarsa alttan at (prop → stil → ortam; karakter asla)
    while len(characters) + len(images) > UNITS:
        for kind in _DROP_ORDER:
            idx = next((i for i in range(len(images) - 1, -1, -1) if images[i][1] == kind), None)
            if idx is not None:
                images.pop(idx)
                break
        else:
            break
    assert len(characters) + len(images) <= UNITS

    manifest: List[Tuple[int, str, str]] = []
    manifest += [(slot, "character", name) for slot, (_, name) in enumerate(characters, 1)]
    manifest += [(slot, kind, name) for slot, (_, kind, name) in enumerate(images, 1)]

    return {
        "character_ids": [kie_id for kie_id, _ in characters],
        "image_urls": [url for url, _, _ in images],
        "audio_ids": audio_ids,
        "manifest": manifest,
    }
