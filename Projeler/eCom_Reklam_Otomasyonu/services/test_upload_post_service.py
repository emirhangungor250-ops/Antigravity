"""
Upload-Post Service — Mock Test Suite
======================================
Tüm canlı API çağrıları `unittest.mock` ile mock'lanır. Network YOK.
"""

from __future__ import annotations

import sys
import os
from unittest.mock import MagicMock, patch

import pytest

# Test dosyası `services/` altında; logger ve utils kök dizinde — sys.path ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.upload_post_service import (  # noqa: E402
    UploadPostService,
    UploadPostAuthError,
    _make_idempotency_key,
    _flatten_hashtags,
    _compose_caption,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _make_response(status_code: int = 200, json_data: dict | None = None, text: str = ""):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data if json_data is not None else {}
    mock.text = text or ""
    if status_code >= 400:
        # raise_for_status'u taklit et
        from requests.exceptions import HTTPError
        err = HTTPError(f"HTTP {status_code}")
        err.response = mock
        mock.raise_for_status.side_effect = err
    else:
        mock.raise_for_status.return_value = None
    return mock


FAKE_USERS_RESPONSE = {
    "success": True,
    "profiles": [
        {
            "username": "test_profile",
            "social_accounts": {
                "tiktok": {
                    "display_name": "Meltem.2035",
                    "handle": "meltem.2035",
                    "reauth_required": False,
                },
                "instagram": "",
                "youtube": {
                    "display_name": "Meltem.2035",
                    "handle": "@meltem.2035",
                    "reauth_required": False,
                },
            },
            "blocked": False,
        },
        {
            "username": "baska_profil",
            "social_accounts": {"tiktok": {"handle": "x"}},
        },
    ],
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestListConnectedPlatforms:
    def test_list_platforms_filters_by_profile(self):
        svc = UploadPostService(api_key="fake-key", profile_name="test_profile")
        with patch("services.upload_post_service.requests.get") as mget:
            mget.return_value = _make_response(200, FAKE_USERS_RESPONSE)
            result = svc.list_connected_platforms()

        assert result["tiktok"]["connected"] is True
        assert result["tiktok"]["username"] == "meltem.2035"

        assert result["youtube"]["connected"] is True
        assert result["youtube"]["username"] == "@meltem.2035"

        # Instagram boş string (bağsız) → connected False
        assert result["instagram"]["connected"] is False
        assert result["instagram"]["username"] is None

        # Hiç dönmemiş platformlar (linkedin, twitter, ...) → connected False default
        assert result["linkedin"]["connected"] is False

    def test_list_platforms_unknown_profile_returns_all_disconnected(self):
        svc = UploadPostService(api_key="fake-key", profile_name="olmayan_profil")
        with patch("services.upload_post_service.requests.get") as mget:
            mget.return_value = _make_response(200, FAKE_USERS_RESPONSE)
            result = svc.list_connected_platforms()

        assert all(not v["connected"] for v in result.values())

    def test_list_platforms_uses_apikey_header(self):
        svc = UploadPostService(api_key="my-secret-key", profile_name="test_profile")
        with patch("services.upload_post_service.requests.get") as mget:
            mget.return_value = _make_response(200, FAKE_USERS_RESPONSE)
            svc.list_connected_platforms()

        _, kwargs = mget.call_args
        auth = kwargs["headers"]["Authorization"]
        assert auth.startswith("Apikey "), f"Expected 'Apikey ' prefix, got: {auth}"
        assert auth == "Apikey my-secret-key"
        assert not auth.startswith("Bearer ")

    def test_401_raises_auth_error(self):
        svc = UploadPostService(api_key="bad-key", profile_name="test_profile")
        with patch("services.upload_post_service.requests.get") as mget:
            mget.return_value = _make_response(401, {"error": "invalid api key"})
            with pytest.raises(UploadPostAuthError):
                svc.list_connected_platforms()


class TestUploadVideo:
    def _patch_post(self, return_status=200, return_json=None):
        if return_json is None:
            return_json = {"request_id": "req_abc", "status": "queued", "platforms": ["tiktok"]}
        return patch(
            "services.upload_post_service.requests.post",
            return_value=_make_response(return_status, return_json),
        )

    def test_upload_video_sends_apikey_header(self):
        svc = UploadPostService(api_key="my-secret", profile_name="test_profile")
        with self._patch_post() as mpost:
            svc.upload_video(
                video_url="https://cdn.example.com/v.mp4",
                platforms=["tiktok"],
                captions={"tiktok": {"caption": "hi", "hashtags": ["a"]}},
            )

        _, kwargs = mpost.call_args
        auth = kwargs["headers"]["Authorization"]
        assert auth.startswith("Apikey "), f"Bearer/diger değil 'Apikey ' olmali: {auth}"
        assert auth == "Apikey my-secret"

    def test_upload_video_multipart_platforms(self):
        svc = UploadPostService(api_key="k", profile_name="test_profile")
        with self._patch_post() as mpost:
            svc.upload_video(
                video_url="https://cdn.example.com/v.mp4",
                platforms=["tiktok", "youtube", "instagram"],
                captions={
                    "tiktok": {"caption": "tt", "hashtags": ["a"]},
                    "youtube": {"title": "yt", "description": "yd", "tags": ["b"]},
                    "instagram": {"caption": "ig", "hashtags": ["c"]},
                },
            )

        _, kwargs = mpost.call_args
        data = kwargs["data"]
        # data: list of (key, value) tuples — `platform[]` çoklu olmalı
        platform_values = [v for (k, v) in data if k == "platform[]"]
        assert set(platform_values) == {"tiktok", "youtube", "instagram"}

    def test_upload_video_includes_idempotency_key(self):
        svc = UploadPostService(api_key="k", profile_name="test_profile")
        with self._patch_post() as mpost:
            svc.upload_video(
                video_url="https://cdn.example.com/v.mp4",
                platforms=["tiktok"],
                captions={"tiktok": {"caption": "hi", "hashtags": []}},
            )

        _, kwargs = mpost.call_args
        headers = kwargs["headers"]
        assert "Idempotency-Key" in headers
        assert len(headers["Idempotency-Key"]) == 32

    def test_caption_expansion_youtube(self):
        svc = UploadPostService(api_key="k", profile_name="test_profile")
        with self._patch_post() as mpost:
            svc.upload_video(
                video_url="https://cdn.example.com/v.mp4",
                platforms=["youtube"],
                captions={
                    "youtube": {
                        "title": "Harika YouTube Title",
                        "description": "Detayli aciklama burada.",
                        "tags": ["fashion", "style", "ootd"],
                    }
                },
            )

        _, kwargs = mpost.call_args
        data = dict_from_pairs_first(kwargs["data"])
        assert data["title"] == "Harika YouTube Title"
        assert data["description"] == "Detayli aciklama burada."
        # youtube_tags virgül ayrımlı
        assert data["youtube_tags"] == "fashion,style,ootd"
        assert data["youtube_categoryId"] == "22"
        assert data["youtube_privacyStatus"] == "public"

    def test_caption_override_uses_same_text_all_platforms(self):
        svc = UploadPostService(api_key="k", profile_name="test_profile")
        override = "Tek metin tum platformlara #hepsi"
        with self._patch_post() as mpost:
            svc.upload_video(
                video_url="https://cdn.example.com/v.mp4",
                platforms=["tiktok", "instagram"],
                captions={"_override": override},
            )

        _, kwargs = mpost.call_args
        data_pairs = kwargs["data"]
        data = dict_from_pairs_first(data_pairs)
        assert data["description"] == override
        # title kısaltılmış
        assert data["title"] == override[:90]
        # TikTok ve Instagram özel alanlarda da aynı metin
        assert data.get("tiktok_description") == override
        assert data.get("instagram_caption") == override

    def test_upload_video_rejects_unsupported_platform(self):
        svc = UploadPostService(api_key="k", profile_name="test_profile")
        with pytest.raises(ValueError):
            svc.upload_video(
                video_url="https://cdn.example.com/v.mp4",
                platforms=["myspace"],
                captions={"myspace": {"caption": "x"}},
            )


class TestPollStatus:
    def test_poll_status_returns_completed(self):
        svc = UploadPostService(api_key="k", profile_name="test_profile")
        completed_response = {
            "status": "completed",
            "results": {
                "tiktok": {"url": "https://tiktok.com/v/1", "video_id": "1"},
                "youtube": {"url": "https://youtu.be/abc", "video_id": "abc"},
            },
        }
        with patch("services.upload_post_service.requests.get") as mget:
            mget.return_value = _make_response(200, completed_response)
            result = svc.poll_status(request_id="req_xyz", timeout_s=5, interval_s=1)

        assert result["status"] == "completed"
        assert "tiktok" in result["results"]
        assert result["results"]["tiktok"]["url"] == "https://tiktok.com/v/1"


class TestHelpers:
    def test_idempotency_key_deterministic_within_minute(self):
        # Aynı dakika bucket'ında aynı input → aynı key
        k1 = _make_idempotency_key("https://x/v.mp4", ["tiktok", "youtube"])
        k2 = _make_idempotency_key("https://x/v.mp4", ["youtube", "tiktok"])  # sıra farkı önemsiz
        assert k1 == k2
        assert len(k1) == 32

    def test_flatten_hashtags(self):
        assert _flatten_hashtags(["a", "#b", "c d"]) == "#a #b #cd"
        assert _flatten_hashtags(None) == ""
        assert _flatten_hashtags([]) == ""

    def test_compose_caption(self):
        assert _compose_caption("Merhaba", ["a", "b"]) == "Merhaba\n\n#a #b"
        assert _compose_caption("Merhaba", []) == "Merhaba"
        assert _compose_caption("", ["a"]) == "#a"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def dict_from_pairs_first(pairs: list[tuple[str, str]]) -> dict[str, str]:
    """Tuple listesinden dict üret (aynı key'in ilk değeri korunur)."""
    out: dict[str, str] = {}
    for k, v in pairs:
        if k not in out:
            out[k] = v
    return out
