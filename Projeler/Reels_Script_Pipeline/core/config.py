"""Merkezi config — master.env veya .env'den env var yükler.

Sprint 1+ pipeline modülleri bu dosyadan import eder.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MASTER_ENV = PROJECT_ROOT.parent.parent / "_knowledge" / "credentials" / "master.env"
LOCAL_ENV = PROJECT_ROOT / ".env"

if MASTER_ENV.exists():
    load_dotenv(MASTER_ENV)
if LOCAL_ENV.exists():
    load_dotenv(LOCAL_ENV, override=False)


def _required(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Env var eksik: {key} (master.env veya .env'de yok)")
    return val


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str
    happyscribe_api_key: str
    happyscribe_org_id: int
    happyscribe_glossary_id: str | None
    notion_token: str
    notion_reels_prod_db_id: str
    notion_reels_prod_data_source_id: str
    notion_test_parent_page_id: str
    notion_emoji_claudecode_id: str
    google_drive_reels_parent_folder_id: str
    supabase_url: str
    supabase_anon_key: str
    supabase_project_ref: str
    rapidapi_key: str | None
    rapidapi_instagram_host: str | None
    youtube_api_key: str | None
    voyage_api_key: str
    embedding_model: str
    apify_api_key: str
    notion_style_corpus_db_id: str
    notion_style_corpus_data_source_id: str
    env: str

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            anthropic_api_key=_required("ANTHROPIC_API_KEY"),
            happyscribe_api_key=_required("HAPPYSCRIBE_API_KEY"),
            happyscribe_org_id=int(os.getenv("HAPPYSCRIBE_ORG_ID", "7246599")),
            happyscribe_glossary_id=os.getenv("HAPPYSCRIBE_ORG_GLOSSARY_ID") or None,
            notion_token=os.getenv("NOTION_REELS_TOKEN") or _required("NOTION_API_TOKEN"),
            notion_reels_prod_db_id=os.getenv("NOTION_REELS_PROD_DB_ID") or _required("NOTION_STYLE_CORPUS_DB_ID"),
            notion_reels_prod_data_source_id=os.getenv("NOTION_REELS_PROD_DATA_SOURCE_ID") or _required("NOTION_STYLE_CORPUS_DATA_SOURCE_ID"),
            notion_test_parent_page_id=_required("NOTION_TEST_PARENT_PAGE_ID"),
            notion_emoji_claudecode_id=_required("NOTION_CUSTOM_EMOJI_CLAUDECODE_ID"),
            google_drive_reels_parent_folder_id=_required("GOOGLE_DRIVE_REELS_PARENT_FOLDER_ID"),
            supabase_url=_required("REELS_SUPABASE_URL"),
            supabase_anon_key=_required("REELS_SUPABASE_ANON_KEY"),
            supabase_project_ref=_required("REELS_SUPABASE_PROJECT_REF"),
            rapidapi_key=os.getenv("RAPIDAPI_KEY") or None,
            rapidapi_instagram_host=os.getenv("RAPIDAPI_INSTAGRAM_HOST") or None,
            youtube_api_key=os.getenv("YOUTUBE_API_KEY") or None,
            voyage_api_key=_required("VOYAGE_API_KEY"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "voyage-3"),
            apify_api_key=os.getenv("APIFY_API_KEY") or _required("APIFY_API_KEY_1"),
            notion_style_corpus_db_id=_required("NOTION_STYLE_CORPUS_DB_ID"),
            notion_style_corpus_data_source_id=_required("NOTION_STYLE_CORPUS_DATA_SOURCE_ID"),
            env=os.getenv("ENV", "local"),
        )
