# -*- coding: utf-8 -*-
"""YouTube Yorum Otomasyonu — Faz 1 cron girişi.

Günlük: yorumları çek -> öğrenme corpus'unu besle -> yeni cevaplanabilir yorumları
mail raporu olarak rapor alıcısına at. Faz 2 (AI cevaplama) generate.py'de.
"""
import sys

import config
from core import comment_pipeline
from core import mail_report


def main() -> int:
    if config.PHASE >= 2:
        # Faz 2: AI taslak + onay akışı generate.py'de. Cron komutu değişmeden YT_PHASE=2 yeter.
        from generate import main as _gen_main
        return _gen_main()
    missing = config.missing_phase1_keys()
    if missing:
        print(f"❌ Eksik anahtar(lar): {', '.join(missing)} — koşu iptal.")
        return 1

    print(f"=== YouTube Yorum Cevaplayıcı | Faz {config.PHASE} | DRY_RUN={config.DRY_RUN} "
          f"| kanal={config.CHANNEL_TITLE} ===")

    try:
        log = comment_pipeline.run()
    except Exception as e:
        # Sessiz kalma: koşu çökerse mail hiç gelmemek yerine alıcı kısa bir uyarı alsın.
        # Teknik sebep loga gider, maile değil.
        print(f"❌ Koşu hatası: {e}")
        mail_report.send_failure_alert(str(e))
        return 1
    print(f"çekilen thread: {log['fetched']} | corpus'a eklenen: {log['seeded']} "
          f"| yeni yorum: {log['reportable']} | maile giren: {len(log.get('cards', []))} "
          f"| elenen (düşük değer): {log.get('filtered_out', 0)} | corpus toplam: {log['corpus_total']}")
    if "seed_error" in log:
        print(f"⚠️ corpus seed hatası: {log['seed_error']}")

    cards = log.get("cards", [])
    if not cards:
        if log.get("classified"):
            print(f"{log['classified']} yeni yorum vardı ama hiçbiri cevaplamaya değer eşiğini geçmedi, mail atılmıyor.")
        else:
            print("Yeni cevaplanabilir yorum yok, mail atılmıyor.")
        return 0

    corpus_ready = log["corpus_total"] >= config.CORPUS_READY_THRESHOLD
    mail_report.send_report(cards, total_new=len(cards), corpus_ready=corpus_ready)
    return 0


if __name__ == "__main__":
    sys.exit(main())
