"""
eCom Reklam Otomasyonu — Telegram Bot Entry Point
====================================================
Seedance 2.0 ile profesyonel ürün reklam videoları üreten
Telegram bot. SIFIR insan müdahalesi, MİNİMUM soru sorar.
Sadece ürün linki verilir, pipeline otomatik işler.

v3.0 — Deterministik, URL-tabanlı tam otomasyon
"""
from __future__ import annotations

import asyncio
import io
import os
import sys

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.error import Conflict

# ── Config (Fail-fast boot) ──
from config import settings
from logger import get_logger

# ── Services ──
from services.openai_service import OpenAIService
from services.perplexity_service import PerplexityService
from services.imgbb_service import ImgBBService
from services.kie_api import KieAIService
from services.elevenlabs_service import ElevenLabsService
from services.replicate_service import ReplicateService
from services.notion_service import NotionService
from services.firecrawl_service import FirecrawlService
from services.chat_logger import chat_tracker
from services.upload_post_service import (
    UploadPostService,
    UploadPostError,
    UploadPostAuthError,
)

# ── Core Logic ──
from core.conversation_manager import ConversationManager, ConversationState
from core.scenario_engine import ScenarioEngine
from core.production_pipeline import ProductionPipeline
from core.url_data_extractor import URLDataExtractor
from core.caption_generator import CaptionGenerator
from core.run_state import emitter as run_emitter
from utils.error_messages import categorize_production_error

log = get_logger("main")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🏗️ SERVİS BAŞLATMA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Servis instance'ları — tüm handler'lar tarafından kullanılır
openai_svc = OpenAIService(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
perplexity_svc = PerplexityService(api_key=settings.PERPLEXITY_API_KEY, base_url=settings.PERPLEXITY_BASE_URL)
imgbb_svc = ImgBBService(api_key=settings.IMGBB_API_KEY)
kie_svc = KieAIService(api_key=settings.KIE_API_KEY, base_url=settings.KIE_BASE_URL)
elevenlabs_svc = ElevenLabsService(api_key=settings.ELEVENLABS_API_KEY, model_id=settings.ELEVENLABS_MODEL)
replicate_svc = ReplicateService(api_token=settings.REPLICATE_API_TOKEN)
notion_svc = NotionService(token=settings.NOTION_TOKEN, database_id=settings.NOTION_DB_ID)
firecrawl_svc = FirecrawlService(api_key=getattr(settings, "FIRECRAWL_API_KEY", ""))

# Core modüller — DI ile servisler enjekte edilir
conversation_mgr = ConversationManager(openai_service=openai_svc)
url_extractor = URLDataExtractor(openai_service=openai_svc, firecrawl_service=firecrawl_svc)
scenario_engine = ScenarioEngine(openai_service=openai_svc, perplexity_service=perplexity_svc)
pipeline = ProductionPipeline(
    kie_service=kie_svc,
    elevenlabs_service=elevenlabs_svc,
    replicate_service=replicate_svc,
    notion_service=notion_svc,
    imgbb_service=imgbb_svc,
    is_dry_run=settings.IS_DRY_RUN,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✉️ TELEGRAM 4096 CHAR GUARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Telegram message hard limit 4096; biraz buffer bırakıyoruz.
_TELEGRAM_TEXT_LIMIT = 4000


async def _safe_reply(message, text: str, **kwargs):
    """Telegram 4096-byte limitine takılan uzun metinleri parçalayıp yollar.

    Sadece serbest-uzunluk metinler (senaryo özeti, brief özeti, caption preview,
    delivery message) için kullan. Sabit kısa mesajlara dokunma; gereksiz yere
    parça mantığı eklemek log gürültüsü yapar.

    Returns: gönderilen son Telegram message objesi (kalan kullanım için).
    """
    if text is None:
        text = ""
    if len(text) <= _TELEGRAM_TEXT_LIMIT:
        return await message.reply_text(text, **kwargs)

    # Mesajı parçala; son parçaya reply_markup düşürmek için kwargs'ı koru
    chunks: list[str] = []
    remaining = text
    while remaining:
        chunks.append(remaining[:_TELEGRAM_TEXT_LIMIT])
        remaining = remaining[_TELEGRAM_TEXT_LIMIT:]

    last = None
    # Reply markup sadece son parçada görünsün; ara parçalar düz olsun.
    markup = kwargs.pop("reply_markup", None)
    for i, chunk in enumerate(chunks):
        is_last = i == len(chunks) - 1
        send_kwargs = dict(kwargs)
        if is_last and markup is not None:
            send_kwargs["reply_markup"] = markup
        last = await message.reply_text(chunk, **send_kwargs)
    return last


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡️ ASYNC TASK HATA YÖNETİMİ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _handle_task_exception(task: asyncio.Task):
    """asyncio.create_task ile oluşturulan task'ların sessizce çökmesini önler."""
    try:
        exc = task.exception()
        if exc:
            log.error(f"Background task çöktü: {task.get_name()}", exc_info=exc)
    except asyncio.CancelledError:
        pass


def _spawn_bg_task(app, coro, name: str | None = None) -> asyncio.Task:
    """Arka plan task'ı oluştur ve `app.bot_data['bg_tasks']` setine bağla.

    asyncio.create_task referansı set'te tutulduğu için event loop zayıf-referans
    GC'sine kurban gitmez. done_callback ile hem hata loglanır hem set'ten çıkarılır.
    """
    task = asyncio.create_task(coro, name=name) if name else asyncio.create_task(coro)
    bg_tasks: set = app.bot_data.setdefault("bg_tasks", set())
    bg_tasks.add(task)
    task.add_done_callback(bg_tasks.discard)
    task.add_done_callback(_handle_task_exception)
    return task


async def _cleanup_idle_sessions(app=None):
    """Bellek sızıntısını önle — inaktif session'ları periyodik temizle.

    Ayrıca: 5dk+ brief-stuck watchdog → soft reset + kullanıcıya bildirim.
    """
    while True:
        await asyncio.sleep(300)  # 5 dakikada bir kontrol et
        try:
            # ── brief-stuck watchdog (5dk+) ──
            try:
                stuck_uids = conversation_mgr.find_stuck_brief(max_idle_seconds=300)
                for uid in stuck_uids:
                    conversation_mgr.soft_reset_to_idle(uid)
                    if app is not None:
                        try:
                            await app.bot.send_message(
                                chat_id=uid,
                                text=(
                                    "⏱️ Tercih seçimi zaman aşımına uğradı.\n\n"
                                    "Yeni link bekliyorum — ürün URL'sini gönderebilirsin. 🚀"
                                ),
                            )
                        except Exception as send_exc:
                            log.warning(f"Watchdog bildirim gönderilemedi user={uid}: {send_exc}")
                if stuck_uids:
                    log.info(f"brief-stuck watchdog: {len(stuck_uids)} session soft-reset edildi")
            except Exception:
                log.error("brief-stuck watchdog hatası", exc_info=True)

            import time as _time
            now = _time.time()
            to_delete = []
            # Snapshot iteration: asyncio single-threaded olsa da, gelecek bir await
            # eklenirse iteration sırasında dict mutate olmasın diye list() ile dondur.
            for uid, session in list(conversation_mgr.sessions.items()):
                if not hasattr(session, '_last_activity'):
                    continue
                idle_seconds = now - session._last_activity
                state_name = session.state.name

                # PRODUCING ve RESEARCHING/URL_PROCESSING/PUBLISHING korunur
                if state_name in ("PRODUCING", "RESEARCHING", "URL_PROCESSING", "PUBLISHING"):
                    if idle_seconds > 7200:
                        to_delete.append(uid)
                    continue

                # IDLE/DELIVERED/PUBLISHED → 10 dakika sonra temizle
                if state_name in ("IDLE", "DELIVERED", "PUBLISHED") and idle_seconds > 600:
                    to_delete.append(uid)
                # Brief akışı / Scenario approval / Platform seçimi → 30 dakika sonra temizle
                elif state_name in (
                    "SCENARIO_APPROVAL",
                    "ASKING_FORMAT",
                    "ASKING_STYLE",
                    "WAITING_STYLE_TEXT",
                    "ASKING_CUSTOM_NOTE",
                    "WAITING_CUSTOM_NOTE_TEXT",
                    "ASKING_PLATFORMS",
                    "EDITING_CAPTION",
                ) and idle_seconds > 1800:
                    to_delete.append(uid)

            # Silmeden önce final state check — arada PRODUCING'a geçtiyse koru
            for uid in to_delete:
                sess = conversation_mgr.sessions.get(uid)
                if sess is None:
                    continue
                if sess.state.name in ("PRODUCING", "RESEARCHING", "URL_PROCESSING", "PUBLISHING"):
                    log.info(f"Session {uid} silmesi iptal edildi (state={sess.state.name})")
                    continue
                # Üretim task'ı hâlâ aktifse koru
                if sess.production_task is not None and not sess.production_task.done():
                    log.info(f"Session {uid} silmesi iptal (aktif production_task)")
                    continue
                del conversation_mgr.sessions[uid]
            if to_delete:
                log.info(f"Session temizliği: {len(to_delete)} session kaldırıldı, "
                         f"kalan: {len(conversation_mgr.sessions)}")
        except Exception:
            log.error("Session temizleme hatası", exc_info=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡️ ERİŞİM KONTROLÜ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def is_authorized(user_id: int) -> bool:
    """Sadece izin verilen kullanıcıları kabul et."""
    return user_id in settings.ALLOWED_USER_IDS


async def unauthorized_reply(update: Update):
    """Yetkisiz kullanıcıya yanıt."""
    await update.effective_message.reply_text(
        "⛔ Bu botu kullanma yetkiniz yok.\n"
        "Bu bot sadece yönetici tarafından kullanılabilir."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📋 KOMUT HANDLER'LARI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komutu — sohbeti başlatır."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    reply = conversation_mgr.handle_start(user.id, user.first_name or user.username or "")
    await update.message.reply_text(reply, parse_mode="Markdown")
    await chat_tracker.log_interaction(str(user.id), "/start", reply)


async def _cancel_user_production(user_id: int) -> bool:
    """Kullanıcının çalışan üretim task'ını gerçekten cancel eder.

    Returns:
        bool: Aktif bir task iptal edildiyse True, yoksa False.
    """
    session = conversation_mgr.get_session(user_id)
    cancelled = False
    task = session.production_task
    if task is not None and not task.done():
        task.cancel()
        cancelled = True
        log.info(f"Üretim task'ı iptal edildi: user={user_id}")
    session.production_task = None
    session.production_progress_msg_id = None
    session.production_chat_id = None
    session.reset()
    return cancelled


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/cancel komutu — mevcut işlemi iptal eder (arka plan task dahil)."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    cancelled = await _cancel_user_production(user.id)
    msg = (
        "❌ İptal edildi — arka plandaki üretim durduruldu.\n"
        if cancelled
        else "❌ İptal edildi.\n"
    )
    msg += "/start yazarak yeni bir video üretimine başlayabilirsin."
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help komutu — komutları ve akışı listele."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    msg = (
        "🤖 *eCom Reklam Bot — Kullanım*\n\n"
        "*Komutlar:*\n"
        "• /start — Sohbeti başlat\n"
        "• /status — Mevcut üretim durumunu göster\n"
        "• /cancel — Çalışan üretimi iptal et\n"
        "• /help — Bu mesaj\n\n"
        "*Akış:*\n"
        "1. Ürün URL'si gönder (PrettyLittleThing, Trendyol, Amazon vb.)\n"
        "2. Format → Tarz → Ek not seçimlerini yap\n"
        "3. Senaryo onayı geldiğinde ✅ veya ❌ bas\n"
        "4. Video teslim edildiğinde sosyal medya platformlarını seç\n"
        "5. Caption'ı düzenle veya direkt paylaş\n\n"
        "Sorun olursa /cancel + yeni URL ile baştan başla."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status komutu — mevcut durumu gösterir."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    session = conversation_mgr.get_session(user.id)
    state_labels = {
        ConversationState.IDLE: "⚪ Boşta",
        ConversationState.ASKING_FORMAT: "📐 Format seçimi bekleniyor",
        ConversationState.ASKING_STYLE: "🎨 Tarz seçimi bekleniyor",
        ConversationState.WAITING_STYLE_TEXT: "🎨 Tarz metni bekleniyor",
        ConversationState.ASKING_CUSTOM_NOTE: "✍️ Ek not seçimi bekleniyor",
        ConversationState.WAITING_CUSTOM_NOTE_TEXT: "✍️ Ek not metni bekleniyor",
        ConversationState.URL_PROCESSING: "🔗 URL inceleniyor",
        ConversationState.RESEARCHING: "🔍 Araştırma & Senaryo",
        ConversationState.SCENARIO_APPROVAL: "📋 Senaryo onayı",
        ConversationState.PRODUCING: "🎬 Video üretimi",
        ConversationState.DELIVERED: "✅ Teslim edildi",
        ConversationState.ASKING_PLATFORMS: "📤 Platform seçimi bekleniyor",
        ConversationState.EDITING_CAPTION: "✏️ Caption düzenleniyor",
        ConversationState.PUBLISHING: "🚀 Sosyal medya paylaşımı",
        ConversationState.PUBLISHED: "✅ Paylaşıldı",
    }
    status_text = state_labels.get(session.state, "❓ Bilinmiyor")

    msg = f"📊 **Durum:** {status_text}\n"

    mode = "🏜️ DRY-RUN" if settings.IS_DRY_RUN else "🟢 PRODUCTION"
    msg += f"\n⚙️ **Mod:** {mode}"

    await update.message.reply_text(msg, parse_mode="Markdown")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💬 MESAJ HANDLER'LARI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _send_button_payload(send_target, btn_data: dict) -> None:
    """Standart buton payload'ını render et ve gönder.

    `send_target.reply_text` çağrılabilir bir mesaj-benzeri objedir
    (update.message veya query.message).
    """
    keyboard_rows = []
    options = btn_data.get("options", [])
    choice_key = btn_data.get("choice_key", "unknown")
    question = btn_data.get("question", "Lütfen seçiminizi yapın:")

    for opt in options:
        val = opt.get("value", "unkn")
        label = opt.get("label", "Seçenek")
        cb_data = f"pref:{choice_key}:{val}"
        if len(cb_data.encode("utf-8")) > 64:
            cb_data = cb_data.encode("utf-8")[:64].decode("utf-8", errors="ignore")
        keyboard_rows.append([InlineKeyboardButton(label, callback_data=cb_data)])

    if btn_data.get("allow_freetext"):
        cb_data = f"pref:{choice_key}:__freetext__"
        keyboard_rows.append([InlineKeyboardButton("✍️ Kendim yazacağım", callback_data=cb_data)])

    markup = InlineKeyboardMarkup(keyboard_rows)
    try:
        await send_target.reply_text(question, reply_markup=markup, parse_mode="Markdown")
    except Exception:
        await send_target.reply_text(question, reply_markup=markup)


async def _send_note_buttons(send_target) -> None:
    """ASKING_CUSTOM_NOTE durumunda 'Not yaz / Atla' butonlarını gönder."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✍️ Not yaz", callback_data="note:write")],
        [InlineKeyboardButton("⏩ Atla", callback_data="note:skip")],
    ])
    try:
        await send_target.reply_text(
            "Aşağıdan seç:", reply_markup=keyboard, parse_mode="Markdown"
        )
    except Exception:
        await send_target.reply_text("Aşağıdan seç:", reply_markup=keyboard)


def _kick_off_lite_extract(user_id: int, url: str, app) -> None:
    """Lite extract'i bg task olarak başlat — session.product_category'yi günceller."""
    session = conversation_mgr.get_session(user_id)
    if session.lite_extract_task is not None and not session.lite_extract_task.done():
        return  # Zaten çalışıyor

    async def _runner():
        try:
            lite_data = await url_extractor.extract_lite(url)
            session.product_category = lite_data.get("category") or "general"
            session.lite_brand = lite_data.get("brand_name") or session.lite_brand
            session.lite_product = lite_data.get("product_name") or session.lite_product
            log.info(
                f"Lite extract tamam: user={user_id}, category={session.product_category}"
            )
        except Exception as exc:
            log.warning(f"Lite extract hatası (user={user_id}): {exc}")
            # Fallback: kategori yoksa generic
            if not session.product_category:
                session.product_category = "general"

    session.lite_extract_task = _spawn_bg_task(app, _runner(), name=f"lite-{user_id}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Metin mesajı handler — ana giriş noktası."""
    user = update.effective_user
    if not is_authorized(user.id):
        return await unauthorized_reply(update)

    text = update.message.text.strip()
    if not text:
        return

    user_name = user.first_name or user.username or ""

    # ── URL algılandıysa lite_extract'i ARKAPLAN'da başlat (UI bloklanmasın) ──
    pre_url = URLDataExtractor.extract_url_from_text(text)
    if pre_url:
        # Pre-validation: scheme + sosyal medya blacklist
        valid, err_msg = URLDataExtractor.is_valid_product_url(pre_url)
        if not valid:
            await update.message.reply_text(f"⚠️ {err_msg}", parse_mode=None)
            await chat_tracker.log_interaction(
                str(user.id), text, f"[Sistem - URL Geçersiz] {err_msg}"
            )
            session = conversation_mgr.get_session(user.id)
            session.state = ConversationState.IDLE
            return

        session = conversation_mgr.get_session(user.id)
        # Yalnızca yeni URL ise veya henüz kategori yoksa başlat
        if (
            not session.product_category
            or session.current_url != pre_url
            or session.pending_url != pre_url
        ):
            # Eski category'yi temizle ki yeni brief doğru kategoriyi alsın
            session.product_category = None
            session.lite_brand = None
            session.lite_product = None
            _kick_off_lite_extract(user.id, pre_url, context.application)

    # Manager'a yönlendir
    result = await conversation_mgr.handle_text_message(user.id, text, user_name)

    # SCENARIO_APPROVAL: Metin tabanlı onay
    if result.get("action") == "approve":
        reply_msg = "🚀 **Üretim başlıyor!**\nHer adımda bildirim alacaksın."
        cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data="prod:cancel")]])
        progress_msg = await update.message.reply_text(reply_msg, parse_mode="Markdown", reply_markup=cancel_kb)
        await chat_tracker.log_interaction(str(user.id), text, reply_msg)

        session = conversation_mgr.get_session(user.id)
        session.production_progress_msg_id = progress_msg.message_id
        session.production_chat_id = progress_msg.chat_id

        task = _spawn_bg_task(
            context.application,
            _run_production(update.effective_message, user.id),
            name=f"production-{user.id}",
        )
        session.production_task = task
        return
    elif result.get("action") == "cancel":
        await update.message.reply_text(result["reply"], parse_mode="Markdown")
        await chat_tracker.log_interaction(str(user.id), text, result["reply"])
        return

    elif result.get("action") == "caption_updated":
        # EDITING_CAPTION sonrası → ack + yeni picker mesajı
        if result.get("reply"):
            try:
                await update.message.reply_text(result["reply"], parse_mode="Markdown")
            except Exception:
                await update.message.reply_text(result["reply"])
        session = conversation_mgr.get_session(user.id)
        await _send_publishing_picker(update.message, session, edit=False)
        return

    # Normal yanıt
    if result.get("reply"):
        try:
            await update.message.reply_text(result["reply"], parse_mode="Markdown")
        except Exception:
            log.warning("Markdown parse hatası — parse_mode=None ile tekrar deneniyor")
            await update.message.reply_text(result["reply"])
        await chat_tracker.log_interaction(str(user.id), text, result["reply"])

    # Buton yanıtı (format butonları — yeni brief başlangıcı)
    if result.get("buttons"):
        try:
            await _send_button_payload(update.message, result["buttons"])
            await chat_tracker.log_interaction(
                str(user.id), "[Sistem - Buton Gösterildi]",
                result["buttons"].get("question", ""),
            )
        except Exception as e:
            log.error(f"Buton yanıtı oluşturulurken hata: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Seçenekler gösterilemedi, lütfen tekrar dene.")

    # Note buttons (custom_note state'i — sadece manager'dan gelirse)
    if result.get("note_buttons"):
        try:
            await _send_note_buttons(update.message)
        except Exception as e:
            log.error(f"Note butonu hatası: {e}", exc_info=True)

    # URL pipeline'ı başlat
    if result.get("has_url") and result.get("url"):
        _spawn_bg_task(
            context.application,
            _process_url_and_scenario(update.effective_message, user.id, result["url"]),
            name=f"url-scenario-{user.id}",
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 Pipeline 1: URL ÇIKARMA + SENARYO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _process_url_and_scenario(message, user_id: int, url: str):
    """Arka planda veri çıkarma, araştırma ve senaryo üretimini yürütür.

    WHY session.lock: Kullanıcı arka arkaya iki URL atarsa (URL1 işleniyorken URL2
    geliyor), URL1'in bg task'ı session.scenario / session.collected_data yazmaya
    devam ediyordu. URL2 ana handler lock alıyor ama URL1'in bg task'ı lock'sızdı
    -> state corruption. Tüm kritik yazma akışı session.lock altında.
    """
    session = conversation_mgr.get_session(user_id)

    async with session.lock:
        try:
            # Dashboard canlı izleme başlat
            run_emitter.start_run(input_label=url)

            # Adım 1: URL'den Veri Çıkarma
            run_emitter.start_stage("extract", sub_text="Sayfa kazınıyor, görsel ve metin analizleri yapılıyor")
            try:
                extracted_data = await url_extractor.extract(url)
                session.set_extracted_data(extracted_data)
                run_emitter.end_stage("extract", payload={
                    "brand": extracted_data.get("brand_name") or "",
                    "product": extracted_data.get("product_name") or "",
                    "concept": extracted_data.get("ad_concept") or "",
                    "hero_image_url": (extracted_data.get("best_image_urls") or [None])[0],
                })
            except Exception as _ex_err:
                run_emitter.fail_stage("extract", str(_ex_err)[:200])
                raise

            # Adım 2: Araştırma
            conversation_mgr.mark_researching(user_id)
            run_emitter.start_stage("scenario", sub_text="Marka araştırması + senaryo kurgulanıyor")
            await message.reply_text(
                f"🔍 **Görsel ve metin analizleri tamam!**\nMarka araştırması ve senaryo kurgulanıyor...\nBu 15-30 saniye sürebilir.",
                parse_mode="Markdown"
            )

            # WHY: research → scenario sıralı; ama her ikisini gather+return_exceptions
            # ile sarmalıyoruz ki dış akıştaki bir hata async task exception'ı sessizce
            # yutmasın. Her sonucu manuel inceliyoruz, hangisi fail ettiyse Telegram'a
            # net Türkçe mesaj döner. (Mirror of _produce_voiceover/_produce_character_image
            # pattern in production_pipeline.py.)
            research_results = await asyncio.gather(
                asyncio.to_thread(scenario_engine.research, session.collected_data),
                return_exceptions=True,
            )
            research_data = research_results[0]
            if isinstance(research_data, BaseException):
                log.error(f"Marka araştırması başarısız: {research_data}", exc_info=research_data)
                session.state = ConversationState.IDLE
                run_emitter.fail_stage("scenario", f"Marka araştırması başarısız: {str(research_data)[:200]}")
                run_emitter.fail_run("Marka araştırması yapılamadı")
                await message.reply_text(
                    "🔎 Marka araştırması yapılamadı.\n\n"
                    f"Detay: {str(research_data)[:160]}\n\n"
                    "Bir kaç dakika sonra tekrar dener misin?",
                    parse_mode="Markdown",
                )
                return

            run_emitter.update_stage("scenario", sub_text="Araştırma tamam, senaryo yazılıyor")

            # Adım 3: Senaryo Üretimi (gather+return_exceptions ile silent-drop koruma)
            scenario_results = await asyncio.gather(
                asyncio.to_thread(
                    scenario_engine.generate_scenario,
                    session.collected_data,
                    research_data,
                    session.preferences,
                ),
                return_exceptions=True,
            )
            scenario = scenario_results[0]
            if isinstance(scenario, BaseException):
                log.error(f"Senaryo üretimi başarısız: {scenario}", exc_info=scenario)
                session.state = ConversationState.IDLE
                run_emitter.fail_stage("scenario", f"Senaryo üretimi başarısız: {str(scenario)[:200]}")
                run_emitter.fail_run("Senaryo üretilemedi")
                await message.reply_text(
                    "🎬 Senaryo üretilemedi.\n\n"
                    f"Detay: {str(scenario)[:160]}\n\n"
                    "Aynı linki tekrar gönder, başka bir tarz veya ek not deneyebilirsin.",
                    parse_mode="Markdown",
                )
                return

            session.scenario = scenario
            conversation_mgr.mark_scenario_approval(user_id)

            run_emitter.end_stage("scenario", payload={
                "scene_count": len(scenario.get("scenes", []) or []),
                "duration_sec": scenario.get("duration") or scenario.get("total_duration"),
                "voiceover_text": (scenario.get("voiceover_text") or scenario.get("voiceover") or "")[:400],
                "first_scene": (scenario.get("scenes") or [{}])[0].get("description") if scenario.get("scenes") else None,
            })

            # Senaryo Özeti + Onay
            summary = ScenarioEngine.format_scenario_summary(scenario)
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Onayla", callback_data="scenario_approve"),
                    InlineKeyboardButton("❌ İptal", callback_data="scenario_cancel"),
                ]
            ])

            try:
                await _safe_reply(
                    message,
                    summary,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception as e:
                log.warning(f"HTML parse hatası (Senaryo Özeti): {e} — parse_mode=None ile deneniyor")
                await _safe_reply(
                    message,
                    summary,
                    reply_markup=keyboard,
                )

        except Exception as e:
            log.error(f"URL işleme/senaryo hatası: {e}", exc_info=True)
            session.state = ConversationState.IDLE
            try:
                run_emitter.fail_run(f"URL/senaryo hatası: {str(e)[:200]}")
            except Exception:
                pass

            err_lower = str(e).lower()
            # Hata tipine göre aksiyon-odaklı mesaj
            if "url" in err_lower and ("hiçbir veri" in err_lower or "extract" in err_lower):
                error_reply = (
                    "🔗 Bu sayfadan ürün bilgisi okuyamadım.\n\n"
                    "Olası sebepler:\n"
                    "• Sayfa JavaScript ile dinamik yükleniyor (scraper göremedi)\n"
                    "• Link bir kategori/ana sayfa, doğrudan ürün sayfası değil\n"
                    "• Site bot trafiğini engelliyor\n\n"
                    "💡 **Çözüm:** Ürünün tek-ürün detay sayfasının linkini gönder "
                    "(örn. `marka.com/urun/X` gibi, `marka.com/kategori` değil)."
                )
            elif "timeout" in err_lower or "timed out" in err_lower:
                error_reply = (
                    "⏱️ Sayfa yanıt vermedi (timeout).\n\n"
                    "Site yavaş ya da bot engeli olabilir. Bir kaç dakika sonra tekrar dener misin? "
                    "Yine olmazsa farklı bir ürün linkiyle devam edelim."
                )
            elif "image" in err_lower and "format" in err_lower:
                error_reply = (
                    "🖼️ Sayfadaki ürün görselleri desteklenmiyor (muhtemelen SVG/AVIF).\n\n"
                    "Aynı ürünün başka bir sayfasını veya farklı bir ürün linkini dener misin?"
                )
            else:
                error_reply = (
                    f"⚠️ Ürün bilgisi çıkarılamadı.\n\n"
                    f"Detay: {str(e)[:160]}\n\n"
                    f"Linki kontrol edip tekrar dene, ya da başka bir ürün linki gönder."
                )
            await _safe_reply(message, error_reply, parse_mode="Markdown")
            await chat_tracker.log_interaction(str(user_id), "[Sistem - Fallback URL Hatası]", error_reply)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔘 INLINE BUTTON HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Senaryo onay/iptal inline butonları."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    if not is_authorized(user.id):
        await query.edit_message_text("⛔ Yetkiniz yok.")
        return

    data = query.data

    if data == "scenario_approve":
        # Double-press guard: kullanıcı 100ms içinde iki kez basarsa ikinci task
        # ilkini override eder ve referans kaybolur (potansiyel GC + Notion duplicate).
        # WHY atomic-via-lock: önceki guard check + task assign arasında race window
        # vardı. Şimdi tüm check+spawn+assign sequence'i session.lock altında —
        # iki paralel callback ilki bitene kadar sıraya giriyor; ikinci callback
        # lock aldığında production_task zaten set olduğu için exit ediyor.
        existing_session = conversation_mgr.get_session(user.id)
        async with existing_session.lock:
            if (
                getattr(existing_session, "production_task", None) is not None
                and not existing_session.production_task.done()
            ):
                try:
                    await query.edit_message_reply_markup(reply_markup=None)
                except Exception:
                    pass
                await query.message.reply_text("⏳ Üretim zaten başladı, lütfen bekle.")
                return

            result = conversation_mgr.handle_scenario_response(user.id, "approve")
            await query.edit_message_reply_markup(reply_markup=None)
            cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data="prod:cancel")]])
            progress_msg = await query.message.reply_text(
                "🚀 **Üretim başlıyor!**\n"
                "Her adımda bildirim alacaksın.",
                parse_mode="Markdown",
                reply_markup=cancel_kb,
            )

            existing_session.production_progress_msg_id = progress_msg.message_id
            existing_session.production_chat_id = progress_msg.chat_id

            task = _spawn_bg_task(
                context.application,
                _run_production(query.message, user.id),
                name=f"production-{user.id}",
            )
            existing_session.production_task = task

    elif data == "prod:cancel":
        # Üretim sırasında "❌ İptal" butonu — gerçek task cancel
        cancelled = await _cancel_user_production(user.id)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        msg = (
            "❌ Üretim iptal edildi — arka plandaki task durduruldu."
            if cancelled
            else "❌ İptal edildi (aktif üretim bulunamadı)."
        )
        await query.message.reply_text(msg, parse_mode="Markdown")

    elif data == "scenario_cancel":
        result = conversation_mgr.handle_scenario_response(user.id, "cancel")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            result.get("reply", "❌ İptal edildi."),
            parse_mode="Markdown",
        )
    elif data.startswith("pref:"):
        await _handle_pref_callback(query, user.id, data, context)

    elif data.startswith("note:"):
        await _handle_note_callback(query, user.id, data, context)

    elif data.startswith("pub:"):
        await _handle_pub_callback(query, user.id, data, context)

    else:
        log.warning(f"Bilinmeyen callback data: {data}")
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass


async def _handle_pref_callback(query, user_id: int, data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """`pref:choice_key:value` callback'ini işler — format/style/freetext routing."""
    parts = data.split(":", 2)
    if len(parts) < 3:
        return
    choice_key = parts[1]
    choice_value = parts[2]

    # Butonları kapat
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    # WHY state pre-check: Eski mesajlardaki butonlar kaldırılmasa bile
    # kullanıcı geri kaydırıp eski format butonuna basabiliyor — handler
    # state'i kontrol etmeden set_format çalıştırıp brief akışını bozuyor
    # (örn. style aşamasındayken format yeniden ediliyor). Şimdi state
    # doğru değilse kullanıcıya kibarca bilgilendir + handler exit et.
    from core.conversation_manager import ConversationState as _CS
    _session = conversation_mgr.get_session(user_id)
    _expected_state = {
        "video_format": _CS.ASKING_FORMAT,
        "video_style": _CS.ASKING_STYLE,
    }.get(choice_key)
    if _expected_state is not None and _session.state != _expected_state:
        log.info(
            f"Stale pref callback ignored: user={user_id} key={choice_key} "
            f"current_state={_session.state.name} expected={_expected_state.name}"
        )
        try:
            await query.message.reply_text(
                "⏭ Bu buton geçerliliğini yitirdi (akış ilerledi). "
                "Devam etmek için yukarıdaki yeni butonları kullan."
            )
        except Exception:
            pass
        return

    # ── video_format ──
    if choice_key == "video_format":
        conversation_mgr.set_format(user_id, choice_value)
        # Lite extract bittiyse direkt style buttons; bitmediyse "kategorize ediyorum" + bekle
        if not conversation_mgr.category_ready(user_id):
            await query.message.reply_text(
                "🔎 Ürünü hızlıca inceliyorum, tarz seçenekleri bir kaç saniye içinde geliyor...",
                parse_mode="Markdown",
            )
            await conversation_mgr.await_lite_extract(user_id, timeout=10.0)
        try:
            buttons = await conversation_mgr.build_style_buttons(user_id)
            await _send_button_payload(query.message, buttons)
            await chat_tracker.log_interaction(
                str(user_id), f"[Format seçildi: {choice_value}]",
                buttons.get("question", ""),
            )
        except Exception as e:
            log.error(f"Style butonları oluşturulamadı: {e}", exc_info=True)
            await query.message.reply_text(
                "⚠️ Tarz seçenekleri üretilemedi. /start ile yeniden başla."
            )
        return

    # ── video_style ──
    if choice_key == "video_style":
        if choice_value == "__freetext__":
            # Kullanıcı kendi tarzını yazacak → WAITING_STYLE_TEXT
            session = conversation_mgr.get_session(user_id)
            from core.conversation_manager import ConversationState as CS
            session.state = CS.WAITING_STYLE_TEXT
            await query.message.reply_text(
                "✍️ Tarzını yaz (örn. 'Sokakta UGC', 'Sinematik close-up'):",
                parse_mode="Markdown",
            )
            return
        # Index-based çözüm
        full_value = conversation_mgr.resolve_style_value(user_id, choice_value)
        result = conversation_mgr.set_style(user_id, full_value)
        if result.get("reply"):
            try:
                await query.message.reply_text(result["reply"], parse_mode="Markdown")
            except Exception:
                await query.message.reply_text(result["reply"])
        if result.get("note_buttons"):
            await _send_note_buttons(query.message)
        return

    # Tanınmayan choice_key
    log.warning(f"Tanınmayan choice_key: {choice_key}")


async def _handle_note_callback(query, user_id: int, data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """`note:skip` veya `note:write` callback'ini işler."""
    action = data.split(":", 1)[1] if ":" in data else ""

    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    if action == "skip":
        result = conversation_mgr.handle_note_skip(user_id)
        if result.get("reply"):
            try:
                await query.message.reply_text(result["reply"], parse_mode="Markdown")
            except Exception:
                await query.message.reply_text(result["reply"])
        if result.get("has_url") and result.get("url"):
            _spawn_bg_task(
                context.application,
                _process_url_and_scenario(query.message, user_id, result["url"]),
                name=f"url-scenario-{user_id}",
            )
        return

    if action == "write":
        result = conversation_mgr.handle_note_write_request(user_id)
        if result.get("reply"):
            try:
                await query.message.reply_text(result["reply"], parse_mode="Markdown")
            except Exception:
                await query.message.reply_text(result["reply"])
        return

    log.warning(f"Tanınmayan note action: {action}")


async def _handle_pub_callback(query, user_id: int, data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """`pub:<action>[:<arg>]` — Upload-Post paylaşım akışı callback'leri.

    Aksiyonlar:
        toggle:<platform>  — platform'u seçili/değil yap, picker'ı tazele
        edit_caption       — kullanıcı yeni caption yazsın (state EDITING_CAPTION)
        share              — Upload-Post'a yolla, polling ile takip et
        cancel             — paylaşım iptal, session reset
        done               — sonuç ekranı kapanır, session reset
    """
    parts = data.split(":")
    if len(parts) < 2:
        return
    action = parts[1]
    session = conversation_mgr.get_session(user_id)

    # WHY stale-callback guard: Telegram eski mesajlardaki butonları silmez.
    # Kullanıcı paylaşım bittikten (PUBLISHED) veya yeni URL gönderdikten
    # sonra geri kaydırıp eski "platform toggle / caption düzenle / paylaş"
    # butonuna basabiliyor. O an session reset edilmiş — connected_platforms
    # boş, publishing_message_id None → _send_publishing_picker boş bozuk
    # bir kart üretiyor, ya da stale `share` video_url'siz publish deniyor.
    # toggle/edit_caption/share yalnızca aktif picker state'lerinde geçerli.
    # cancel/done her zaman güvenli (sadece temizlik yapıyorlar).
    if action in ("toggle", "edit_caption", "share"):
        if session.state not in (
            ConversationState.ASKING_PLATFORMS,
            ConversationState.EDITING_CAPTION,
        ):
            log.info(
                f"Stale pub callback ignored: user={user_id} action={action} "
                f"state={session.state.name}"
            )
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass
            try:
                await query.message.reply_text(
                    "⏭ Bu paylaşım butonu geçerliliğini yitirdi (akış ilerledi). "
                    "Yeni video için ürün linki gönder."
                )
            except Exception:
                pass
            return

    if action == "toggle":
        if len(parts) < 3:
            return
        platform = parts[2]
        if platform in session.selected_platforms:
            session.selected_platforms.discard(platform)
        else:
            session.selected_platforms.add(platform)
        await _send_publishing_picker(query.message, session, edit=True)
        return

    if action == "edit_caption":
        session.state = ConversationState.EDITING_CAPTION
        try:
            await query.message.reply_text(
                "✏️ Yeni caption'ı yaz (tüm seçili platformlara aynı metin gönderilir):",
            )
        except Exception:
            log.warning("Edit caption prompt gönderilemedi", exc_info=True)
        return

    if action == "share":
        if not session.selected_platforms:
            # query.answer() en üstte çağrılmış olduğundan alert düşmeyecek;
            # bunun yerine kullanıcıya görünür bir mesaj döndür.
            try:
                await query.message.reply_text("⚠️ En az bir platform seç!")
            except Exception:
                pass
            return
        # WHY double-press guard: kullanıcı 100ms içinde iki kez basarsa iki
        # paralel _publish_and_track aynı video'yu Upload-Post'a iki kez yollar
        # + aynı publishing_message_id'ye yazmaya çalışır (race + ikinci
        # Notion comment). scenario_approve'daki guard pattern'ini birebir
        # uygula: lock altında check + spawn + assign atomik.
        async with session.lock:
            existing_publish = getattr(session, "publish_task", None)
            if existing_publish is not None and not existing_publish.done():
                try:
                    await query.message.reply_text("⏳ Paylaşım zaten başladı, lütfen bekle.")
                except Exception:
                    pass
                return
            session.state = ConversationState.PUBLISHING
            task = _spawn_bg_task(
                context.application,
                _publish_and_track(query.message, user_id),
                name=f"publish-{user_id}",
            )
            session.publish_task = task
        return

    if action == "cancel":
        # WHY: session.reset() publish_task referansını sıfırlar ama çalışan
        # task'ı CANCEL ETMEZ — Upload-Post API çağrısı + polling (180s)
        # arka planda devam eder, kullanıcıya "iptal edildi" denmesine
        # rağmen publish gerçekleşir. Önce task.cancel() ile durdur.
        existing_publish = getattr(session, "publish_task", None)
        if existing_publish is not None and not existing_publish.done():
            existing_publish.cancel()
            log.info(f"Publish task iptal edildi: user={user_id}")
        # WHY: pub:cancel dashboard run'ını "running" durumunda bırakıyordu —
        # caption stage tamam, upload pending, run sonsuza kadar çalışır
        # görünüyor. Bir sonraki start_run() reset ediyor ama canlı demo
        # sırasında ekran "takılmış" görünür. fail_run ile temiz kapat.
        try:
            run_emitter.fail_run("Paylaşım kullanıcı tarafından iptal edildi")
        except Exception:
            pass
        try:
            await query.message.edit_text("❌ Paylaşım iptal edildi.")
        except Exception:
            try:
                await query.message.reply_text("❌ Paylaşım iptal edildi.")
            except Exception:
                pass
        session.reset()
        return

    if action == "done":
        original = ""
        try:
            original = query.message.text or ""
        except Exception:
            pass
        session.reset()
        try:
            await query.message.edit_text(
                (original + "\n\n_(Yeni video için ürün URL'i gönder)_").strip(),
                parse_mode="Markdown",
            )
        except Exception:
            try:
                await query.message.reply_text(
                    "Yeni video için ürün URL'i gönder.",
                )
            except Exception:
                pass
        return

    log.warning(f"Tanınmayan pub action: {action}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎬 Pipeline 2: VIDEO ÜRETİMİ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _run_production(message, user_id: int):
    """Deterministik üretim pipeline'ını arka planda yürütür."""
    session = conversation_mgr.get_session(user_id)
    scenario = session.scenario

    if not scenario:
        await message.reply_text("⚠️ Senaryo bulunamadı. /start ile tekrar başla.")
        return

    # İptal butonu sadece üretim başlangıç mesajında bir kez gösteriliyor (yukarıda).
    # Progress mesajları sade — her mesajda buton spam'ı yok.
    # Dashboard sub-stage routing (lokal-only, no-op subscriber yoksa):
    # 3 alt-grup — assets (karakter+ses), scenes (N/M sahne), merge (concat+sync)
    _produce_subs = {"assets": False, "scenes": False, "merge": False}

    def _ensure_sub(sub_id: str, sub_text: str | None = None) -> None:
        if not _produce_subs[sub_id]:
            run_emitter.start_substage("produce", sub_id, sub_text=sub_text)
            _produce_subs[sub_id] = True
        elif sub_text is not None:
            run_emitter.update_substage("produce", sub_id, sub_text=sub_text)

    ASSETS_STEPS = {
        "step_voiceover", "voiceover_warning", "voiceover_resync",
        "step_character", "scene_extend",
    }
    MERGE_STEPS = {"step_1b", "step_3", "merge_warning", "warning_silent_video"}
    # WHY: retry_no_ref/retry_safety tek-sahne video üretimi sırasında (scenes
    # fazı) fire ediyor — step_1 zaten assets'i kapatıp scenes'i açmış olur.
    # Eskiden ASSETS_STEPS'teydiler → _ensure_sub("assets") kapalı assets
    # substage'ini YENİDEN AÇIYORDU (dashboard'da tamamlanmış kutu tekrar
    # "active"a dönüyordu). Bunlar video-gen retry'ları → scenes substage'ine ait.
    SCENE_RETRY_STEPS = {"scene_retry", "retry_no_ref", "retry_safety"}

    async def progress_callback(step: str, msg: str):
        # Dashboard alt-detay güncellemesi + sub-stage routing
        try:
            run_emitter.update_stage("produce", sub_text=msg[:140])

            if step == "scene_done" and msg.startswith("__SCENE_PROGRESS__"):
                # Pipeline'ın özel sinyali: __SCENE_PROGRESS__|idx|total|name
                parts = msg.split("|")
                if len(parts) >= 4:
                    try:
                        idx, total = int(parts[1]), int(parts[2])
                        scene_name = parts[3]
                        _ensure_sub("scenes", sub_text=f"{idx}/{total} sahne hazır")
                        progress = idx / max(total, 1)
                        run_emitter.update_substage(
                            "produce", "scenes",
                            sub_text=f"{idx}/{total} sahne — {scene_name[:50]}",
                            progress=progress,
                        )
                        if idx >= total:
                            run_emitter.end_substage(
                                "produce", "scenes",
                                payload={"scene_count": total},
                            )
                    except (ValueError, IndexError):
                        pass
                return  # scene_done Telegram'a mesaj basmaz

            if step in ASSETS_STEPS:
                _ensure_sub("assets", sub_text=msg[:120])
            elif step in MERGE_STEPS:
                # Önceki sub-stage'leri kapat (assets/scenes hâlâ açıksa)
                if _produce_subs["assets"]:
                    run_emitter.end_substage("produce", "assets")
                    _produce_subs["assets"] = False
                if _produce_subs["scenes"]:
                    run_emitter.end_substage("produce", "scenes")
                    _produce_subs["scenes"] = False
                _ensure_sub("merge", sub_text=msg[:120])
            elif step.startswith("step_1") and step != "step_1b":
                # tek video render veya multi-scene başlangıç
                if _produce_subs["assets"]:
                    run_emitter.end_substage("produce", "assets")
                    _produce_subs["assets"] = False
                _ensure_sub("scenes", sub_text=msg[:120])
            elif step in SCENE_RETRY_STEPS:
                # scene_retry / retry_no_ref / retry_safety — hepsi scenes fazı
                _ensure_sub("scenes", sub_text=msg[:120])
        except Exception:
            log.warning("Dashboard progress emit hatası", exc_info=True)
        try:
            await message.reply_text(msg, parse_mode="Markdown")
        except Exception:
            try:
                await message.reply_text(msg, parse_mode=None)
            except Exception:
                log.error(f"Progress bildirim hatası: {step}", exc_info=True)

    try:
        run_emitter.start_stage("produce", sub_text="Seedance video render kuyruğa alındı")
        result = await pipeline.produce(
            scenario=scenario,
            collected_data=session.collected_data,
            progress_callback=progress_callback,
            user_name=session.user_name,
            preferences=session.preferences,
        )

        if result["status"] == "success":
            video_url = result.get("video_url", "")
            # Sub-stage'leri kapat (hâlâ açık kalanlar varsa)
            for _sub_id, _open in list(_produce_subs.items()):
                if _open:
                    run_emitter.end_substage("produce", _sub_id)
                    _produce_subs[_sub_id] = False
            run_emitter.end_stage("produce", payload={
                "video_url": video_url,
                "raw_video_url": result.get("raw_video_url"),
                "voiceover_ok": result.get("voiceover_succeeded", True),
                "duration_sec": result.get("duration_sec"),
            })

            # WHY: voiceover üretilemediyse video ambient seslerle teslim
            # ediliyor — kullanıcı önceden sadece "Video Hazır!" görüp tıklayıp
            # sessiz video ile karşılaşıyordu. Explicit uyarı + sebep göster.
            voiceover_ok = result.get("voiceover_succeeded", True)
            if voiceover_ok:
                delivery_msg = (
                    f"🎬 **Video Hazır!**\n\n"
                    f"📥 **İndir:** {video_url}\n"
                )
            else:
                _vo_err = (result.get("voiceover_error") or "Dış ses üretilemedi")[:160]
                delivery_msg = (
                    f"🎬 **Video Hazır — Sessiz Teslimat**\n"
                    f"⚠️ Dış ses üretilemediği için video ambient seslerle teslim edildi.\n"
                    f"_Sebep: {_vo_err}_\n\n"
                    f"📥 **İndir:** {video_url}\n"
                )

            if result.get("cost"):
                cost = result["cost"]
                delivery_msg += f"💰 **Maliyet:** ${cost.get('total_usd', 0):.2f}\n"

            if result.get("notion_page_url"):
                delivery_msg += f"📋 **Log:** {result['notion_page_url']}\n"

            delivery_msg += "\n🔄 Yeni video için ürün linki gönderebilir veya /start yazabilirsin!"

            try:
                await _safe_reply(message, delivery_msg, parse_mode="Markdown")
            except Exception:
                await _safe_reply(message, delivery_msg, parse_mode=None)
            await chat_tracker.log_interaction(str(user_id), "[Sistem - Üretim Tamamlandı]", delivery_msg)

            # Native Telegram Video Upload (Fallbacks to URL)
            # WHY: 50MB video buffer in-memory. Eski hali video_io.close() son
            # satırdaydı — reply_video exception atarsa close çağrılmıyor,
            # buffer GC'ye kalıyor (Railway 512MB plan'da OOM kill riski).
            # Şimdi try/finally ile close garantili.
            video_io = None
            try:
                import requests as req
                MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB Telegram limit
                CHUNK_SIZE = 1024 * 1024  # 1MB chunk

                def _download_video_streamed(url: str) -> io.BytesIO | None:
                    resp = req.get(url, timeout=120, stream=True)
                    try:
                        resp.raise_for_status()
                        content_length = resp.headers.get("Content-Length")
                        if content_length and int(content_length) > MAX_VIDEO_SIZE:
                            return None
                        buf = io.BytesIO()
                        downloaded = 0
                        for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                            downloaded += len(chunk)
                            if downloaded > MAX_VIDEO_SIZE:
                                buf.close()
                                return None
                            buf.write(chunk)
                        buf.seek(0)
                        return buf
                    finally:
                        resp.close()

                video_io = await asyncio.to_thread(_download_video_streamed, video_url)
                if video_io is not None:
                    video_io.name = "reklam_videosu.mp4"
                    await message.reply_video(
                        video=InputFile(video_io),
                        caption=f"🎬 {session.collected_data.get('brand_name', '')} — "
                                f"{session.collected_data.get('product_name', '')}",
                    )
                else:
                    log.warning("Video 50MB'ı aşıyor — Telegram'a gönderilemedi, URL paylaşıldı")
            except Exception:
                log.warning("Video dosyası Telegram'a gönderilemedi — URL paylaşıldı", exc_info=True)
            finally:
                if video_io is not None:
                    try:
                        video_io.close()
                    except Exception:
                        pass

            conversation_mgr.mark_delivered(user_id)

            # ── Sosyal Medya Paylaşım Akışı ──
            # Video başarıyla teslim edildi; Upload-Post akışı tetikleniyor.
            log.info(f"Publishing flow başlatılıyor: user={user_id} video={video_url[:80]}")
            try:
                # brief_payload pipeline'dan geliyor; gelmediyse fallback session helper.
                session.brief_payload = (
                    result.get("brief_payload")
                    or session.to_brief_payload(video_url, "tr")
                )
                session.last_video_url = video_url
                # Notion page ID'yi sosyal log için sakla
                _np_id = result.get("_notion_page_id")
                if not _np_id and result.get("notion_page_url"):
                    _np_id = ProductionPipeline._extract_page_id(result["notion_page_url"])
                session.notion_page_id = _np_id
                log.info(
                    f"Publishing setup OK: brand={session.brief_payload.get('brand')!r} "
                    f"product={session.brief_payload.get('product')!r} np_id={_np_id}"
                )
                await _open_publishing_flow(message, user_id, video_url)
                log.info(f"Publishing flow control returned: state={session.state.name if hasattr(session.state, 'name') else session.state}")
            except Exception as e:
                log.error(
                    f"Publishing flow başlatılamadı: {type(e).__name__}: {e}",
                    exc_info=True,
                )
                # Silent fail olmasın — kullanıcıya Telegram'da açık geri bildirim
                try:
                    await message.reply_text(
                        f"⚠️ Sosyal medya paylaşım akışı açılamadı.\n\n"
                        f"Hata: {type(e).__name__}: {str(e)[:200]}\n\n"
                        f"📥 Video URL: {video_url}\n"
                        "Upload-Post dashboard'undan manuel paylaşabilirsin.",
                        parse_mode=None,
                    )
                except Exception:
                    pass

        else:
            error_raw = result.get("error", "")
            # Teknik detay debug için log'a
            log.error(
                "Production pipeline FAILED user=%s error_raw=%s",
                user_id,
                str(error_raw)[:500],
            )
            # Açık sub-stage'leri fail olarak kapat
            for _sub_id, _open in list(_produce_subs.items()):
                if _open:
                    run_emitter.fail_substage("produce", _sub_id, str(error_raw)[:200])
                    _produce_subs[_sub_id] = False
            run_emitter.fail_stage("produce", str(error_raw)[:200])
            run_emitter.fail_run(f"Üretim başarısız: {str(error_raw)[:200]}")
            user_msg = categorize_production_error(error_raw)
            error_msg = (
                f"❌ Üretim tamamlanamadı\n\n"
                f"{user_msg}\n\n"
                f"🔄 Tekrar link gönderebilirsin."
            )
            await message.reply_text(error_msg, parse_mode=None)
            await chat_tracker.log_interaction(str(user_id), "[Sistem - Hata]", error_msg)
            session.reset()

    except asyncio.CancelledError:
        # /cancel veya "❌ İptal" butonu → graceful kapanma
        log.info(f"Production pipeline iptal edildi (CancelledError): user={user_id}")
        # WHY: Eskiden cancel path'i run_emitter'a hiç dokunmuyordu —
        # dashboard'da produce stage + açık substage'ler sonsuza kadar
        # "active" kalıyordu, run header'ı hâlâ "running" gösteriyordu.
        # Açık substage'leri ve produce stage'ini fail olarak kapat, run'ı bitir.
        try:
            for _sid, _open in list(_produce_subs.items()):
                if _open:
                    run_emitter.fail_substage("produce", _sid, "İptal edildi")
            run_emitter.fail_stage("produce", "Üretim kullanıcı tarafından iptal edildi")
            run_emitter.fail_run("Üretim iptal edildi")
        except Exception:
            pass
        try:
            await message.reply_text(
                "🛑 Üretim iptal edildi — arka plandaki API çağrıları durduruluyor.",
                parse_mode=None,
            )
        except Exception:
            pass
        # Session zaten _cancel_user_production içinde reset edildi; emniyet için tekrar
        session.production_task = None
        raise  # Task'ın CANCELLED state'ine düşmesi için propagate et
    except Exception as _crash:
        log.error("Production pipeline çöktü", exc_info=True)
        # WHY: Eskiden sadece fail_run çağrılıyordu — produce stage ve açık
        # substage'ler "active" kalıyordu, dashboard'da run "error" ama
        # produce kutusu hâlâ dönüyor görünüyordu (tutarsız). Hepsini kapat.
        try:
            for _sid, _open in list(_produce_subs.items()):
                if _open:
                    run_emitter.fail_substage("produce", _sid, str(_crash)[:120])
            run_emitter.fail_stage("produce", f"{type(_crash).__name__}: {str(_crash)[:160]}")
            run_emitter.fail_run(f"Pipeline çökmesi: {type(_crash).__name__}: {str(_crash)[:200]}")
        except Exception:
            pass
        await message.reply_text(
            "💥 Kritik hata! Üretim sırasında beklenmeyen bir hata oluştu.\n"
            "🔄 Linki kontrol edip tekrar dene.",
            parse_mode=None,
        )
        session.reset()
    finally:
        # Üretim task referansını temizle (zaten cancel edildiyse no-op)
        if session.production_task is not None and session.production_task.done():
            session.production_task = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📤 SOSYAL MEDYA PAYLAŞIM AKIŞI (Upload-Post)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PLATFORM_ICONS = {
    "tiktok": "🎵", "youtube": "📺", "instagram": "📸",
    "x": "🐦", "linkedin": "💼", "threads": "🧵", "facebook": "📘",
}


def _make_upload_post_service() -> UploadPostService:
    """Tek noktadan UploadPostService instance üret."""
    return UploadPostService(
        api_key=settings.UPLOAD_POST_API_KEY,
        profile_name=settings.UPLOAD_POST_PROFILE,
    )


def _close_dashboard_run_on_publish_abort(reason: str) -> None:
    """Publishing flow erken çıkarsa dashboard koşusunu temiz kapat.

    WHY: _open_publishing_flow erken return ederse (Upload-Post bağlantı
    hatası, hiç platform bağlı değil vb.) dashboard'da `produce` stage
    completed kalıyor ama run sonsuza kadar "running" görünüyordu. Canlı
    demo sırasında ekran takılmış izlenimi veriyor. fail_run ile kapat.
    """
    try:
        run_emitter.fail_run(reason)
    except Exception:
        pass


async def _open_publishing_flow(message, user_id: int, video_url: str) -> None:
    """Video hazır → bağlı platformları listele + caption üret + multi-select buton göster."""
    log.info(f"_open_publishing_flow: girdi (user={user_id})")
    session = conversation_mgr.get_session(user_id)
    upload_svc = _make_upload_post_service()

    # 1) Bağlı platformlar
    log.info("_open_publishing_flow: list_connected_platforms çağrılıyor")
    try:
        connected = await asyncio.to_thread(upload_svc.list_connected_platforms)
        log.info(f"_open_publishing_flow: connected_platforms keys={list((connected or {}).keys())}")
    except UploadPostAuthError:
        _close_dashboard_run_on_publish_abort("Upload-Post bağlantısı geçersiz")
        await message.reply_text(
            "⚠️ Upload-Post bağlantısı geçersiz. Yöneticiye haber ver."
        )
        return
    except UploadPostError as e:
        log.error(f"Upload-Post connect error: {e}")
        _close_dashboard_run_on_publish_abort(f"Upload-Post hatası: {str(e)[:120]}")
        await message.reply_text(
            f"⚠️ Upload-Post hatası: {str(e)[:200]}\n\nVideo URL: {video_url}"
        )
        return
    except Exception as e:
        log.error(f"Upload-Post beklenmeyen hata: {e}", exc_info=True)
        _close_dashboard_run_on_publish_abort("Sosyal medya bağlantısı kurulamadı")
        await message.reply_text(
            f"⚠️ Sosyal medya bağlantısı kurulamadı.\n\nVideo URL: {video_url}"
        )
        return

    session.connected_platforms = connected or {}
    connected_keys = [p for p, info in session.connected_platforms.items()
                      if isinstance(info, dict) and info.get("connected")]

    # WHY: Upload-post bazı platformlar için token expire'da bile
    # connected=True dönüyor ama ek bir `reauth_required=True` flag ile
    # işaret ediyor. Eski sürüm bu flag'i okumuyordu — upload denenip
    # "Upload Failed" generic hatasıyla sessizce başarısız oluyordu.
    # Şimdi explicit uyarı bas ve flag'li platformları seçilebilir
    # listeden CIKARMA, sadece kullanıcıya hangilerini yenilemesi
    # gerektiğini söyle (kullanıcı yine de denemek isteyebilir).
    reauth_platforms = [
        p for p, info in session.connected_platforms.items()
        if isinstance(info, dict) and info.get("connected")
        and info.get("reauth_required")
    ]
    if reauth_platforms:
        await message.reply_text(
            "⚠️ Bazı platformların oturumu yenilenmeli (token expire): "
            f"{', '.join(reauth_platforms)}\n"
            "Upload-Post dashboard'undan yeniden bağla. "
            "Aksi halde paylaşım o platformlarda başarısız olacak."
        )

    if not connected_keys:
        _close_dashboard_run_on_publish_abort("Hiçbir sosyal medya hesabı bağlı değil")
        await message.reply_text(
            "📭 Hiçbir sosyal medya hesabın bağlı değil.\n\n"
            "Upload-Post dashboard'undan TikTok/YouTube/Instagram bağla.\n\n"
            f"Video URL: {video_url}"
        )
        return

    # 2) Caption üret
    captions: dict = {}
    log.info(f"_open_publishing_flow: caption üretici çağrılıyor (platforms={connected_keys})")
    run_emitter.start_stage("caption", sub_text=f"{len(connected_keys)} platform için caption üretiliyor")
    try:
        cg = CaptionGenerator(openai_svc)
        captions = await asyncio.to_thread(cg.generate, session.brief_payload, connected_keys)
        log.info(f"_open_publishing_flow: caption üretildi, keys={list((captions or {}).keys())}")
    except Exception as e:
        log.warning(f"Caption üretim hatası: {e}", exc_info=True)
        # Fallback: tek caption tüm platformlara
        brand = session.brief_payload.get("brand", "")
        product = session.brief_payload.get("product", "")
        fallback_text = f"{brand} {product}".strip() or "Yeni reklam videomuz!"
        for p in connected_keys:
            if p == "youtube":
                captions[p] = {"title": fallback_text[:80], "description": fallback_text, "tags": []}
            else:
                captions[p] = {"caption": fallback_text, "hashtags": []}

    # Caption ara çıktısı — ilk platformun özetini göster
    _first_cap = ""
    _first_tags: list = []
    for _p in connected_keys:
        _c = captions.get(_p)
        if isinstance(_c, dict):
            _first_cap = _c.get("caption") or _c.get("description") or _c.get("title") or ""
            _first_tags = _c.get("hashtags") or _c.get("tags") or []
            break
    run_emitter.end_stage("caption", payload={
        "platforms": connected_keys,
        "sample_text": (_first_cap or "")[:240],
        "hashtags": list(_first_tags)[:8],
    })

    session.captions = captions
    session.selected_platforms = set(connected_keys)  # default: hepsi seçili
    session.state = ConversationState.ASKING_PLATFORMS
    log.info(
        f"_open_publishing_flow: ASKING_PLATFORMS state set; "
        f"connected_keys={connected_keys}, captions_keys={list(captions.keys())}"
    )

    # 3) Mesaj + butonlar
    await _send_publishing_picker(message, session)


async def _send_publishing_picker(message, session, edit: bool = False) -> None:
    """Inline keyboard ile platform seçimi + paylaş butonu.

    NOT: Caption metinleri kullanıcı/LLM kaynaklı olduğundan `_`, `*`, `[`
    gibi Markdown V1 karakterleri içerebilir → format bozulması yerine
    parse_mode=None ile düz metin gönderiyoruz (Markdown emoji başlık kaybı
    kabul edilebilir; format hatasının vereceği UX bozulması daha kötü).
    """
    text_lines = ["🎬 Video hazır! Hangi platformlara paylaşalım?", ""]
    text_lines.append("📝 Caption önizleme:")

    # İlk seçili platformun caption'ını göster (override varsa onu göster)
    sample_text = ""
    if session.captions.get("_override"):
        sample_text = session.captions["_override"]
    else:
        sample_platform = next(iter(sorted(session.selected_platforms)), None)
        if sample_platform and isinstance(session.captions.get(sample_platform), dict):
            c = session.captions[sample_platform]
            sample_text = c.get("caption") or c.get("title") or c.get("description") or ""
            hashtags = c.get("hashtags") or []
            if hashtags:
                sample_text = (sample_text + " " + " ".join(f"#{h}" for h in hashtags[:5])).strip()
    if sample_text:
        # Caption metni `_` `*` `[` gibi Markdown özel karakteri içerebilir;
        # italic veya bold sarmalı parse hatası riski taşır → düz metin.
        text_lines.append(sample_text[:200])

    keyboard: list[list[InlineKeyboardButton]] = []
    for platform, info in session.connected_platforms.items():
        if not (isinstance(info, dict) and info.get("connected")):
            continue
        icon = PLATFORM_ICONS.get(platform, "🔗")
        username = info.get("username", "") or ""
        check = "✅" if platform in session.selected_platforms else "⬜"
        label = f"{check} {icon} {platform.title()}"
        if username:
            label += f" {username}"
        keyboard.append([InlineKeyboardButton(label[:60], callback_data=f"pub:toggle:{platform}")])

    keyboard.append([InlineKeyboardButton("✏️ Caption Düzenle", callback_data="pub:edit_caption")])
    keyboard.append([
        InlineKeyboardButton("🚀 Şimdi Paylaş", callback_data="pub:share"),
        InlineKeyboardButton("❌ İptal", callback_data="pub:cancel"),
    ])

    text = "\n".join(text_lines)
    markup = InlineKeyboardMarkup(keyboard)

    if edit and session.publishing_message_id:
        try:
            await message.get_bot().edit_message_text(
                chat_id=message.chat_id,
                message_id=session.publishing_message_id,
                text=text,
                reply_markup=markup,
                parse_mode=None,
            )
            return
        except Exception:
            log.warning("Publishing picker edit failed, sending new message", exc_info=True)

    sent = await _safe_reply(message, text, reply_markup=markup, parse_mode=None)
    session.publishing_message_id = sent.message_id
    log.info(f"Publishing picker gönderildi: message_id={sent.message_id}")


async def _publish_and_track(message, user_id: int) -> None:
    """Upload-Post'a yolla, polling et, sonuç linklerini göster."""
    session = conversation_mgr.get_session(user_id)
    upload_svc = _make_upload_post_service()

    video_url = (
        session.brief_payload.get("video_url")
        or session.last_video_url
        or ""
    )
    platforms = sorted(session.selected_platforms)

    # Override caption varsa hepsi için aynı metin kullanılır
    captions_to_send: dict = dict(session.captions or {})
    override = captions_to_send.pop("_override", None)
    if override:
        for p in platforms:
            if p == "youtube":
                captions_to_send[p] = {
                    "title": override[:80],
                    "description": override,
                    "tags": [],
                }
            else:
                captions_to_send[p] = {"caption": override, "hashtags": []}

    # Progress mesajını güncelle
    progress_text = "🚀 *Paylaşılıyor...*\n\n" + "\n".join(
        f"⏳ {PLATFORM_ICONS.get(p, '🔗')} {p.title()}" for p in platforms
    )
    try:
        await message.get_bot().edit_message_text(
            chat_id=message.chat_id,
            message_id=session.publishing_message_id,
            text=progress_text,
            parse_mode="Markdown",
        )
    except Exception:
        try:
            sent = await message.reply_text(progress_text, parse_mode="Markdown")
            session.publishing_message_id = sent.message_id
        except Exception:
            log.warning("Progress mesajı oluşturulamadı", exc_info=True)

    try:
        run_emitter.start_stage("upload", sub_text=f"{', '.join(platforms)} → Upload-Post kuyruğa alındı")
        upload_result = await asyncio.to_thread(
            upload_svc.upload_video,
            video_url=video_url,
            platforms=platforms,
            captions=captions_to_send,
            async_upload=True,
        )
        request_id = (upload_result or {}).get("request_id")
        session.upload_request_id = request_id

        if request_id:
            run_emitter.update_stage("upload", sub_text="Yayınlanma durumu polling ediliyor")
            status = await asyncio.to_thread(upload_svc.poll_status, request_id, 180, 5)
        else:
            status = upload_result or {}

        session.post_results = status.get("results", {}) if isinstance(status, dict) else {}
        errors = (status.get("errors") if isinstance(status, dict) else None) or {}
        upload_status = (status.get("status") if isinstance(status, dict) else "") or ""

        # Header — durum bazlı (timeout/failed varken "tamam" yalanı verme)
        ok_count = sum(
            1 for p, info in session.post_results.items()
            if isinstance(info, dict)
            and info.get("success") is not False
            and p not in errors
        )
        fail_count = len(errors)
        if fail_count == 0 and ok_count and upload_status in ("completed", "success", "succeeded"):
            header = "🎉 *Paylaşım Tamam!*"
        elif ok_count and fail_count:
            header = f"⚠️ *Kısmi Paylaşım* — {ok_count} başarılı, {fail_count} hatalı"
        elif fail_count and not ok_count:
            header = "❌ *Paylaşım Başarısız*"
        elif upload_status == "timeout":
            header = "⏳ *Paylaşım Sürüyor* (timeout — sonuç bilinmiyor)"
        elif ok_count == 0 and fail_count == 0:
            # WHY: Upload-Post bazen boş results + boş errors döndürüyor (ör.
            # async_upload=True iken request_id alınamadıysa veya
            # poll_status hâlâ "processing" iken döndüysek). Eski sürüm
            # buna "🎉 Paylaşım Tamam!" diyordu — kullanıcı linklere
            # tıklamak istiyor, ama sonuç ekranında hiç link yok →
            # yanıltıcı. Dürüst mesaj: durum bilinmiyor.
            header = "⏳ *Paylaşım Durumu Belirsiz* — Upload-Post sonuç döndürmedi, dashboard'dan kontrol et"
        else:
            header = "🎉 *Paylaşım Tamam!*"

        result_lines = [header, ""]
        for platform, info in session.post_results.items():
            if platform in errors:
                continue  # hata satırı aşağıda zaten yazılacak
            if isinstance(info, dict) and info.get("success") is False:
                continue
            url = ""
            if isinstance(info, dict):
                url = info.get("url") or info.get("post_url") or info.get("video_url") or ""
            icon = PLATFORM_ICONS.get(platform, "🔗")
            if url:
                result_lines.append(f"{icon} {platform.title()}: {url}")
            else:
                result_lines.append(f"{icon} {platform.title()}: ✅ (link bekleniyor)")

        # Hatalı platformlar
        if errors:
            result_lines.append("")
            for platform, err in errors.items():
                icon = PLATFORM_ICONS.get(platform, "🔗")
                result_lines.append(f"❌ {icon} {platform.title()}: {str(err)[:120]}")

        keyboard = [[InlineKeyboardButton("✅ Tamam", callback_data="pub:done")]]
        try:
            await message.get_bot().edit_message_text(
                chat_id=message.chat_id,
                message_id=session.publishing_message_id,
                text="\n".join(result_lines),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        except Exception:
            await message.reply_text("\n".join(result_lines), reply_markup=InlineKeyboardMarkup(keyboard))

        session.state = ConversationState.PUBLISHED

        # Dashboard: upload + run kapanışı
        try:
            _post_urls: dict[str, str] = {}
            for _pl, _info in (session.post_results or {}).items():
                if isinstance(_info, dict):
                    _u = _info.get("url") or _info.get("post_url") or _info.get("video_url") or ""
                    if _u:
                        _post_urls[_pl] = _u
            if errors and not _post_urls:
                run_emitter.fail_stage("upload", f"Tüm platformlar başarısız: {list(errors.keys())}")
                run_emitter.fail_run("Sosyal medya paylaşımı başarısız")
            else:
                run_emitter.end_stage("upload", payload={
                    "post_urls": _post_urls,
                    "platforms": platforms,
                    "errors": list(errors.keys()) if errors else [],
                })
                run_emitter.end_run(final_payload={"final_video_url": video_url})
        except Exception:
            log.warning("Dashboard end-of-run emit hatası", exc_info=True)

        # Notion'a log
        try:
            page_id = session.notion_page_id
            if page_id:
                await asyncio.to_thread(
                    notion_svc.log_social_posting,
                    page_id=page_id,
                    platforms=platforms,
                    post_results=session.post_results,
                    status="Paylaşıldı",
                )
        except Exception as e:
            log.warning(f"Notion social log fail: {e}")

    except asyncio.CancelledError:
        # WHY: Kullanıcı "❌ İptal" basınca _handle_pub_callback publish_task'ı
        # cancel ediyor → buraya CancelledError düşüyor. Graceful kapanma:
        # session zaten cancel handler tarafında reset edildi; bu task'ın
        # asyncio'ya CANCELLED olarak dönmesi için raise et — yoksa
        # _handle_task_exception ERROR loglar.
        log.info(f"Publish task graceful cancel: user={user_id}")
        try:
            run_emitter.fail_run("Paylaşım kullanıcı tarafından iptal edildi")
        except Exception:
            pass
        raise
    except UploadPostAuthError:
        try:
            run_emitter.fail_stage("upload", "Upload-Post bağlantısı geçersiz (token)")
            run_emitter.fail_run("Upload-Post auth hatası")
        except Exception:
            pass
        try:
            await message.get_bot().edit_message_text(
                chat_id=message.chat_id,
                message_id=session.publishing_message_id,
                text="❌ Upload-Post bağlantısı geçersiz. Yöneticiye haber ver.",
            )
        except Exception:
            await message.reply_text("❌ Upload-Post bağlantısı geçersiz. Yöneticiye haber ver.")
        session.reset()
    except Exception as e:
        log.error(f"Publish error: {e}", exc_info=True)
        try:
            run_emitter.fail_stage("upload", str(e)[:200])
            run_emitter.fail_run(f"Paylaşım hatası: {str(e)[:200]}")
        except Exception:
            pass
        err_msg = (
            f"⚠️ Paylaşım hatası: {str(e)[:200]}\n\n"
            f"request_id: {session.upload_request_id or 'yok'}\n\n"
            f"Video: {video_url}"
        )
        try:
            await message.get_bot().edit_message_text(
                chat_id=message.chat_id,
                message_id=session.publishing_message_id,
                text=err_msg,
            )
        except Exception:
            await message.reply_text(err_msg)
        session.reset()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚠️ GLOBAL HATA HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_CRASHED_WITH_CONFLICT = False

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global hata yakalayıcı — Telegram bot'un çökmesini önler."""

    # Sadece exc_info'yu eğer The context.error is set, to prevent NoneType logging
    err_str = str(context.error)
    # Transient Telegram API hataları (502/504/timeout/network) kullanıcıyı da
    # etkilemiyor; ERROR yerine WARNING — watchdog gürültüsünü önle.
    _transient = ("Bad Gateway", "Timed out", "NetworkError", "httpx",
                  "Connection", "Gateway Time-out", "Service Unavailable")
    if any(t in err_str for t in _transient):
        log.warning(f"Telegram transient hatası: {err_str}")
    else:
        log.error(f"Telegram handler hatası: {err_str}")

    try:
        # isinstance ile tip kontrolü — string match kırılgan
        if isinstance(context.error, Conflict) or "getUpdates" in err_str:
            global _CRASHED_WITH_CONFLICT
            if not _CRASHED_WITH_CONFLICT:
                _CRASHED_WITH_CONFLICT = True
                log.warning(
                    "🔄 Conflict algılandı! run_polling durduruluyor → "
                    "process exit 75 → Railway temiz restart."
                )
                # WHY: error_handler eskiden SADECE flag set ediyordu. Ama
                # python-telegram-bot run_polling() Conflict'te kendi içinde
                # sonsuza kadar getUpdates retry ediyor — RETURN ETMİYOR.
                # Dolayısıyla main()'deki `if _CRASHED_WITH_CONFLICT: sys.exit(75)`
                # satırına hiç ulaşılmıyordu. 2026-05-14: unutulmuş bir lokal
                # ghost instance yüzünden production bot 4+ saat sessizce
                # conflict-loop'ta kaldı (her getUpdates 409, bot fiilen ölü).
                # stop_running() run_polling'i zorla döndürür → exit 75 →
                # Railway ON_FAILURE policy konteyneri temiz restart eder ve
                # eski polling session gerçekten ölmüş olur.
                try:
                    context.application.stop_running()
                except Exception as stop_exc:
                    log.error(f"stop_running çağrısı başarısız: {stop_exc}")

    except Exception as check_exc:
        log.error(f"Conflict kontrolü sırasında hata: {check_exc}")

    if update and update.effective_message:
        # TIMEOUT veya NETWORK ERROR gibi durumlarda (örneğin video yüklerken) 
        # kullanıcıya yanıltıcı "Hata" mesajı gönderme.
        if any(e in err_str for e in ["Timed out", "NetworkError", "httpx", "Connection"]):
            log.warning("Kullanıcıya mesaj gönderilmeyecek (Timeout/NetworkError).")
            return

        try:
            await update.effective_message.reply_text(
                "⚠️ Bir hata oluştu. Lütfen tekrar dene.",
                parse_mode="Markdown",
            )
        except Exception as fallback_exc:
            log.error(f"Kullanıcıya mesaj gönderilemedi: {fallback_exc}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 UYGULAMA BAŞLATMA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    """Bot'u başlat ve polling modunda çalıştır."""
    global _CRASHED_WITH_CONFLICT
    _CRASHED_WITH_CONFLICT = False

    mode = "🏜️ DRY-RUN" if settings.IS_DRY_RUN else "🟢 PRODUCTION"
    log.info(f"🚀 eCom Reklam Otomasyonu v3.0 başlatılıyor... [Mod: {mode}]")
    log.info(f"📊 Model: {settings.OPENAI_MODEL}")
    log.info(f"👤 İzinli kullanıcılar: {settings.ALLOWED_USER_IDS}")

    # WHY: Video upload (10-30MB) + uzun render sırasında progress mesajları
    # 30s timeout'a takılıp "bot ölü" hissi veriyordu. Telegram MTProto için
    # 60s comfort zone; pool_timeout ise concurrent send'lerde slot bekler.
    app = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .connect_timeout(60)
        .read_timeout(60)
        .write_timeout(120)  # send_video için uzun upload süresi
        .pool_timeout(60)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("help", cmd_help))

    # Tek mesaj dinleyicisi: Linkleri algılar
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Inline button callback
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Global hata handler
    app.add_error_handler(error_handler)

    # Post-init: webhook temizle + session cleanup başlat
    async def _post_init(app_instance):
        # Conflict hatasını önle: eski webhook/polling session'ını temizle
        try:
            await app_instance.bot.delete_webhook(drop_pending_updates=True)
            log.info("✅ Webhook temizlendi, Telegram bağlantısının kesilmesi için 5 saniye bekleniyor...")
            await asyncio.sleep(5)  # Ghost instance ve 409 riskine karşı uzatılmış bekleme
        except Exception as e:
            log.warning(f"Webhook silme uyarısı (devam ediliyor): {e}")

        # WHY: Notion bağlantısı startup'ta sağlam değilse üretim sırasında
        # sessizce "log_production None döndü" durumu oluşur — admin "neden
        # Notion'da görmüyorum" der ama log'larda da gömülü kalır. Burada
        # patladıysa bilinçli olarak büyük ERROR bas; bot yine başlasın çünkü
        # video üretimi Notion'dan bağımsız çalışabilir.
        try:
            ok, msg = await asyncio.to_thread(notion_svc.health_check)
            if ok:
                log.info("✅ Notion bağlantısı sağlıklı (DB erişilebilir)")
            else:
                log.error(
                    f"⚠️ NOTION STARTUP CHECK BAŞARISIZ: {msg} — "
                    f"üretim logları KAYDEDILEMEYECEK ama bot devam edecek"
                )
        except Exception as e:
            log.error(f"Notion health check beklenmedik hata: {e}", exc_info=True)

        # Session bellek temizleme task'ı (referansı bot_data'da tut — GC'ye karşı)
        cleanup_task = asyncio.create_task(_cleanup_idle_sessions(app_instance), name="session-cleanup")
        cleanup_task.add_done_callback(_handle_task_exception)
        app_instance.bot_data.setdefault("bg_tasks", set()).add(cleanup_task)
        cleanup_task.add_done_callback(app_instance.bot_data["bg_tasks"].discard)

        # Canlı dashboard (sadece DASHBOARD_ENABLED=1 ise — production'da kapalı)
        if os.getenv("DASHBOARD_ENABLED", "0") == "1":
            try:
                from dashboard_server import start_dashboard
                dash_task = asyncio.create_task(start_dashboard(), name="dashboard-server")
                dash_task.add_done_callback(_handle_task_exception)
                app_instance.bot_data["bg_tasks"].add(dash_task)
                dash_task.add_done_callback(app_instance.bot_data["bg_tasks"].discard)
                log.info("📊 Canlı dashboard aktif → http://localhost:%s",
                         os.getenv("DASHBOARD_PORT", "8000"))
            except Exception as e:
                log.warning(f"Dashboard başlatılamadı (devam ediliyor): {e}", exc_info=True)

    app.post_init = _post_init

    log.info("🤖 Telegram polling başlatılıyor...")
    
    try:
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            poll_interval=1.0,
            timeout=30,
        )
    except Exception as e:
        log.error(f"Polling sırasında hata: {e}")

    if _CRASHED_WITH_CONFLICT:
        # 409 Conflict: aynı bot token'ı için başka bir polling session var.
        # Internal restart loop yerine process'i exit code 75 (TEMPFAIL) ile
        # bitir; Railway konteyneri yeniden başlatır ve eski polling session
        # gerçekten ölmüş olur. Internal retry'da telegram-bot kütüphanesinin
        # iç state'i tam temizlenmediği için 409 dönüp duruyordu.
        log.error("⚠️ Telegram Conflict (409) - process restart edilecek (exit 75)")
        sys.exit(75)


if __name__ == "__main__":
    import time as _startup_time

    MAX_RESTARTS = 10
    restart_count = 0

    while restart_count < MAX_RESTARTS:
        try:
            main()
            # app.run_polling() genelde sadece hata durumunda veya manuel durdurulduğunda döner.
            # KeyboardInterrupt veya SystemExit dışında buraya ulaşıldıysa beklenmedik bir duruştur.
            raise RuntimeError("Telegram polling döngüsü beklenmedik şekilde sonlandı (Muhtemel Conflict 409).")
        except SystemExit as se:
            # WHY: main() Conflict 409'da `sys.exit(75)` çağırıyor. Eski kod
            # bu SystemExit'i yutup `break` ediyordu → process exit 0 ile
            # kapanıyordu. Railway `restartPolicyType: ON_FAILURE` exit 0'ı
            # "başarılı çıkış" sayıp konteyneri RESTART ETMİYORDU — yani
            # Conflict recovery zincirinin ikinci kırık halkası. Sıfır-dışı
            # exit kodlarını (75 = Conflict TEMPFAIL) propagate et ki Railway
            # konteyneri gerçekten yeniden başlatsın.
            if se.code not in (None, 0):
                log.error(
                    f"Bot exit kodu {se.code} ile kapanıyor — Railway "
                    f"konteyner restart'ı bekleniyor."
                )
                raise
            log.info("Bot sistem çağrısıyla durduruldu (temiz çıkış).")
            break  # Bilerek temiz kapatıldı (exit 0)
        except KeyboardInterrupt:
            log.info("Bot kullanıcı tarafından durduruldu (Ctrl+C).")
            break
        except Exception as e:
            restart_count += 1
            log.error(
                f"💥 Bot çöktü veya durdu (restart {restart_count}/{MAX_RESTARTS}): {e}"
            )
            if restart_count < MAX_RESTARTS:
                wait = min(5 * restart_count, 30)
                log.info(f"🔄 {wait} saniye sonra yeniden başlatılıyor...")
                _startup_time.sleep(wait)
            else:
                log.error("❌ Maksimum restart sayısına ulaşıldı, bot durduruluyor")
                sys.exit(1)
