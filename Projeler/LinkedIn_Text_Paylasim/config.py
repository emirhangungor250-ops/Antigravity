import os
import sys
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", "..", "_knowledge", "credentials", "master.env")
if os.path.exists(env_path):
    load_dotenv(env_path)

# Antigravity V2 Fail-Fast Environment Validation
class Config:
    def __init__(self):
        # 1. Environment mode
        self.ENV = os.environ.get("ENV", "development").lower()
        self.IS_DRY_RUN = self.ENV == "development" or os.environ.get("DRY_RUN", "0") == "1"

        # Perplexity — AI haberleri araştırması
        self.PERPLEXITY_API_KEY = self._require_env("PERPLEXITY_API_KEY")
        self.PERPLEXITY_BASE_URL = os.environ.get("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")

        # OpenAI — Post yazma (GPT-4.1) + Görsel prompt (GPT-4.1-mini)
        self.OPENAI_API_KEY = self._require_env("OPENAI_API_KEY")

        # Kie AI — Görsel üretme (Nano Banana 2)
        self.KIE_API_KEY = self._require_env("KIE_API_KEY")

        # Typefully — LinkedIn artık Typefully üzerinden yayınlanıyor (token expire derdi yok)
        self.TYPEFULLY_API_KEY = self._require_env("TYPEFULLY_API_KEY")
        self.TYPEFULLY_SOCIAL_SET_ID = int(self._require_env("TYPEFULLY_SOCIAL_SET_ID"))

        # Notion — Sosyal medya draft DB (Twitter projesiyle ortak)
        self.NOTION_TOKEN = self._require_env("NOTION_SOCIAL_TOKEN", os.environ.get("NOTION_TOKEN"))
        self.NOTION_X_DB_ID = self._require_env("NOTION_X_DB_ID")
        # Geriye uyumluluk: eski LinkedIn-only DB hâlâ kullanılabilir (örn. weekly-dedup)
        self.NOTION_LINKEDIN_DB_ID = os.environ.get("NOTION_LINKEDIN_DB_ID", "")

    def _require_env(self, key, default=None):
        """Fetches an environment variable, raises error if missing."""
        val = os.environ.get(key, default)
        if not val:
            raise EnvironmentError(f"CRITICAL STARTUP FAILURE: Gerekli ortam değişkeni {key} bulunamadı!")
        return val

# Instantiating the config globally so it fails fast on module load.
try:
    settings = Config()
except EnvironmentError as e:
    print(f"BOOT ERROR: {e}")
    sys.exit(1)
