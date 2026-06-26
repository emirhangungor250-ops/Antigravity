# -*- coding: utf-8 -*-
"""Faz 2 TUR A önizleme — gerçek yorumlara AI taslakları üret, YouTube'a YAZMA.

Son yorumları çeker, en cevaplık birkaçını seçer, reply_writer ile kanal sahibinin
sesinde taslak üretir ve few-shot örnekleriyle ekrana basar.
DB'ye ve YouTube'a DOKUNMAZ (salt okuma + LLM).
Kullanım (proje kökünden):  python tests/preview_drafts.py [adet]
"""
import os
import sys

os.environ.setdefault("YT_MAX_THREADS", "120")  # küçük örneklem (hızlı önizleme)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core import youtube_client as YT
from core import llm
from core import comment_pipeline as CP
from core import reply_writer as RW

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3

print(f"== Faz 2 taslak önizleme | kanal={config.CHANNEL_TITLE} | corpus few-shot ==")
print("eksik anahtar:", config.missing_phase1_keys() or "yok")

threads = YT.fetch_comment_threads()
cand = [t for t in threads
        if (not t.is_by_channel) and (not t.channel_replied) and len(t.text.strip()) > 15]
print(f"çekilen thread: {len(threads)} | aday yorum (izleyici, cevapsız, dolu): {len(cand)}")
if not cand:
    print("uygun yorum yok — önizleme yapılamadı")
    sys.exit(0)

sample = cand[:40]
worth = llm.classify_worth_batch([t.text for t in sample])
ranked = sorted(zip(sample, worth), key=lambda x: -x[1]["score"])
picks = [(t, w) for t, w in ranked
         if CP.passes_quality_gate({"worth_kind": w["kind"], "worth_score": w["score"]})][:N]
if not picks:                       # kalite kapısını geçen yoksa en yüksek skorluları göster
    picks = ranked[:N]

titles = YT.resolve_video_titles([t.video_id for t, _ in picks])
for i, (t, w) in enumerate(picks, 1):
    print("\n" + "=" * 72)
    print(f"[{i}] {t.author} · {w['kind']} {w['score']} · 📺 {titles.get(t.video_id, '')[:50]}")
    print(f"    YORUM: {t.text.strip()[:220]!r}")
    out = RW.generate_reply(t.text, lang=w["lang"], video_title=titles.get(t.video_id, ""))
    ex = out["examples"]
    print(f"    benzer geçmiş cevap: {len(ex)} (en yüksek benzerlik {out['top_similarity']:.2f})")
    for e in ex[:2]:
        print(f"      ~ \"{(e.get('comment_text') or '')[:48]}\" -> \"{(e.get('reply_text') or '')[:48]}\"")
    print(f"    ── TASLAK [güven: {out['confidence']}] ─────────────")
    print(f"    {out['reply']}")

print("\n✅ önizleme bitti (YouTube'a ve DB'ye yazılmadı)")
