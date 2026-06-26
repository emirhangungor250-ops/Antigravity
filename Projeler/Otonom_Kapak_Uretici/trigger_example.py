"""
trigger_example.py — Pipeline'i tek bir video icin manuel tetikleme ornegi.

Normalde main.py Notion'dan "hazir" videolari ceker. Bu script ise Notion'a
dokunmadan, elle tanimladiginiz tek bir video icin pipeline'i calistirir.
Test, demo veya tek seferlik uretim icin kullanilir.

Kullanim:
    python trigger_example.py
"""
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.logger import get_logger
from main import process_reels  # YouTube icin: from main import process_youtube

# TODO: Kendi videonuzun bilgilerini girin.
# - id: Notion sayfa ID'si (opsiyonel, mock'ta kullanilmaz)
# - name: video adi (Gemini'ye anlamli gelecek bir baslik)
# - drive_url: uretilen kapaklarin yuklenecegi Google Drive klasor linki
# - script_text: videonun senaryosu — temalar bu metinden uretilir
example_video = {
    "id": "<NOTION_PAGE_ID>",
    "name": "Ornek Video Basligi",
    "drive_url": "<GOOGLE_DRIVE_FOLDER_URL>",
    "script_text": "Buraya videonuzun senaryo metnini yazin. Kapak temalari "
                   "bu metnin icerigine gore uretilir, bu yuzden somut detaylar "
                   "(sayilar, fiyatlar, sureler) icermesi iyi sonuc verir.",
}


def fake_get_ready_videos(cover_type):
    if cover_type == "reels":
        return [example_video]
    return []


def fake_count_existing_covers(drive_url):
    # Her zaman 0 don — uretimi zorla
    return 0


@patch('main.get_ready_videos', fake_get_ready_videos)
@patch('main.count_existing_covers', fake_count_existing_covers)
def run():
    logger = get_logger("Otonom_Kapak_Example", level="INFO")
    logger.info("Tek video icin Reels pipeline tetikleniyor...")
    process_reels(logger)


if __name__ == "__main__":
    run()
