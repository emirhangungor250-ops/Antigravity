# -*- coding: utf-8 -*-
"""Faz 2 cron girişi — yeni cevaplık yorumlara AI taslağı üret, onay mailine koy.

Gölge dönem (YT_AUTO_POST=0): hiçbir cevap otomatik yayınlanmaz; her taslak kanal sahibinin
mailden tek-tık onayından geçer (web/app.py). Öğrenme (corpus seed) Faz 1'deki gibi sürer.

Akış run() -> Faz 1 boru hattını yeniden kullanır (fetch + seed + reportable + classify + kapı),
sonra geçen her yoruma reply_writer ile taslak üretir, DB'ye yazar, maile koyar.
AUTO_POST açık + güven 'high' ise otomatik yayınlar (gölge dönemde kapalı).
"""
import sys

import config
from core import youtube_client as YT
from core import comment_pipeline as CP
from core import reply_writer as RW
from core import db as DB
from core import mail_report


def run() -> dict:
    log = {"fetched": 0, "seeded": 0, "reportable": 0, "drafted": 0,
           "auto_posted": 0, "corpus_total": 0, "cards": []}
    threads = YT.fetch_comment_threads()
    log["fetched"] = len(threads)

    # (A) öğrenme — Faz 1 ile aynı, her koşuda
    try:
        log["seeded"] = CP._seed_corpus(threads)
    except Exception as e:
        log["seed_error"] = str(e)[:200]

    # (B) rapor + taslak
    reportable = CP._reportable(threads)
    log["reportable"] = len(reportable)
    if not reportable:
        log["corpus_total"] = _corpus_total()
        return log

    all_cards = CP._classify_and_persist(reportable)            # hepsi DB'ye (status=reported)
    email_cards = [c for c in all_cards if CP.passes_quality_gate(c)]

    for c in email_cards:
        try:
            d = RW.generate_reply(c.get("text", ""), lang=c.get("lang"),
                                  video_title=c.get("video_title", ""))
        except Exception as e:
            c["draft_error"] = str(e)[:160]
            continue
        c["ai_confidence"] = d["confidence"]

        # Canlı (AUTO_POST) + yüksek güven -> otomatik yayınla. Gölge dönemde bu blok atlanır.
        if config.AUTO_POST_ENABLED and d["confidence"] == "high" and not config.DRY_RUN:
            try:
                YT.post_reply(c["comment_id"], d["reply"])
                DB.update_comment(c["comment_id"], {"status": "auto_replied", "ai_draft": d["reply"],
                                                    "ai_confidence": "high", "posted_reply": d["reply"]})
                c["auto_posted"] = True
                log["auto_posted"] += 1
                continue
            except Exception as e:
                c["draft_error"] = f"otomatik yayın hatası: {str(e)[:120]}"
                # düşerse taslağı onaya bırak (aşağı düş)

        # Gölge dönem: her taslağı onaya koy. Canlıda yalnız high/medium gösterilir, low elle.
        show_draft = (not config.AUTO_POST_ENABLED) or d["confidence"] in ("high", "medium")
        if show_draft:
            c["ai_draft"] = d["reply"]
        DB.update_comment(c["comment_id"], {"status": "drafted", "ai_draft": d["reply"],
                                            "ai_confidence": d["confidence"]})
        log["drafted"] += 1

    log["cards"] = email_cards
    log["corpus_total"] = _corpus_total()
    return log


def _corpus_total() -> int:
    try:
        return DB.corpus_count()
    except Exception:
        return 0


def main() -> int:
    missing = config.missing_phase1_keys()
    if missing:
        print(f"❌ Eksik anahtar(lar): {', '.join(missing)} — koşu iptal.")
        return 1

    print(f"=== YouTube Yorum Cevaplayıcı | Faz 2 | AUTO_POST={config.AUTO_POST_ENABLED} "
          f"| DRY_RUN={config.DRY_RUN} | kanal={config.CHANNEL_TITLE} ===")
    try:
        log = run()
    except Exception as e:
        print(f"❌ Koşu hatası: {e}")
        mail_report.send_failure_alert(str(e))
        return 1

    print(f"çekilen: {log['fetched']} | corpus+: {log['seeded']} | yeni: {log['reportable']} "
          f"| taslak: {log['drafted']} | oto-yayın: {log['auto_posted']} | corpus: {log['corpus_total']}")
    if "seed_error" in log:
        print(f"⚠️ corpus seed hatası: {log['seed_error']}")

    cards = log.get("cards", [])
    if not cards:
        print("Yeni cevaplık yorum yok — mail atılmıyor.")
        return 0

    corpus_ready = log["corpus_total"] >= config.CORPUS_READY_THRESHOLD
    mail_report.send_report(cards, total_new=len(cards), corpus_ready=corpus_ready)
    return 0


if __name__ == "__main__":
    sys.exit(main())
