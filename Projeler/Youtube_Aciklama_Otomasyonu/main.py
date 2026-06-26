"""YT_Aciklama_Otomasyonu — main orchestrator.

Cron her 15 dakikada bir çalışır. Yayınlanmış YouTube iş birliği videolarına
otomatik açıklama yazar, Drive klasörlerine Google Docs olarak bırakır.

Akış:
  1. Notion DB'den Durum='Yayınlandı' + URL + Drive dolu satırları çek
  2. Her satır için Drive'da Aciklama_Taslagi*.gdoc varsa atla
  3. YouTube transcript'i çek (yoksa atla + Notion'a not düş)
  4. Claude ile açıklama + chapter üret
  5. Brand affiliate map'ten link çek
  6. Drive klasörüne yeni Doc yarat
  7. Notion sayfasının altına başarı bloğu ekle, Telegram'a bildirim at
"""

import json
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent.parent / "_knowledge" / "credentials" / "master.env")

# Tüm modüller env'i yükleyebilsin diye load_dotenv'den SONRA import
from core import notion_service, transcript_service, description_builder, google_docs_service  # noqa: E402

BRAND_AFFILIATES_PATH = ROOT / "data" / "brand_affiliates.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")


def send_telegram(text: str) -> None:
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": True},
            timeout=15,
        )
    except Exception as e:
        print(f"[telegram] hata: {e}")


def _load_affiliates() -> dict[str, str]:
    if not BRAND_AFFILIATES_PATH.exists():
        return {}
    with open(BRAND_AFFILIATES_PATH, encoding="utf-8") as f:
        return json.load(f)


def _guess_brand_from_text(*texts: str, affiliates: dict[str, str]) -> str | None:
    """Title / brief / URL'de affiliate marka adı geçiyor mu — basit substring tarama (Claude fallback)."""
    combined = " ".join(t for t in texts if t).lower()
    for brand in affiliates:
        if brand.lower() in combined:
            return brand
    return None


def _slugify(text: str, maxlen: int = 60) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "_", text.strip())
    return text[:maxlen] or "Video"


def process_one(video: dict) -> dict:
    """Tek videoyu işle. Sonuç dict döndür (status: 'created' | 'skipped' | 'error')."""
    page_id = video["page_id"]
    name = video["video_name"]
    url = video["video_url"]
    drive_url = video["drive_url"]

    print(f"\n— işleniyor: {name}")

    # 1. Drive folder ID
    folder_id = google_docs_service.extract_folder_id(drive_url)
    if not folder_id:
        msg = f"Drive URL parse edilemedi: {drive_url}"
        notion_service.append_status_block(page_id, msg, is_error=True)
        return {"status": "error", "msg": msg}

    # 2. Idempotency — Drive'da Aciklama_Taslagi var mı?
    existing = google_docs_service.find_existing_draft(folder_id)
    if existing:
        print(f"  idempotent skip — mevcut Docs: {existing}")
        return {"status": "skipped", "doc_link": existing}

    # 3. Transcript (varsa)
    video_id = transcript_service.extract_video_id(url)
    if not video_id:
        msg = f"YouTube video ID çıkarılamadı: {url}"
        notion_service.append_status_block(page_id, msg, is_error=True)
        return {"status": "error", "msg": msg}
    segments = transcript_service.fetch_transcript(video_id)
    transcript_text = transcript_service.format_for_prompt(segments) if segments else ""
    duration = transcript_service.total_duration_seconds(segments) if segments else 0

    # 4. Brief / Notion sayfa içeriği (her zaman çek)
    brief_body = notion_service.get_page_content(page_id)

    # 5. Transcript yoksa: YT Data API'den süre + Notion içeriği fallback
    if not segments:
        duration = transcript_service.fetch_youtube_duration(video_id) or 0
        if not brief_body or len(brief_body) < 200:
            msg = (
                "Transcript yok ve Notion sayfa içeriği yetersiz (<200 char). "
                "Videoyu public yap veya sahne sahne script ekle."
            )
            notion_service.append_status_block(page_id, msg, is_error=True)
            return {"status": "error", "msg": msg}
        print(f"  ⚠ transcript yok — Notion script fallback (duration={duration}s, brief={len(brief_body)} char)")

    # 5. Claude ile üret
    try:
        ai_out = description_builder.build_description(
            video_name=name,
            video_url=url,
            brief=brief_body,
            transcript_with_timestamps=transcript_text,
            duration_sec=duration,
        )
    except Exception as e:
        msg = f"Claude üretim hatası: {e}"
        traceback.print_exc()
        notion_service.append_status_block(page_id, msg, is_error=True)
        return {"status": "error", "msg": msg}

    # 6. Affiliate link tespiti
    affiliates = _load_affiliates()
    brand_key = (ai_out.get("marka_anahtari") or "").strip().lower()
    if brand_key not in affiliates:
        brand_key = _guess_brand_from_text(name, brief_body, affiliates=affiliates) or ""
    affiliate_link = affiliates.get(brand_key) if brand_key else None
    if brand_key:
        print(f"  marka: {brand_key}  →  {affiliate_link}")

    # 7. Birleştir
    final_text = description_builder.assemble_final_description(
        ai_output=ai_out, affiliate_link=affiliate_link
    )

    # 8. Drive'a Docs olarak yaz
    doc_name = f"Aciklama_Taslagi_{_slugify(name)}_{datetime.now().strftime('%Y%m%d')}"
    html = google_docs_service.build_html(title=name, description_text=final_text)
    try:
        file = google_docs_service.create_doc_in_folder(folder_id, doc_name, html)
    except Exception as e:
        msg = f"Drive Docs üretim hatası: {e}"
        traceback.print_exc()
        notion_service.append_status_block(page_id, msg, is_error=True)
        return {"status": "error", "msg": msg}

    doc_link = file.get("webViewLink") or f"https://docs.google.com/document/d/{file['id']}"
    print(f"  ✅ Docs: {doc_link}")

    # 9. Notion'a not düş
    notion_service.append_status_block(
        page_id,
        f"{doc_link}  (chapter: {len(ai_out.get('chapters', []))}, marka: {brand_key or '—'})",
        is_error=False,
    )

    # 10. Telegram
    send_telegram(f"✅ YouTube açıklama hazır\n{name}\n{doc_link}")

    return {"status": "created", "doc_link": doc_link, "name": name}


def main() -> int:
    videos = notion_service.get_published_videos()
    if not videos:
        print("İşlenecek video yok.")
        return 0

    summary = {"created": 0, "skipped": 0, "error": 0}
    for v in videos:
        try:
            r = process_one(v)
            summary[r["status"]] = summary.get(r["status"], 0) + 1
        except Exception as e:
            traceback.print_exc()
            summary["error"] += 1
            print(f"  beklenmedik hata: {e}")

    print(f"\nÖzet: {summary}")
    if summary["error"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
