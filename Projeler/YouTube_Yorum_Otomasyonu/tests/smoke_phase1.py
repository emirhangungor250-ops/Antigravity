# -*- coding: utf-8 -*-
"""Faz 1 read-only smoke testi — DB'ye YAZMAZ.

Doğrular: YouTube fetch, seed/rapor ayrımı, LLM sınıflama, HTML render, corpus sayımı.
Kullanım (proje kökünden):  python tests/smoke_phase1.py
"""
import os
os.environ.setdefault("YT_MAX_THREADS", "60")  # küçük örneklem

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core import youtube_client as YT
from core import db as DB
from core import llm
from core import mail_report

print(f"== Faz 1 smoke | kanal={config.CHANNEL_TITLE} | max_threads={config.MAX_THREADS_PER_RUN} ==")
miss = config.missing_phase1_keys()
print("eksik anahtar:", miss or "yok")

threads = YT.fetch_comment_threads()
print(f"çekilen thread: {len(threads)}")

seed = [t for t in threads if (not t.is_by_channel) and t.channel_replied and t.channel_reply_text.strip()]
print(f"corpus adayı (kanal cevaplamış): {len(seed)}")
if seed:
    s = seed[0]
    print(f"  örnek çift:\n   YORUM: {s.text[:80]!r}\n   KANAL: {s.channel_reply_text[:80]!r}")

cand = [t for t in threads if (not t.is_by_channel) and (not t.channel_replied)
        and t.text.strip() and YT.is_recent(t.published_at, config.COMMENT_LOOKBACK_DAYS)]
print(f"yeni cevaplanabilir (idempotency öncesi): {len(cand)}")

try:
    known = DB.known_comment_ids([t.comment_id for t in cand])
    print(f"DB'de zaten raporlanmış: {len(known)} (idempotency okuması çalışıyor)")
    cand = [t for t in cand if t.comment_id not in known]
except Exception as e:
    print(f"⚠️ DB known okuma hatası: {e}")

print(f"raporlanacak (idempotency sonrası): {len(cand)}")

sample = cand[:10]
if sample:
    print("\n-- LLM sınıflama (ilk 10) --")
    res = llm.classify_worth_batch([t.text for t in sample])
    for t, w in zip(sample, res):
        print(f"  [{w['kind']:>11} {w['score']:>3} {w['lang']}] {t.text[:60]!r}")

    titles = YT.resolve_video_titles([t.video_id for t in sample])
    cards = []
    for t, w in zip(sample, res):
        cards.append({
            "comment_id": t.comment_id, "video_id": t.video_id,
            "video_title": titles.get(t.video_id, ""), "author": t.author,
            "text": t.text, "like_count": t.like_count, "published_at": t.published_at,
            "worth_kind": w["kind"], "worth_score": w["score"], "lang": w["lang"],
        })
    cards.sort(key=lambda c: (c["worth_kind"] == "spam", -c["worth_score"]))
    html = mail_report.build_html(cards, total_new=len(cards), corpus_ready=False)
    out = "/tmp/yt_yorum_rapor_preview.html"
    open(out, "w", encoding="utf-8").write(html)
    print(f"\n📄 HTML önizleme yazıldı: {out} ({len(html)} byte)")
    print("   ilk kart derin link:", mail_report.deep_link(cards[0]["video_id"], cards[0]["comment_id"]))

try:
    print("\ncorpus toplam (DB):", DB.corpus_count())
except Exception as e:
    print("corpus_count hata:", e)

print("\n✅ smoke bitti (DB'ye yazılmadı)")
