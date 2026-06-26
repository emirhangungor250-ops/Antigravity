# -*- coding: utf-8 -*-
"""Faz 1 boru hattı — yorumları çek, corpus besle, rapor kartlarını üret.

İki iş tek taramadan:
  (A) ÖĞRENME: kanalın zaten cevapladığı thread'ler -> (yorum, kanal sahibi cevabı) çifti corpus'a.
  (B) RAPOR: izleyici yazmış + kanal henüz cevaplamamış + yeni + raporlanmamış yorumlar -> mail.

Kör otomasyon yasağı: "cevaplanmaya değerlik" yargısı LLM ile (llm.classify_worth_batch).
"""
from __future__ import annotations

from core import youtube_client as YT
from core import corpus as CORPUS
from core import db as DB
from core import llm

import config

WORTH_CHUNK = 20


def passes_quality_gate(card: dict) -> bool:
    """Mail kalite kapısı: yorum cevaplamaya değer mi?
    Geçemeyen (kısa övgü/emoji/spam ya da düşük skorlu) yorumlar DB'ye + corpus'a YİNE yazılır,
    sadece günlük mail raporuna girmez. Tek tanım: hem run() hem birim test buradan okur."""
    return (
        card.get("worth_kind") in config.REPORT_KINDS
        and (card.get("worth_score") or 0) >= config.REPORT_MIN_SCORE
    )


def _seed_corpus(threads: list[YT.CommentThread]) -> int:
    """(A) Kanalın cevapladığı thread'lerden öğrenme çiftleri üret, corpus'a yaz."""
    candidates = []
    for t in threads:
        if t.is_by_channel:
            continue                      # kendi yorumumuz değil
        if not t.channel_replied:
            continue                      # kanal sahibi cevaplamamış -> öğrenecek bir şey yok
        reply = t.channel_reply_text.strip()
        if not reply or not t.text.strip():
            continue
        candidates.append(t)
    if not candidates:
        return 0

    have = CORPUS.existing_corpus_ids([t.comment_id for t in candidates])
    fresh = [t for t in candidates if t.comment_id not in have]
    if not fresh:
        return 0

    pairs = [{
        "comment_id": t.comment_id,
        "comment_text": t.text.strip(),
        "reply_text": t.channel_reply_text.strip(),
        "video_id": t.video_id,
        "video_title": "",
        "lang": llm._guess_lang(t.text),
        "source": "native",
    } for t in fresh]
    return CORPUS.seed_pairs(pairs)


def _reportable(threads: list[YT.CommentThread]) -> list[YT.CommentThread]:
    """(B) Rapora girecek yeni yorumları süz (idempotency dahil)."""
    cand = [
        t for t in threads
        if not t.is_by_channel
        and not t.channel_replied
        and t.text.strip()
        and YT.is_recent(t.published_at, config.COMMENT_LOOKBACK_DAYS)
    ]
    if not cand:
        return []
    known = DB.known_comment_ids([t.comment_id for t in cand])
    return [t for t in cand if t.comment_id not in known]


def _classify_and_persist(threads: list[YT.CommentThread]) -> list[dict]:
    """LLM ile sınıfla, yt_comments'e yaz, kart sözlükleri döndür (skor sıralı)."""
    titles = YT.resolve_video_titles([t.video_id for t in threads])

    worth_by_id: dict[str, dict] = {}
    for i in range(0, len(threads), WORTH_CHUNK):
        chunk = threads[i:i + WORTH_CHUNK]
        results = llm.classify_worth_batch([t.text for t in chunk])
        for t, w in zip(chunk, results):
            worth_by_id[t.comment_id] = w

    cards = []
    rows = []
    for t in threads:
        w = worth_by_id.get(t.comment_id, {"kind": "substantive", "score": 60, "lang": llm._guess_lang(t.text)})
        card = {
            "comment_id": t.comment_id,
            "video_id": t.video_id,
            "video_title": titles.get(t.video_id, ""),
            "author": t.author,
            "text": t.text,
            "like_count": t.like_count,
            "published_at": t.published_at,
            "worth_kind": w["kind"],
            "worth_score": w["score"],
            "lang": w["lang"],
        }
        cards.append(card)
        rows.append({
            "comment_id": t.comment_id,
            "video_id": t.video_id,
            "video_title": titles.get(t.video_id, ""),
            "author": t.author,
            "author_channel": t.author_channel,
            "text": t.text,
            "lang": w["lang"],
            "like_count": t.like_count,
            "published_at": t.published_at or None,
            "worth_kind": w["kind"],
            "worth_score": w["score"],
            "status": "reported",
        })

    DB.upsert_comments(rows)
    # spam en dibe, sonra skora göre yüksekten düşüğe
    cards.sort(key=lambda c: (c["worth_kind"] == "spam", -c["worth_score"]))
    return cards


def run() -> dict:
    log = {"fetched": 0, "seeded": 0, "reportable": 0, "corpus_total": 0, "cards": []}
    threads = YT.fetch_comment_threads()
    log["fetched"] = len(threads)

    # (A) öğrenme — pasif, her koşuda
    try:
        log["seeded"] = _seed_corpus(threads)
    except Exception as e:
        log["seed_error"] = str(e)[:200]

    # (B) rapor — sınıfla + DB'ye yaz (hepsi), maile SADECE kalite eşiğini geçenler
    reportable = _reportable(threads)
    log["reportable"] = len(reportable)
    if reportable:
        all_cards = _classify_and_persist(reportable)   # hepsi DB'ye + corpus öğrenmesine akar
        email_cards = [c for c in all_cards if passes_quality_gate(c)]
        log["classified"] = len(all_cards)
        log["filtered_out"] = len(all_cards) - len(email_cards)
        log["cards"] = email_cards

    try:
        log["corpus_total"] = DB.corpus_count()
    except Exception:
        log["corpus_total"] = 0
    return log
