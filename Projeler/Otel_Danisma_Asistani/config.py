"""Merkezi config — repo kök master.env (varsa) + proje .env'inden yükler.

Fiyat servisi (Phase 1) hiçbir sır gerektirmez; bot (Phase 2) Groq + ManyChat +
Supabase ister. Bu yüzden bot anahtarları OPSİYONEL tutulur: eksikse /price çalışmaya
devam eder, /webhook kullanıma açıldığında ilgili anahtar runtime'da kontrol edilir.

Tüm gerçek değerler .env dosyanızdan gelir (bkz. .env.example). Repoya hiçbir anahtar
gömülü değildir.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
# Opsiyonel: starter kit kökünde paylaşılan bir credentials/master.env varsa onu da yükle.
MASTER_ENV = PROJECT_ROOT.parent.parent / "_knowledge" / "credentials" / "master.env"
LOCAL_ENV = PROJECT_ROOT / ".env"

if MASTER_ENV.exists():
    load_dotenv(MASTER_ENV)
if LOCAL_ENV.exists():
    load_dotenv(LOCAL_ENV, override=False)


@dataclass(frozen=True)
class Config:
    # --- LLM (Groq — ucuz workhorse; maliyet politikası gereği Opus/Sonnet API yasak) ---
    groq_api_key: str | None
    agent_model: str           # ana ajan + parse
    whisper_model: str         # ses transkripsiyon
    # --- ManyChat (kendi ManyChat hesabınızın API token'ı) ---
    manychat_token: str | None
    # --- Supabase (konuşma hafızası) ---
    supabase_url: str | None
    supabase_service_key: str | None
    # --- Görsel (gpt-4o-mini; maliyet politikası gereği gpt-4o/Opus/Sonnet YASAK) ---
    openai_api_key: str | None
    vision_model: str          # görsel betimleme modeli (sadece gpt-4o-mini)
    vision_max_mb: int         # görsel boyut üst sınırı (gpt-4o-mini sert limiti 8MB)
    # --- Medya sınıflandırma (Content-Type probe) ---
    media_probe_timeout: float  # HEAD/GET probe zaman aşımı (sn)
    # --- Mesaj birleştirme / burst coalesce (sadece zamanlama, LLM maliyeti YOK) ---
    coalesce_initial_ms: int   # ilk pencere (artçı mesajları toplama)
    coalesce_straggler_ms: int  # artçı pencere
    coalesce_max_iter: int     # iç/dış döngü üst sınırı
    coalesce_pool_size: int    # ayrılmış worker havuzu boyutu (anyio havuzunu açlığa düşürmesin)
    # --- davranış ---
    history_window: int        # ajana verilecek son mesaj sayısı
    dry_run: bool              # 1 ise ManyChat'e gerçekten göndermez (test)

    @staticmethod
    def from_env() -> "Config":
        return Config(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            agent_model=os.getenv("AGENT_MODEL", "openai/gpt-oss-120b"),
            whisper_model=os.getenv("WHISPER_MODEL", "whisper-large-v3"),
            manychat_token=os.getenv("MANYCHAT_TOKEN"),
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_service_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            vision_model=os.getenv("VISION_MODEL", "gpt-4o-mini"),
            vision_max_mb=int(os.getenv("VISION_MAX_MB", "8")),
            media_probe_timeout=float(os.getenv("MEDIA_PROBE_TIMEOUT", "5")),
            coalesce_initial_ms=int(os.getenv("COALESCE_INITIAL_MS", "3000")),
            coalesce_straggler_ms=int(os.getenv("COALESCE_STRAGGLER_MS", "1500")),
            coalesce_max_iter=int(os.getenv("COALESCE_MAX_ITER", "4")),
            coalesce_pool_size=int(os.getenv("COALESCE_POOL_SIZE", "16")),
            history_window=int(os.getenv("HISTORY_WINDOW", "15")),
            dry_run=os.getenv("DRY_RUN", "0") == "1",
        )


CONFIG = Config.from_env()
