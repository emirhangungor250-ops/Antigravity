"""Sheet Tetikli Mail Yanıtlayıcı — ana giriş.

Kullanım:
  python3 main.py            # Tek tur, prod (cron ile uyumlu)
  python3 main.py --dry-run  # Mail gönderme, sadece taslakları yazdır
  python3 main.py --loop     # Sürekli polling (worker modu)
"""
from __future__ import annotations
import argparse
import re
import time
from datetime import datetime, timezone

from config import POLL_INTERVAL_SECONDS, DRY_RUN
import sheets_client
import mail_writer
import gmail_sender


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def process_once(dry_run: bool = False) -> dict:
    sheets_client.ensure_status_header()
    rows = sheets_client.fetch_pending_rows()
    summary = {"checked": len(rows), "sent": 0, "skipped": 0, "failed": 0}
    if not rows:
        print(f"[{_now_str()}] Bekleyen satır yok.")
        return summary

    for lead in rows:
        rid = lead["row_index"]
        email = lead.get("email", "").strip()
        name = (lead.get("name") or "").strip() or "?"
        if not email or not EMAIL_RE.match(email):
            print(f"  ⚠️  Satır {rid} ({name}): e-posta boş/geçersiz → atlandı.")
            sheets_client.mark_status(rid, f"⚠️ E-posta yok ({_now_str()})")
            summary["skipped"] += 1
            continue

        try:
            mail = mail_writer.generate_mail(lead)
        except Exception as e:
            print(f"  ❌ Satır {rid}: mail üretim hatası: {e}")
            summary["failed"] += 1
            continue

        if dry_run:
            print(f"\n--- DRY-RUN satır {rid} → {email} ---")
            print(f"Subject: {mail['subject']}")
            print(mail["body_text"])
            print("--- end ---\n")
            summary["sent"] += 1
            continue

        try:
            msg_id = gmail_sender.send_mail(email, mail["subject"], mail["body_text"])
            sheets_client.mark_status(rid, f"✅ Gönderildi {_now_str()} (id:{msg_id[:10]})")
            print(f"  ✉️  Satır {rid} → {email}: gönderildi (id:{msg_id[:10]})")
            summary["sent"] += 1
        except Exception as e:
            err = str(e)[:120]
            sheets_client.mark_status(rid, f"❌ Hata {_now_str()}: {err}")
            print(f"  ❌ Satır {rid} → {email}: {err}")
            summary["failed"] += 1

    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Mail gönderme, sadece göster")
    p.add_argument("--loop", action="store_true", help="Sürekli polling (worker modu)")
    args = p.parse_args()

    dry = args.dry_run or DRY_RUN

    if not args.loop:
        s = process_once(dry_run=dry)
        print(f"\n[özet] checked={s['checked']} sent={s['sent']} "
              f"skipped={s['skipped']} failed={s['failed']}")
        return

    print(f"[loop] polling her {POLL_INTERVAL_SECONDS}s — Ctrl+C ile durdur.")
    while True:
        try:
            process_once(dry_run=dry)
        except Exception as e:
            print(f"[loop] tur hatası: {e}")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
