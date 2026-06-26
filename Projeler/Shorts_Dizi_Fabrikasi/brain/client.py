"""Anthropic istemcisi: structured-output (messages.parse) sarmalayicisi.

Tum LLM cagrilari buradan gecer. DRY_RUN'da hicbir API cagrisi yapilmaz;
fixture'lar doner. Her gercek cagrinin usage'i USAGE_LOG'a yazilir
(services.cost_tracker okur).
"""
import json
from pathlib import Path
from typing import List, Optional

import anthropic

from core.config import settings
from brain.schemas import (
    BiblePlan,
    EpisodeScript,
    SeasonSummary,
    SimplifiedPrompt,
    validate_bible_plan,
)

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

# Her cagri sonrasi {"model", "input_tokens", "output_tokens",
# "cache_creation_input_tokens", "cache_read_input_tokens"} eklenir.
USAGE_LOG: List[dict] = []

_anthropic_client: Optional[anthropic.Anthropic] = None

SIMPLIFY_SYSTEM = (
    "You rewrite video generation prompts that were rejected by a content policy filter. "
    "Keep the exact same story beat, characters, camera work, dialogue lines and output format, "
    "but remove or soften anything that could read as violent, sexual, branded, political, "
    "or otherwise sensitive. Return only the rewritten prompt."
)

COMPRESS_SYSTEM = (
    "You compress a Turkish mini-series rolling season summary. Merge the old summary and the "
    "recent episode synopses into ONE Turkish prose summary of at most 200 words. "
    "Preserve every canon fact you are given. No lists, no headers, plain prose."
)


def _client() -> anthropic.Anthropic:
    """Lazy istemci — DRY_RUN'da API key gerekmesin."""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _anthropic_client


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _load_fixture(name: str) -> dict:
    path = FIXTURES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"DRY_RUN fixture eksik: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _log_usage(model: str, response) -> None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    USAGE_LOG.append({
        "model": model,
        "input_tokens": getattr(usage, "input_tokens", 0) or 0,
        "output_tokens": getattr(usage, "output_tokens", 0) or 0,
        "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
        "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
    })


def _parse(schema, system_text: str, user_text: str, model: str = None, max_tokens: int = 16000):
    """messages.parse + 1 repair re-ask. temperature/top_p ASLA gonderilmez (Opus 4.8'de 400)."""
    model = model or settings.BRAIN_MODEL
    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}],
        output_format=schema,
    )
    # Haiku 4.5 adaptive thinking desteklemiyor; opus/sonnet'te adaptive zorunlu tercih.
    if "haiku" not in model:
        kwargs["thinking"] = {"type": "adaptive"}

    last_err = None
    text = user_text
    for _ in range(2):
        try:
            response = _client().messages.parse(
                messages=[{"role": "user", "content": text}], **kwargs
            )
        except anthropic.APIError:
            raise
        except Exception as e:  # pydantic dogrulama / JSON parse hatasi
            last_err = f"schema validation failed: {e}"
            text = (
                f"{user_text}\n\nPREVIOUS ATTEMPT FAILED: {last_err}\n"
                "Fix the issue and return output that matches the schema exactly."
            )
            continue

        _log_usage(model, response)

        if response.stop_reason == "refusal":
            last_err = "model refused the request"
        else:
            parsed = response.parsed_output
            if parsed is not None:
                return parsed
            last_err = f"no parsed output (stop_reason={response.stop_reason})"

        text = (
            f"{user_text}\n\nPREVIOUS ATTEMPT FAILED: {last_err}\n"
            "Fix the issue and return output that matches the schema exactly."
        )

    raise RuntimeError(f"LLM structured output failed after repair retry: {last_err}")


# ─── Dizi kitabi ──────────────────────────────────────────────────────────

def build_series_bible_plan(scenario_text: str, notes: str = "") -> BiblePlan:
    if settings.IS_DRY_RUN:
        return BiblePlan.model_validate(_load_fixture("bible_plan.json"))

    system_text = _load_prompt("bible_system.md")
    user_text = f"SENARYO:\n{scenario_text}\n\nOpsiyonel notlar: {notes}"

    plan = _parse(BiblePlan, system_text, user_text)
    errors = validate_bible_plan(plan)
    if errors:
        repair_text = (
            f"{user_text}\n\nYOUR PREVIOUS PLAN HAD THESE PROBLEMS — fix ALL of them:\n- "
            + "\n- ".join(errors)
        )
        plan = _parse(BiblePlan, system_text, repair_text)
        errors = validate_bible_plan(plan)
        if errors:
            raise RuntimeError(f"Bible plan failed semantic validation twice: {errors}")
    return plan


# ─── Bolum senaryosu ──────────────────────────────────────────────────────

def write_episode(
    bible_compact: str,
    series_state_summary: str,
    episode_no: int,
    episode_seed: str,
    konu: str = "",
) -> EpisodeScript:
    if settings.IS_DRY_RUN:
        data = _load_fixture("episode_script.json")
        data["episode_number"] = episode_no
        return EpisodeScript.model_validate(data)

    system_text = _load_prompt("episode_system.md")
    # Cache-dostu sira: stabil icerik (bible) once, degisken icerik sonra.
    user_text = (
        f"SERIES BIBLE (compact JSON):\n{bible_compact}\n\n"
        f"SERIES STATE:\n{series_state_summary}\n\n"
        f"EPISODE NUMBER: {episode_no}\n"
        f"EPISODE SEED (from series arc): {episode_seed}\n"
        f"PRODUCER STEER: {konu if konu else '(none — follow the seed)'}"
    )
    return _parse(EpisodeScript, system_text, user_text)


# ─── Yardimci cagrilar ────────────────────────────────────────────────────

def simplify_scene_prompt(prompt: str, fail_msg: str) -> str:
    """Policy reddi yiyen sahne promptunu ayni hikaye beat'iyle sadeleştirir."""
    if settings.IS_DRY_RUN:
        return prompt

    user_text = (
        f"ORIGINAL PROMPT:\n{prompt}\n\n"
        f"REJECTION MESSAGE:\n{fail_msg}\n\n"
        "Rewrite the prompt to be policy-safe while keeping the same story beat."
    )
    result = _parse(SimplifiedPrompt, SIMPLIFY_SYSTEM, user_text, max_tokens=4000)
    return result.prompt


def compress_season_summary(
    old_summary: str, recent_synopses: List[str], canon_facts: List[str]
) -> str:
    """Sezon ozetini ≤200 kelimeye sikistirir (haiku)."""
    if settings.IS_DRY_RUN:
        combined = " ".join([old_summary] + list(recent_synopses)).split()
        return " ".join(combined[:200])

    user_text = (
        f"OLD SEASON SUMMARY:\n{old_summary or '(empty)'}\n\n"
        "RECENT EPISODE SYNOPSES:\n- " + "\n- ".join(recent_synopses) + "\n\n"
        "CANON FACTS (must all survive):\n- " + "\n- ".join(canon_facts or ["(none)"])
    )
    result = _parse(
        SeasonSummary, COMPRESS_SYSTEM, user_text,
        model=settings.QC_MODEL, max_tokens=2000,
    )
    return result.summary_tr
