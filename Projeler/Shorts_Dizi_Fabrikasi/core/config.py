import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger("Config")

# Lokal calismada .env dosyasini yukle (Railway'de env zaten setli)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


class Config:
    def __init__(self):
        self.ENV = os.environ.get("ENV", "development").lower()
        self.IS_DRY_RUN = self.ENV == "development" or os.environ.get("DRY_RUN", "0") == "1"

        _dev_default = "dev_placeholder" if self.IS_DRY_RUN else None

        self.KIE_API_KEY = self._require_env("KIE_API_KEY", default=_dev_default)
        self.ANTHROPIC_API_KEY = self._require_env("ANTHROPIC_API_KEY", default=_dev_default)
        self.IMGBB_API_KEY = self._require_env("IMGBB_API_KEY", default=_dev_default)

        self.KIE_BASE_URL = os.environ.get("KIE_BASE_URL", "https://api.kie.ai/api/v1/")
        # Maliyet notu: pahalı model (Opus/Sonnet) varsayılan OLMASIN. Senaryo
        # üretimi için ucuz model yeter; pahalı model istenirse BRAIN_MODEL env'i
        # ile bilinçli seçilir. Varsayılan ucuz/uygun model.
        self.BRAIN_MODEL = os.environ.get("BRAIN_MODEL", "claude-haiku-4-5")
        self.QC_MODEL = os.environ.get("QC_MODEL", "claude-haiku-4-5")

        # Drive: Railway'de JSON env var, lokalde oauth token dosyasi (google_auth.py cozer)
        self.GOOGLE_OUTREACH_TOKEN_JSON = os.environ.get("GOOGLE_OUTREACH_TOKEN_JSON", "")
        self.DRIVE_FOLDER_URL = os.environ.get("DRIVE_FOLDER_URL", "")

        self.KIE_CREDITS_PER_USD = float(os.environ.get("KIE_CREDITS_PER_USD", "200"))
        self.MAX_EPISODE_CREDITS = float(os.environ.get("MAX_EPISODE_CREDITS", "0"))

        # Railway cron uyumu: CLI arg verilmezse env'den okunur
        self.MODE = os.environ.get("MODE", "")
        self.SERI_SLUG = os.environ.get("SERI_SLUG", "")

        logger.info(f"Config loaded: ENV={self.ENV}, DRY_RUN={self.IS_DRY_RUN}, BRAIN={self.BRAIN_MODEL}")

    def _require_env(self, key, default=None):
        val = os.environ.get(key) or default
        if not val:
            raise EnvironmentError(f"CRITICAL STARTUP FAILURE: Gerekli ortam değişkeni {key} bulunamadı!")
        return val


try:
    settings = Config()
except EnvironmentError as e:
    print(f"BOOT ERROR: {e}")
    sys.exit(1)
