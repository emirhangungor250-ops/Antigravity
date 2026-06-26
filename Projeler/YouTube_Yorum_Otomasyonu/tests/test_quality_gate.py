# -*- coding: utf-8 -*-
"""Kalite kapısı birim testi — AĞ YOK, API YOK (saf fonksiyon).

Doğrular: mail raporuna SADECE cevaplamaya değer yorumlar girer (soru/dolu + skor >= eşik);
kısa övgü/emoji/spam ve düşük skorlu muğlak sorular elenir. Bu sabahki (2026-06-08) gerçek
çöp yorumlar ("Nerde nasıl", "Ben biliyom", "Slma") regresyon vakası olarak gömülü.

Kullanım (proje kökünden):  python tests/test_quality_gate.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core.comment_pipeline import passes_quality_gate


def _card(kind, score):
    return {"worth_kind": kind, "worth_score": score}


THR = config.REPORT_MIN_SCORE

CASES = [
    # (açıklama, kart, maile girmeli mi)
    ("açık soru, yüksek skor",              _card("question", 88),     True),
    ("dolu yorum, eşik üstü",               _card("substantive", 70),  True),
    ("dolu yorum, tam eşikte",              _card("substantive", THR), True),
    ("LLM fail-open varsayımı (60) geçer",  _card("substantive", 60),  True),
    ("'Nerde nasıl' (muğlak soru)",         _card("question", 30),     False),
    ("'Ben biliyom' (anlamsız)",            _card("emoji_only", 10),   False),
    ("'Slma' (selam)",                      _card("emoji_only", 8),    False),
    ("kısa övgü, düşük skor",               _card("praise", 30),       False),
    ("kısa övgü yüksek skorlu olsa bile",   _card("praise", 95),       False),  # kind elenir
    ("spam",                                _card("spam", 0),          False),
    ("eşiğin 1 altı soru",                  _card("question", THR - 1), False),
]


def main():
    fails = 0
    for desc, card, expected in CASES:
        got = passes_quality_gate(card)
        ok = got == expected
        fails += 0 if ok else 1
        print(f"  {'✅' if ok else '❌ HATA':<7} [{'GİRER' if got else 'ELENİR':<6}] {desc}")
    print(f"\neşik={THR}, kabul edilen türler={sorted(config.REPORT_KINDS)}")
    if fails:
        print(f"❌ {fails} vaka başarısız")
        return 1
    print(f"✅ {len(CASES)} vaka geçti — kalite kapısı doğru çalışıyor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
