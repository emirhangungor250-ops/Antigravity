"""Transkript düzeltme sözlüğü.

ASR'nin yanlış duyduğu marka/terimleri doğru yazıma çevirir. Veri data/glossary.json'da;
yeni hata görülünce oraya eklenir, kod değişmez.
"""
import json
import re
from functools import lru_cache

from config import GLOSSARY_PATH


@lru_cache(maxsize=1)
def _entries():
    data = json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))
    out = []
    for e in data.get("entries", []):
        canon = e["canonical"]
        # En uzun varyant önce gelsin ki "create ugc" "create"den önce yakalansın
        variants = sorted(set(e.get("variants", [])), key=len, reverse=True)
        for v in variants:
            if v.lower() == canon.lower():
                continue
            pat = re.compile(r"\b" + re.escape(v) + r"\b", re.IGNORECASE)
            out.append((pat, canon, v))
    return out


def apply_glossary(text: str):
    """Metni düzeltir. (düzeltilmiş_metin, [(yanlış, doğru, adet), ...]) döner."""
    if not text:
        return text, []
    applied = []
    for pat, canon, variant in _entries():
        text, n = pat.subn(canon, text)
        if n:
            applied.append((variant, canon, n))
    return text, applied
