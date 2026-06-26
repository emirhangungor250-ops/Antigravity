# -*- coding: utf-8 -*-
"""Merkezi konfigürasyon — YouTube Yorum Otomasyonu.

Lokalde `_knowledge/credentials/master.env` okunur (varsa).
Production'da env var'lar doğrudan set edilir (YOUTUBE_*, SUPABASE_*, VOYAGE_*, OPENAI_*).

Faz 1 (rapor + öğrenme) sadece YOUTUBE_API_KEY ister (OAuth yok).
Faz 2 (oto-cevap) ayrıca youtube.force-ssl OAuth token'ı ister.

Kanala/kişiye özel tüm değerler env'den okunur; kodda sabit değer yoktur.
"""
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(PROJECT_DIR, "..", ".."))
OAUTH_DIR = os.path.join(REPO_ROOT, "_knowledge", "credentials", "oauth")
MASTER_ENV = os.path.join(REPO_ROOT, "_knowledge", "credentials", "master.env")


def load_env():
    """master.env varsa os.environ'a yükle (mevcut değerleri EZME — gerçek env kazanır)."""
    if os.path.exists(MASTER_ENV):
        for line in open(MASTER_ENV, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


load_env()

# ── Kanal ────────────────────────────────────────────────
# Hangi YouTube kanalının yorumları taranacak. UC... ile başlayan kanal ID'si.
CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID", "")
# Loglarda/mailde görünen kanal adı (kozmetik). Boşsa kanal ID kullanılır.
CHANNEL_TITLE = os.environ.get("YOUTUBE_CHANNEL_TITLE", "") or CHANNEL_ID or "Kanalım"

# ── Creator kimliği (LLM prompt'larında kullanılır) ──────
# AI'nın kimin sesiyle yorum sınıflayıp cevap yazacağı. Kendi profilini yaz.
# CREATOR_NAME: kanalın/içerik üreticisinin adı (ör. "Ada Yılmaz").
# CREATOR_BIO: tek satır tanım (ör. "yemek tarifi paylaşan bir YouTuber").
CREATOR_NAME = os.environ.get("YT_CREATOR_NAME", "") or CHANNEL_TITLE
CREATOR_BIO = os.environ.get("YT_CREATOR_BIO", "kendi konusunda içerik üreten bir YouTuber")

# ── YouTube Data API ─────────────────────────────────────
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")          # okuma (Faz 1)
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "")      # yazma OAuth (Faz 2)
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
# force-ssl token: lokalde dosya, Railway'de env JSON
YT_TOKEN_PATH = os.path.join(PROJECT_DIR, "youtube_forcessl_token.json")
YT_TOKEN_ENV = "YOUTUBE_FORCESSL_TOKEN_JSON"
YT_WRITE_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# ── Tarama / hacim ───────────────────────────────────────
# Yeni yorum penceresi: son N gün içinde gelen, henüz raporlanmamış yorumlar.
# 7 gün: hafta sonu / kısa kesinti olsa bile yorum kaçmasın. Tekrarı idempotency (DB) önler,
# yani pencereyi genişletmek "aynı yorumu iki kez raporlama" riski yaratmaz.
COMMENT_LOOKBACK_DAYS = int(os.environ.get("YT_LOOKBACK_DAYS", "7"))
# allThreadsRelatedToChannelId tüm geçmişi değil yakın bir alt kümeyi döndürür (~ son aylar).
# Tavanı yüksek tut: API ne döndürürse tamamını al -> corpus seed maksimum, rapor garanti.
MAX_THREADS_PER_RUN = int(os.environ.get("YT_MAX_THREADS", "1500"))
MAX_EMAIL_CARDS = int(os.environ.get("YT_MAX_EMAIL_CARDS", "40"))    # tek mailde kart tavanı (hepsi DB'de)

# ── Supabase (corpus + durum) ────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# ── Embedding (Voyage, repo standardı = voyage-3 / 1024d) ─
VOYAGE_API_KEY = os.environ.get("VOYAGE_API_KEY", "")
EMBEDDING_MODEL = os.environ.get("YT_EMBEDDING_MODEL", "voyage-3")
EMBED_DIM = 1024

# ── LLM (varsayılan: gpt-4.1-mini @ OpenAI direkt) ─────────
# Yönlendirme (core/llm.py): model adında "/" VARSA -> OpenRouter; YOKSA -> OpenAI direkt.
# gpt-4.1-mini ucuz + Türkçe kısa-yaratıcı işlerde güçlü; model env'den değiştirilebilir.
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENAI_DIRECT_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_DIRECT_KEY = os.environ.get("OPENAI_API_KEY_DATA_SHARED", "") or os.environ.get("OPENAI_API_KEY", "")

WORTH_MODEL = os.environ.get("YT_WORTH_MODEL", "gpt-4.1-mini")   # yorum sınıflama (sıralama sinyali)
REPLY_MODEL = os.environ.get("YT_REPLY_MODEL", "gpt-4.1-mini")   # Faz 2 cevap üretimi + güven

# ── Mail raporu (Resend + doğrulanmış kendi domain'in) ────
# Gmail API ile kendine gönderimde DKIM imzalanmadığı için "kimliği doğrulanamadı"
# uyarısı çıkabiliyor. Resend + kendi domain'inde DKIM/SPF/DMARC kurarak bu çözülür.
# Tüm adresler env'den gelir; sabit kişisel adres yoktur.
RECIPIENT = os.environ.get("YT_REPORT_TO", "")           # raporu kim alacak
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
REPORT_FROM = os.environ.get("YT_REPORT_FROM", "")       # ör. Asistan <asistan@senin-domain.com>
REPORT_REPLY_TO = os.environ.get("YT_REPORT_REPLY_TO", "") or RECIPIENT

# Faz 2 onay/yanıt web servisi (mail butonları buraya gelir)
APPROVAL_BASE_URL = os.environ.get("YT_APPROVAL_BASE_URL", "").rstrip("/")
APPROVAL_SECRET = os.environ.get("YT_APPROVAL_SECRET", "")

# Kopyala sayfası (sunucusuz statik host — eşlik eden YouTube_Kopya_Sayfa projesi).
# Mailde "Cevabı kopyala" butonu buraya gider; cevap + YouTube linki link hash'inde taşınır,
# sayfa panoya kopyalar. URL = o servisin adresi (YT_COPY_PAGE_URL env'inden).
# Boşsa make_copy_url link üretmez -> kart otomatik YouTube derin linkine düşer (kırılmaz).
COPY_PAGE_URL = os.environ.get("YT_COPY_PAGE_URL", "").rstrip("/")

# ── Faz / güvenlik anahtarları ───────────────────────────
PHASE = int(os.environ.get("YT_PHASE", "1"))                       # 1=rapor+öğren, 2=AI cevapla
AUTO_POST_ENABLED = os.environ.get("YT_AUTO_POST", "0") == "1"     # Faz 2 gölge dönem freni
DRY_RUN = os.environ.get("YT_DRY_RUN", "0") == "1"                 # mail/yazma yapma, sadece logla
# corpus bu kadar gerçek cevaba ulaşınca rapora "Faz 2'ye hazırım" notu düşer
CORPUS_READY_THRESHOLD = int(os.environ.get("YT_CORPUS_READY", "50"))

# ── Mail kalite kapısı ───────────────────────────────────
# Rapora SADECE cevaplamaya değer yorum girsin; durgun günde maili çöple doldurma.
# Eşiğin altı + zayıf türler DB'ye ve corpus'a yine yazılır, sadece maile girmez.
# Sınıflama patlarsa fail-open: llm fallback score=60 (eşik üstü) -> emin değilken gizlemeyiz.
REPORT_MIN_SCORE = int(os.environ.get("YT_REPORT_MIN_SCORE", "55"))
REPORT_KINDS = {"question", "substantive"}   # maile girebilen türler (praise/emoji_only/spam elenir)


def missing_phase1_keys() -> list[str]:
    """Faz 1 için zorunlu anahtarlar — eksikse erken ve net patla."""
    out = []
    if not CHANNEL_ID:
        out.append("YOUTUBE_CHANNEL_ID")
    if not YOUTUBE_API_KEY:
        out.append("YOUTUBE_API_KEY")
    if not SUPABASE_URL:
        out.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        out.append("SUPABASE_SERVICE_ROLE_KEY")
    if not VOYAGE_API_KEY:
        out.append("VOYAGE_API_KEY")
    if not RESEND_API_KEY:
        out.append("RESEND_API_KEY")
    return out
