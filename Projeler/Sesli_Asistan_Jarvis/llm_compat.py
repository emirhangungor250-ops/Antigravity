"""
llm_compat.py — thin Anthropic→OpenAI(OpenRouter) call shim for JARVIS.

The original repo called Anthropic's SDK as `client.messages.create(model=, max_tokens=,
system=, messages=)` and read `response.content[0].text`. We migrated the whole app to an
OpenAI-compatible client pointed at OpenRouter. To keep the migration minimal and uniform,
every former `X.messages.create(...)` call site now reads `chat(X, ...)` and every former
`.content[0].text` reads `.choices[0].message.content`.

`chat()` accepts the old `system=` kwarg and folds it into the OpenAI-style messages list,
so call sites did not have to be restructured.

Model tiers (override via env, one line each):
  JARVIS_MODEL        — main brain (conversation, research)   default: openai/gpt-4o-mini
  JARVIS_SMALL_MODEL  — fast/cheap (intent classify, summaries) default: openai/gpt-4o-mini

Defaults are intentionally cheap. Point them at any model your OpenRouter key can
reach (e.g. a stronger model for the main brain) by setting the env vars.
"""
import os

LLM_MODEL = os.getenv("JARVIS_MODEL", "openai/gpt-4o-mini")
LLM_SMALL_MODEL = os.getenv("JARVIS_SMALL_MODEL", "openai/gpt-4o-mini")


async def chat(client, *, model, messages, system=None, max_tokens=None, temperature=None, **kwargs):
    """Anthropic-style call shim over an openai.AsyncOpenAI (OpenRouter) client.

    Returns the OpenAI response object; read its text via
    `response.choices[0].message.content`.
    """
    msgs = list(messages)
    if system is not None:
        msgs = [{"role": "system", "content": system}] + msgs
    params = {"model": model, "messages": msgs}
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    if temperature is not None:
        params["temperature"] = temperature
    params.update(kwargs)
    return await client.chat.completions.create(**params)
