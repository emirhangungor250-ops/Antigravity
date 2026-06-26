"""IG_Carousel_Cron — config & env."""

import sys

from env_loader import get_env


class Config:
    def __init__(self):
        self.ENV = (get_env("ENV") or "development").lower()
        self.IS_DRY_RUN = self.ENV == "development" or get_env("DRY_RUN") == "1"

        # Notion (Twitter_Text_Paylasim ile aynı DB)
        self.NOTION_TOKEN = self._require("NOTION_SOCIAL_TOKEN")
        self.NOTION_X_DB_ID = self._require("NOTION_X_DB_ID")

        # Kie AI
        self.KIE_API_KEY = self._require("KIE_API_KEY")
        self.KIE_MODEL = get_env("KIE_MODEL") or "nano-banana-2"

        # Vision (Gemini)
        self.GEMINI_API_KEY = self._require("GEMINI_API_KEY")
        self.VISION_MODEL = get_env("VISION_MODEL") or "gemini-2.5-flash"

        # Planner / Caption LLM
        self.LLM_PROVIDER = (get_env("LLM_PROVIDER") or "anthropic").lower()
        self.ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY") or ""
        self.OPENAI_API_KEY = get_env("OPENAI_API_KEY") or ""
        if self.LLM_PROVIDER == "anthropic":
            if not self.ANTHROPIC_API_KEY:
                raise EnvironmentError(
                    "CRITICAL STARTUP FAILURE: LLM_PROVIDER=anthropic ama ANTHROPIC_API_KEY yok"
                )
            self.WRITER_MODEL = get_env("WRITER_MODEL") or "claude-opus-4-7"
        else:
            if not self.OPENAI_API_KEY:
                raise EnvironmentError(
                    "CRITICAL STARTUP FAILURE: LLM_PROVIDER=openai ama OPENAI_API_KEY yok"
                )
            self.WRITER_MODEL = get_env("WRITER_MODEL") or "gpt-4o"

        # ImgBB (CDN)
        self.IMGBB_API_KEY = self._require("IMGBB_API_KEY")

        # Approval
        self.APPROVAL_BASE_URL = (get_env("APPROVAL_BASE_URL") or "").rstrip("/")
        self.APPROVAL_SECRET = get_env("APPROVAL_SECRET") or ""

        # Carousel davranış
        self.SLIDE_COUNT = int(get_env("SLIDE_COUNT") or 7)
        self.VISION_SCORE_THRESHOLD = int(get_env("VISION_SCORE_THRESHOLD") or 7)
        self.VISION_MAX_RETRY = int(get_env("VISION_MAX_RETRY") or 2)
        # Argument body sunum formatı (bullets_highlighted = madde işaretli + sayı vurgu)
        self.BODY_FORMAT = (get_env("BODY_FORMAT") or "bullets_highlighted").lower()

    def _require(self, key: str) -> str:
        val = get_env(key)
        if not val:
            raise EnvironmentError(f"CRITICAL STARTUP FAILURE: {key} bulunamadı")
        return val


try:
    settings = Config()
except EnvironmentError as e:
    print(f"BOOT ERROR: {e}")
    sys.exit(1)
