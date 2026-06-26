"""Seri hafizasi: series_state.json icerigini bolum sonunda gunceller,
bir sonraki bolumun senaristine SINIRLI ozet metni uretir.

State semasi pipeline.state.load_series_state default'una birebir uyar.
"""
import re
from typing import List, Optional

from brain import client
from brain.schemas import EpisodeScript

RECENT_EPISODES_KEPT = 3
SUMMARY_WORD_LIMIT = 1500


def _next_thread_id(open_threads: List[dict]) -> str:
    max_n = 0
    for t in open_threads:
        m = re.match(r"t(\d+)$", str(t.get("id", "")))
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"t{max_n + 1:03d}"


def _words(text: str) -> set:
    return {w.lower().strip(".,!?;:\"'()") for w in str(text).split() if len(w) > 2}


def _fuzzy_match_thread(resolved_text: str, open_threads: List[dict]) -> Optional[dict]:
    """En yuksek kelime ortusmesine sahip acik thread'i bulur (esik 0.2)."""
    res_words = _words(resolved_text)
    best, best_score = None, 0.0
    for t in open_threads:
        if t.get("status") != "open":
            continue
        t_words = _words(t.get("text", ""))
        union = res_words | t_words
        score = len(res_words & t_words) / len(union) if union else 0.0
        if score > best_score:
            best, best_score = t, score
    return best if best_score >= 0.2 else None


def update_series_state(state: dict, episode: EpisodeScript) -> dict:
    mu = episode.memory_update

    # Idempotence: resume ayni bolumu ikinci kez uygulamasin (marker state ile atomic yazilir)
    applied = state.setdefault("applied_episodes", [])
    if episode.episode_number in applied:
        return state
    applied.append(episode.episode_number)

    state["episodes_produced"] = state.get("episodes_produced", 0) + 1

    recent = state.setdefault("recent_episodes", [])
    recent.append({
        "episode": episode.episode_number,
        "title_tr": episode.title_tr,
        "synopsis_short_tr": mu.synopsis_short_tr,
        "cliffhanger_tr": mu.cliffhanger_tr,
    })
    state["recent_episodes"] = recent[-RECENT_EPISODES_KEPT:]

    threads = state.setdefault("open_threads", [])
    for resolved in mu.threads_resolved:
        match = _fuzzy_match_thread(resolved, threads)
        if match is not None:
            match["status"] = "resolved"
            match["resolved_in_episode"] = episode.episode_number
    for opened in mu.threads_opened:
        threads.append({
            "id": _next_thread_id(threads),
            "text": opened,
            "status": "open",
            "opened_in_episode": episode.episode_number,
        })

    char_state = state.setdefault("character_state", {})
    for dev in mu.character_developments:
        if ":" in dev:
            key, rest = dev.split(":", 1)
            key, rest = key.strip(), rest.strip()
        else:
            key, rest = "genel", dev.strip()
        char_state.setdefault(key, []).append(f"B{episode.episode_number}: {rest}")

    canon = state.setdefault("canon_facts", [])
    for fact in mu.new_canon_facts:
        if fact not in canon:
            canon.append(fact)

    hooks = state.setdefault("used_hooks", [])
    if episode.hook_description and episode.hook_description not in hooks:
        hooks.append(episode.hook_description)

    synopses = [e["synopsis_short_tr"] for e in state["recent_episodes"]]
    if state["episodes_produced"] > 3:
        state["season_summary_tr"] = client.compress_season_summary(
            state.get("season_summary_tr", ""), synopses, canon
        )
    else:
        state["season_summary_tr"] = " ".join(synopses)

    return state


def build_series_state_summary(state: dict) -> str:
    """Bolum senaristinin promptuna enjekte edilecek sinirli metin (~1500 kelime tavan)."""
    if state.get("episodes_produced", 0) == 0:
        return (
            "This is the FIRST episode of the series. There is no prior state — "
            "establish the world, the characters and the central question."
        )

    parts = [
        f"EPISODES PRODUCED SO FAR: {state['episodes_produced']}",
        "",
        "SEASON SUMMARY:",
        state.get("season_summary_tr", "").strip() or "(yok)",
        "",
        "RECENT EPISODES (oldest to newest, verbatim):",
    ]
    for ep in state.get("recent_episodes", []):
        parts.append(
            f"- B{ep['episode']} \"{ep['title_tr']}\": {ep['synopsis_short_tr']} "
            f"| Cliffhanger: {ep['cliffhanger_tr']}"
        )

    open_threads = [t for t in state.get("open_threads", []) if t.get("status") == "open"]
    parts += ["", "OPEN THREADS (address or advance at least one):"]
    parts += [f"- ({t['id']}) {t['text']}" for t in open_threads] or ["- (none)"]

    parts += ["", "CANON FACTS (never contradict these):"]
    parts += [f"- {f}" for f in state.get("canon_facts", [])] or ["- (none)"]

    parts += ["", "CHARACTER STATE:"]
    char_state = state.get("character_state", {})
    if char_state:
        for char_id, devs in char_state.items():
            parts.append(f"- {char_id}: " + " / ".join(devs[-3:]))
    else:
        parts.append("- (none)")

    parts += ["", "USED HOOKS (do NOT repeat these opening hooks):"]
    parts += [f"- {h}" for h in state.get("used_hooks", [])] or ["- (none)"]

    text = "\n".join(parts)
    words = text.split(" ")
    if len(words) > SUMMARY_WORD_LIMIT:
        text = " ".join(words[:SUMMARY_WORD_LIMIT])
    return text
