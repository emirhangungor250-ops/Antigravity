"""Süre bütçeleri + deterministik bölüm onarımı (LLM çağrısı yok).

Senarist LLM'in ürettiği EpisodeScript burada bible'a karşı doğrulanır ve
kelime/satır/süre bütçeleri kod ile onarılır. Tüm onarımlar uyarı listesine yazılır.
"""
from typing import List, Tuple

from brain.schemas import EpisodeScript, SceneSpec

# süre (sn) → maks Türkçe kelime / maks diyalog satırı
BUDGETS = {
    4: {"words": 6, "lines": 1},
    6: {"words": 11, "lines": 2},
    8: {"words": 15, "lines": 2},
    10: {"words": 18, "lines": 3},
}

DURATION_STEPS = [4, 6, 8, 10]
MIN_TOTAL_S = 44
MAX_TOTAL_S = 60


def _step_down(duration: int) -> int:
    idx = DURATION_STEPS.index(duration)
    return DURATION_STEPS[idx - 1] if idx > 0 else duration


def _step_up(duration: int) -> int:
    idx = DURATION_STEPS.index(duration)
    return DURATION_STEPS[idx + 1] if idx < len(DURATION_STEPS) - 1 else duration


def _dialogue_words(scene: SceneSpec) -> int:
    return sum(len(line.line_tr.split()) for line in scene.dialogue)


def _enforce_budget(scene: SceneSpec, warnings: List[str]) -> None:
    """Satır sayısı ve kelime bütçesi aşımında son diyalog satırlarını siler."""
    budget = BUDGETS[scene.duration_s]
    while len(scene.dialogue) > budget["lines"]:
        dropped = scene.dialogue.pop()
        warnings.append(
            f"sahne {scene.scene_number}: satır bütçesi aşıldı "
            f"({budget['lines']} satır @ {scene.duration_s}sn), silindi: \"{dropped.line_tr}\""
        )
    while scene.dialogue and _dialogue_words(scene) > budget["words"]:
        dropped = scene.dialogue.pop()
        warnings.append(
            f"sahne {scene.scene_number}: kelime bütçesi aşıldı "
            f"({budget['words']} kelime @ {scene.duration_s}sn), silindi: \"{dropped.line_tr}\""
        )


def validate_and_repair(episode: EpisodeScript, bible: dict) -> Tuple[EpisodeScript, List[str]]:
    """Bible'a karşı id/speaker doğrulaması + deterministik süre/bütçe onarımı.

    Returns: (onarılmış kopya, uyarı listesi)
    """
    episode = episode.model_copy(deep=True)
    warnings: List[str] = []

    env_ids = {e["id"] for e in bible.get("environments", [])}
    char_ids = {c["id"] for c in bible.get("characters", [])}
    prop_ids = {p["id"] for p in bible.get("props", [])}
    narrator_enabled = bool(bible.get("narrator", {}).get("enabled"))

    # 1) id ve speaker doğrulaması
    for scene in episode.scenes:
        if scene.environment_id not in env_ids:
            warnings.append(
                f"sahne {scene.scene_number}: bilinmeyen environment_id '{scene.environment_id}'"
            )
        for cid in scene.character_ids:
            if cid not in char_ids:
                warnings.append(f"sahne {scene.scene_number}: bilinmeyen character_id '{cid}'")
        for pid in scene.prop_ids:
            if pid not in prop_ids:
                warnings.append(f"sahne {scene.scene_number}: bilinmeyen prop_id '{pid}'")

        kept = []
        for line in scene.dialogue:
            if line.speaker == "NARRATOR":
                if narrator_enabled:
                    kept.append(line)
                else:
                    warnings.append(
                        f"sahne {scene.scene_number}: narrator kapalı, NARRATOR satırı silindi: "
                        f"\"{line.line_tr}\""
                    )
            elif line.speaker in scene.character_ids:
                kept.append(line)
            else:
                warnings.append(
                    f"sahne {scene.scene_number}: speaker '{line.speaker}' sahnede yok, "
                    f"satır silindi: \"{line.line_tr}\""
                )
        scene.dialogue = kept

    # 2) sahne 1 = 4sn hook
    if episode.scenes and episode.scenes[0].duration_s != 4:
        warnings.append(
            f"sahne 1: hook süresi {episode.scenes[0].duration_s}sn → 4sn'e zorlandı"
        )
        episode.scenes[0].duration_s = 4

    # 3) kelime/satır bütçeleri
    for scene in episode.scenes:
        _enforce_budget(scene, warnings)

    # 4) toplam süre onarımı
    total = sum(s.duration_s for s in episode.scenes)
    while total > MAX_TOTAL_S:
        middles = [s for s in episode.scenes[1:-1] if s.duration_s > DURATION_STEPS[0]]
        if not middles:
            warnings.append(f"toplam {total}sn > {MAX_TOTAL_S}sn ama düşürülecek ara sahne kalmadı")
            break
        target = max(middles, key=lambda s: s.duration_s)
        old = target.duration_s
        target.duration_s = _step_down(old)
        warnings.append(
            f"toplam {total}sn > {MAX_TOTAL_S}sn: sahne {target.scene_number} "
            f"{old}sn → {target.duration_s}sn düşürüldü"
        )
        _enforce_budget(target, warnings)
        total = sum(s.duration_s for s in episode.scenes)

    if total < MIN_TOTAL_S:
        changed = True
        while total < MIN_TOTAL_S and changed:
            changed = False
            for scene in episode.scenes[1:-1]:
                if total >= MIN_TOTAL_S:
                    break
                if scene.duration_s < DURATION_STEPS[-1]:
                    old = scene.duration_s
                    scene.duration_s = _step_up(old)
                    total += scene.duration_s - old
                    changed = True
                    warnings.append(
                        f"toplam süre < {MIN_TOTAL_S}sn: sahne {scene.scene_number} "
                        f"{old}sn → {scene.duration_s}sn yükseltildi"
                    )
        if total < MIN_TOTAL_S:
            warnings.append(f"toplam {total}sn < {MIN_TOTAL_S}sn ama yükseltilecek ara sahne kalmadı")

    return episode, warnings
