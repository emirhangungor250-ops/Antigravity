"""LinkedIn Text Paylaşım — orkestratör.

Pazartesi: Haftanın AI Haberleri  (Source: "LinkedIn Haber")
Perşembe: Haftalık AI Tavsiyesi   (Source: "LinkedIn Tavsiye")

Pipeline (her iki gün için aynı):
  Schedule → Perplexity → GPT-4.1 (post text) → GPT-4.1-mini (image prompt)
  → Kie AI (görsel) → Typefully (LinkedIn-only draft) → Notion log

Yayın artık burada olmuyor. Twitter projesi sabah summary mail'ini gönderiyor
(aynı DB query'si LinkedIn draft'larını da topluyor) — yönetici mail'deki
"Onayla ve yayına al" butonuna basınca twitter-onay-api Typefully draft'ı
publish_at:next-free-slot ile schedule ediyor; Typefully LinkedIn'e yayınlıyor.
"""

import logging
import os
import time

import schedule

from logger import setup_logging
from ops_logger import get_ops_logger, wait_all_loggers
from core.researcher import Researcher
from core.post_writer import PostWriter
from core.image_generator import ImageGenerator
from core.typefully_publisher import TypefullyDraftPublisher, TypefullyDraftError
from core.notion_logger import NotionLogger

ops = get_ops_logger("LinkedIn_Text_Paylasim", "Pipeline")


# Eski post_type → yeni Source/Title eşleşmesi (Notion DB için)
_FLOW_MAP = {
    "haber": {
        "source": "LinkedIn Haber",
        "title_prefix": "LinkedIn Haftalık Haber",
        "research_fn": "research_weekly_news",
        "writer_fn": "write_weekly_news_post",
    },
    "tavsiye": {
        "source": "LinkedIn Tavsiye",
        "title_prefix": "LinkedIn Haftalık Tavsiye",
        "research_fn": "research_weekly_tip",
        "writer_fn": "write_weekly_tip_post",
    },
}


def _run_flow(kind: str) -> None:
    """Ortak pipeline; kind = 'haber' veya 'tavsiye'."""
    flow = _FLOW_MAP[kind]
    source = flow["source"]
    title_prefix = flow["title_prefix"]

    ops.info("Workflow Başladı", f"{title_prefix} pipeline'ı")
    notion_logger = NotionLogger()

    if notion_logger.is_already_posted_this_week(source):
        ops.info("Duplicate Atlandı", f"Bu hafta zaten {source} draft/onay var")
        return

    image_path = None
    try:
        # 1) Araştırma
        researcher = Researcher()
        ops.info("Adım 1/4", f"Perplexity: {source} araştırması")
        research_content = getattr(researcher, flow["research_fn"])()
        ops.info("Araştırma Tamamlandı", f"{len(research_content)} char")

        # 2) Post yazımı
        writer = PostWriter()
        ops.info("Adım 2/4", "GPT-4.1: LinkedIn post metni")
        post_text = getattr(writer, flow["writer_fn"])(research_content)
        ops.info("Post Yazıldı", f"{len(post_text)} char")

        # 3) Görsel
        img_gen = ImageGenerator()
        ops.info("Adım 3/4", "Kie AI: görsel üretimi")
        image_path = img_gen.generate_post_image(post_text)
        if not image_path:
            raise RuntimeError("Görsel üretilemedi — görselsiz LinkedIn postu atılmaz")

        # 4) Typefully LinkedIn-only draft + Notion log
        publisher = TypefullyDraftPublisher()
        ops.info("Adım 4/4", "Typefully'ye LinkedIn-only draft yükleniyor")
        draft = publisher.create_linkedin_only_draft(text=post_text, image_path=image_path)

        notion_logger.log_draft(
            source=source,
            score=10,  # LinkedIn pipeline'ı zaten kuratör — tüm draft'lar yayına aday
            linkedin_text=post_text,
            draft_url=draft.get("share_url", ""),
            draft_id=draft.get("draft_id", ""),
            title=f"{title_prefix} (draft)",
        )
        ops.success("Workflow Tamamlandı", f"{source} draft yüklendi: {draft.get('share_url','')}")

    except TypefullyDraftError as e:
        ops.error(f"Typefully error", message=str(e))
        notion_logger.log_failed(source=source, error=str(e), title=f"{title_prefix} (failed)")
    except Exception as e:
        ops.error(f"FATAL: {title_prefix}", exception=e, message=str(e)[:500])
        try:
            notion_logger.log_failed(source=source, error=str(e)[:2000],
                                     title=f"{title_prefix} (failed)")
        except Exception:
            pass
    finally:
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
                logging.info(f"Geçici görsel silindi: {image_path}")
            except Exception:
                pass


def run_weekly_news():
    _run_flow("haber")


def run_weekly_tip():
    _run_flow("tavsiye")


if __name__ == "__main__":
    setup_logging()

    from datetime import datetime, timezone
    mode = os.environ.get("RUN_MODE", "cron").lower()

    if mode == "schedule":
        ops.info("Başlatıldı", "SCHEDULE mode (local dev)")
        schedule.every().monday.at("08:00").do(run_weekly_news)
        schedule.every().thursday.at("08:00").do(run_weekly_tip)
        while True:
            schedule.run_pending()
            time.sleep(60)
    elif mode == "haber":
        run_weekly_news()
    elif mode == "tavsiye":
        run_weekly_tip()
    else:
        # Railway Cron: 0 5 * * 1,4 (UTC 05:00 Pazartesi+Perşembe = TR 08:00)
        today = datetime.now(timezone.utc).weekday()
        ops.info("Başlatıldı", f"CRON mode — weekday={today}")
        if today == 0:
            run_weekly_news()
        elif today == 3:
            run_weekly_tip()
        else:
            ops.info("Gün Kontrolü", f"Bugün ne Pazartesi ne Perşembe (weekday={today}). Atlanıyor.")
        ops.info("Job Bitti", "Container kapanıyor")
        wait_all_loggers()
