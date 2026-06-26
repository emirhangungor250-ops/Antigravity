"""Teleprompter_Senkron — Notion "Çekime Hazır" script'lerini teleprompter klasörüne bırakır.

Akış (GitHub Actions cron veya lokal çalıştırma):
  1. Notion script DB'sinden Status = "Çekime Hazır" kartları çek.
  2. Adı boş VEYA gövdesi boş kartı atla.
  3. O kart için klasörde ZATEN bir dosya varsa (Doc da olsa) dokunma.
  4. Yoksa gövdeyi AI ile temizleyip "{gün} - {ad}.txt" olarak klasöre BIRAK.

Teleprompter uygulaması (ör. Nano Teleprompter, Android) Drive'a bağlanınca KENDİ klasörünü
açar, yalnızca onu iki yönlü senkronlar ve sahiplenir: bıraktığımız .txt'i Google Doc'a
çevirir, sildiğimizi geri getirir. Bu yüzden biz klasörü YÖNETMEYİZ — sadece yeni script'i
bir kez bırakırız. Eşleme dosya ADINA göredir (gün damgası ayıklanıp kart adına bakılır),
mükerrer önlenir. Silme/güncelleme uygulamanın işidir (detay: README).

Kullanım:
  python sync.py            # gerçek senkron
  python sync.py --dry-run  # ne yapılacağını yazar, Drive'a dokunmaz
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from core.cleaner import clean_script
from core.drive_auth import authed_email, drive_service
from core.drive_sync import create_file, list_files
from core.notion_source import fetch_body_text, fetch_ready_cards, notion_client

# Lokal: proje kökündeki .env'i yükle (Actions'ta yok, env zaten dolu).
_ENV_FILE = Path(__file__).resolve().parent / ".env"
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)

# Notion script DB'sinin ID'si. ZORUNLU — .env'e kendi DB ID'nizi yazın.
DB_ID = os.environ.get("PROMPTER_NOTION_DB_ID", "<NOTION_DB_ID>")
# Teleprompter uygulamasının Drive'da kendi açtığı klasörün ID'si. ZORUNLU.
# (Klasör adının sonunda boşluk olabilir; biz ID ile yazdığımız için sorun değil.)
FOLDER_ID = os.environ.get("PROMPTER_DRIVE_FOLDER_ID", "<GOOGLE_DRIVE_FOLDER_ID>")

_TR_AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
# Bizim koyduğumuz gün damgası: "7 Haziran - " (yıl yok, ay yazıyla). Eşlemede ayıklanır.
_DATE_PREFIX = re.compile(r"^\d{1,2} (?:" + "|".join(_TR_AYLAR) + r") - ")


def _today() -> str:
    """Bugünün gün damgası (İstanbul), '7 Haziran'. Dosya adının başına yazılır."""
    d = datetime.now(ZoneInfo("Europe/Istanbul"))
    return f"{d.day} {_TR_AYLAR[d.month - 1]}"


def _filename(added: str, name: str) -> str:
    """Gün damgalı dosya adı: '7 Haziran - Soru Cevap 1.txt'."""
    return f"{added} - {name}.txt"


def _base_name(filename: str) -> str:
    """Dosya adından .txt ve gün damgasını ayıkla -> kart adına eşle.

    Teleprompter uygulaması .txt'i Doc'a çevirip uzantıyı düşürür; biz de gün damgasını
    ekleriz. Bu yüzden 'Soru Cevap 1.txt', '7 Haziran - Soru Cevap 1' ve
    '7 Haziran - Soru Cevap 1.txt' hepsi -> 'Soru Cevap 1'.
    """
    n = filename[:-4] if filename.endswith(".txt") else filename
    n = _DATE_PREFIX.sub("", n)
    return n.strip()


def run(dry_run: bool = False) -> int:
    drive = drive_service()
    email = authed_email(drive)
    print(f"Drive hesabı: {email}")
    # Güvenlik kapısı: yanlış Google hesabına yazmayı önler. EXPECTED_DRIVE_DOMAIN
    # ayarlıysa, token o domain'e ait değilse hiçbir şey yazmadan durur. Boşsa kapı kapalı.
    expected = os.environ.get("EXPECTED_DRIVE_DOMAIN", "").strip()
    if expected and expected not in email:
        print(f"DURDU: beklenen '{expected}' hesabı değil, hiçbir şey yazılmadı.")
        return 1

    notion = notion_client()
    cards = fetch_ready_cards(notion, DB_ID)
    print(f"Çekime Hazır kart: {len(cards)}")

    files = list_files(drive, FOLDER_ID)
    present = {_base_name(f["name"]) for f in files}  # klasörde mevcut script adları

    created = exists = skipped = 0
    today = _today()

    for card in cards:
        name = (card.get("name") or "").strip()
        if not name:
            print("  atla: isimsiz kart")
            skipped += 1
            continue

        if name in present:  # bu kart için zaten dosya var — dokunma
            exists += 1
            continue

        body = fetch_body_text(notion, card["id"])
        if not body.strip():
            print(f"  atla: gövde boş — {name}")
            skipped += 1
            continue

        cleaned = clean_script(body)
        if not cleaned.strip():
            print(f"  atla: temizlenince boş kaldı — {name}")
            skipped += 1
            continue
        content = cleaned if cleaned.endswith("\n") else cleaned + "\n"

        want = _filename(today, name)
        if dry_run:
            print(f"  [BIRAK] {want} ({len(content)} karakter)")
        else:
            create_file(drive, FOLDER_ID, want, content)
            present.add(name)  # aynı koşuda mükerrer bırakma
            print(f"  bırakıldı: {want}")
        created += 1

    print(f"\nÖzet — bırakılan:{created} zaten-var:{exists} atlanan:{skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(run(dry_run="--dry-run" in sys.argv))
