"""
Akıllı Watchdog — Konfigürasyon Modülü
LLM-destekli pipeline sağlık kontrolü.

Bu dosya senin izleyeceğin servislerin envanteridir.
Aşağıdaki MONITORED_PROJECTS listesine kendi projelerini ekle.
İki örnek satır bırakıldı — birini Notion + Railway için, birini
sadece Railway için kullan, sonra kendi değerlerinle çoğalt.

İzlenebilen pipeline tipleri:
  - custom_notion : Notion DB + Railway servisi olan proje
  - railway_only  : Sadece Railway servisi olan proje (Notion DB yok)

Ek katmanlar:
  - Token Freshness: OAuth2 token expire takibi (TOKEN_EXPIRY_TRACKING)
  - Railway Probe: Aktif projelerin son deployment durumu kontrolü
"""
import os
from datetime import datetime, timezone, timedelta
import json
import logging
from adapter_logger import get_logger

logger = get_logger(__name__)


def _parse_tabs(csv_str: str) -> list[str]:
    """Virgülle ayrılmış tab isimlerini parse eder."""
    return [t.strip() for t in csv_str.split(",") if t.strip()]


class Config:
    """Environment variable tabanlı konfigürasyon."""

    # ── Groq LLM ──────────────────────────────────────────
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_BASE_URL = os.environ.get(
        "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
    )
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    # ── Alarm ─────────────────────────────────────────────
    # Alarm maillerinin gideceği adres — .env dosyasından doldur.
    ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")

    # Gmail API OAuth2 (SMTP yerine — Railway port engellemesi nedeniyle)
    # Railway: GOOGLE_OUTREACH_TOKEN_JSON env variable
    # Lokal: Merkezi google_auth modülü otomatik kullanılır

    # ── Notion ─────────────────────────────────────────────
    NOTION_API_TOKEN = os.environ.get("NOTION_API_TOKEN", "")
    NOTION_SOCIAL_TOKEN = os.environ.get("NOTION_SOCIAL_TOKEN", "")
    # Varsayılan DB ID'sini .env dosyasından NOTION_DATABASE_ID ile ver.
    NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")

    # Token registry — proje config'inde notion_token_key ile referans edilir
    NOTION_TOKENS = {
        "NOTION_API_TOKEN": os.environ.get("NOTION_API_TOKEN", ""),
        "NOTION_SOCIAL_TOKEN": os.environ.get("NOTION_SOCIAL_TOKEN", ""),
    }

    @classmethod
    def get_notion_token(cls, token_key: str) -> str:
        """Proje config'indeki token_key'e göre doğru Notion token'ı döner."""
        return cls.NOTION_TOKENS.get(token_key, cls.NOTION_API_TOKEN)

    # ── Google Auth (Production: Service Account) ─────────
    GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

    # ── İzlenen Projeler ──────────────────────────────────
    # TODO: Aşağıdaki iki örnek satırı kendi projelerinle değiştir/çoğalt.
    # Notion DB ID ve Railway service ID değerlerini .env'den oku veya
    # doğrudan buraya kendi ID'lerini yaz.
    MONITORED_PROJECTS = [

        # ── Örnek 1: Notion + Railway projesi ─────────────────
        {
            "name": "Örnek Notion Projesi",
            "spreadsheet_id": "",
            "sheet_tabs": [],
            "expected_columns": [],
            "expected_column_keywords": [],
            "pipeline": "custom_notion",
            "notion_token_key": "NOTION_API_TOKEN",
            "notion_db_id": os.environ.get("NOTION_DB_ORNEK", "<NOTION_DB_ID>"),
            "notion_properties": ["Name", "Status"],
            "expected_daily_activity": False,
            "railway_service_id": os.environ.get(
                "RAILWAY_SERVICE_ID_ORNEK", "<RAILWAY_SERVICE_ID>"
            ),
        },

        # ── Örnek 2: Sadece Railway projesi (Notion DB yok) ───
        {
            "name": "Örnek Railway Servisi",
            "spreadsheet_id": "",
            "sheet_tabs": [],
            "expected_columns": [],
            "expected_column_keywords": [],
            "pipeline": "railway_only",
            "railway_service_id": os.environ.get(
                "RAILWAY_SERVICE_ID_ORNEK_2", "<RAILWAY_SERVICE_ID>"
            ),
            # Opsiyonel: dış HTTP health-check endpoint'i
            # "health_endpoint": "https://ornek-servis.up.railway.app/health",
        },

    ]

    # ── Token Expire Takibi ─────────────────────────────
    # OAuth2 token expire takibi yapmak istersen buraya
    # {"name": ..., "env_var": ..., "warn_days": 14} formatında ekle.
    TOKEN_EXPIRY_TRACKING = []

    # ── Railway Deployment Probe ────────────────────────
    RAILWAY_TOKEN = os.environ.get("RAILWAY_TOKEN", "")
    RAILWAY_GRAPHQL_URL = "https://backboard.railway.com/graphql/v2"

    @classmethod
    def get_railway_service_ids(cls) -> list[dict]:
        """Aktif projelerin Railway service ID'lerini toplar."""
        services = []
        for project in cls.MONITORED_PROJECTS:
            sid = project.get("railway_service_id")
            if sid:
                services.append({
                    "name": project["name"],
                    "service_id": sid,
                })
        return services

    # ── Zamanlama ────────────────────────────────────────
    CHECK_INTERVAL_HOURS = int(os.environ.get("CHECK_INTERVAL_HOURS", "24"))

    @classmethod
    def validate(cls) -> bool:
        """Zorunlu konfigürasyon değerlerini kontrol eder."""
        errors = []

        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY tanımlı değil")

        if errors:
            error_msg = f"Eksik konfigürasyon nedeniyle uygulama başlatılamadı: {', '.join(errors)}"
            for err in errors:
                logger.error(f"❌ Config hatası: {err}")
            raise EnvironmentError(error_msg)

        logger.info("✅ Konfigürasyon doğrulandı")
        return True

    @classmethod
    def get_google_credentials_info(cls):
        """Google credentials bilgisini döner."""
        if cls.GOOGLE_SERVICE_ACCOUNT_JSON:
            try:
                return json.loads(cls.GOOGLE_SERVICE_ACCOUNT_JSON)
            except json.JSONDecodeError:
                logger.error("GOOGLE_SERVICE_ACCOUNT_JSON parse edilemedi")
                return None
        return None
