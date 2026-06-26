"""Self-improvement hafızası (chat-driven).

agents/learnings.md: ManyChat akışı üretiminde uyulacak damıtılmış tarz kuralları; her üretim
prompt'una enjekte edilir. Kullanıcı feedback verir, bu dosya elle güncellenir
(Notion satırı okuma yok).
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEARNINGS_PATH = PROJECT_ROOT / "agents" / "learnings.md"


def load_learnings() -> str:
    if LEARNINGS_PATH.exists():
        return LEARNINGS_PATH.read_text(encoding="utf-8")
    return ""
