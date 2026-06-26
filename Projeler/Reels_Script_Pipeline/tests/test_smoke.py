"""Sprint 0 smoke test — tüm dış servislere bir ping atar.

Kullanım:
    python -m tests.test_smoke

Çıktı: her servis için ✅/❌ ve kısa açıklama.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable

import httpx

from core.config import Config


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def check_anthropic(cfg: Config) -> CheckResult:
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": cfg.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "ping"}],
        },
        timeout=15,
    )
    if r.status_code == 200:
        return CheckResult("Anthropic", True, "messages API yanıtladı")
    return CheckResult("Anthropic", False, f"HTTP {r.status_code}: {r.text[:120]}")


def check_happyscribe(cfg: Config) -> CheckResult:
    r = httpx.get(
        "https://www.happyscribe.com/api/v1/organizations",
        headers={"Authorization": f"Bearer {cfg.happyscribe_api_key}"},
        timeout=10,
    )
    if r.status_code != 200:
        return CheckResult("HappyScribe", False, f"HTTP {r.status_code}")
    orgs = r.json().get("organizations", [])
    if not any(o["id"] == cfg.happyscribe_org_id for o in orgs):
        return CheckResult("HappyScribe", False, f"org_id {cfg.happyscribe_org_id} listede yok")
    # Glossary listesi de okunabiliyor mu kontrol et
    rg = httpx.get(
        f"https://www.happyscribe.com/api/v1/glossaries?organization_id={cfg.happyscribe_org_id}",
        headers={"Authorization": f"Bearer {cfg.happyscribe_api_key}"},
        timeout=10,
    )
    if rg.status_code != 200:
        return CheckResult("HappyScribe", False, f"glossaries HTTP {rg.status_code}")
    glossaries = rg.json().get("glossaries", [])
    has_target = cfg.happyscribe_glossary_id and any(
        str(g["id"]) == str(cfg.happyscribe_glossary_id) for g in glossaries
    )
    note = (
        f"org OK, glossary OK (id={cfg.happyscribe_glossary_id})"
        if has_target
        else f"org OK, glossary henüz set edilmemiş ({len(glossaries)} glossary mevcut)"
    )
    return CheckResult("HappyScribe", True, note)


def check_notion(cfg: Config) -> CheckResult:
    """Sprint 2: prod DB 'İçerik DB' erişimini probe et."""
    r = httpx.get(
        f"https://api.notion.com/v1/databases/{cfg.notion_reels_prod_db_id}",
        headers={
            "Authorization": f"Bearer {cfg.notion_token}",
            "Notion-Version": "2022-06-28",
        },
        timeout=10,
    )
    if r.status_code == 200:
        body = r.json()
        title = "".join(t["plain_text"] for t in body.get("title", []))
        if title != "İçerik DB":
            return CheckResult(
                "Notion",
                False,
                f"Beklenmeyen DB başlığı: '{title}' (beklenen 'İçerik DB')",
            )
        return CheckResult("Notion", True, f"prod DB '{title}' erişilebilir")
    if r.status_code == 404:
        return CheckResult(
            "Notion",
            False,
            "Prod DB bulunamadı — NOTION_REELS_TOKEN bu workspace'e bağlı olmayabilir.",
        )
    return CheckResult("Notion", False, f"HTTP {r.status_code}: {r.text[:120]}")


def check_drive(cfg: Config) -> CheckResult:
    """OAuth refresh token validity. Parent folder yazılabilirliği create-test
    ile doğrulanır; drive.file scope arbitrary folder.get'i 404 döndüğünden
    burada about.user ve geçici create+delete denenir."""
    try:
        from core.drive import _drive
        drive = _drive()
        about = drive.about().get(fields="user").execute()
        email = about.get("user", {}).get("emailAddress", "?")
        # Geçici klasör yaratıp hemen sil — yazma iznini test eder
        f = drive.files().create(
            body={
                "name": "_smoke_test_delete_me",
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [cfg.google_drive_reels_parent_folder_id],
            },
            fields="id",
            supportsAllDrives=True,
        ).execute()
        drive.files().delete(fileId=f["id"]).execute()
        return CheckResult("Drive", True, f"OAuth {email}, parent yazılabilir")
    except Exception as e:
        return CheckResult("Drive", False, f"erişim hatası: {str(e)[:100]}")


def check_apify(cfg: Config) -> CheckResult:
    """Apify auth probe."""
    if not cfg.apify_api_key:
        return CheckResult("Apify", False, "APIFY_API_KEY yok")
    r = httpx.get(
        "https://api.apify.com/v2/users/me",
        params={"token": cfg.apify_api_key},
        timeout=10,
    )
    if r.status_code == 200:
        plan = r.json().get("data", {}).get("plan", {}) or {}
        plan_id = plan.get("id", "?") if isinstance(plan, dict) else plan
        return CheckResult("Apify", True, f"auth OK (plan={plan_id})")
    return CheckResult("Apify", False, f"HTTP {r.status_code}")


def check_supabase(cfg: Config) -> CheckResult:
    r = httpx.get(
        f"{cfg.supabase_url}/rest/v1/pipeline_runs?select=count",
        headers={
            "apikey": cfg.supabase_anon_key,
            "Authorization": f"Bearer {cfg.supabase_anon_key}",
            "Prefer": "count=exact",
        },
        timeout=10,
    )
    if r.status_code in (200, 206):
        count = r.headers.get("content-range", "0/0").split("/")[-1]
        return CheckResult("Supabase", True, f"pipeline_runs erişilebilir (count={count})")
    return CheckResult("Supabase", False, f"HTTP {r.status_code}: {r.text[:120]}")


def check_youtube(cfg: Config) -> CheckResult:
    if not cfg.youtube_api_key:
        return CheckResult("YouTube", False, "YOUTUBE_API_KEY yok (opsiyonel, Sprint 2)")
    r = httpx.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={"id": "jNQXAC9IVRw", "part": "snippet", "key": cfg.youtube_api_key},
        timeout=10,
    )
    if r.status_code == 200:
        return CheckResult("YouTube", True, "Data API ping OK")
    return CheckResult("YouTube", False, f"HTTP {r.status_code}: {r.text[:120]}")


def check_voyage(cfg: Config) -> CheckResult:
    r = httpx.post(
        "https://api.voyageai.com/v1/embeddings",
        headers={
            "Authorization": f"Bearer {cfg.voyage_api_key}",
            "content-type": "application/json",
        },
        json={"input": ["ping"], "model": cfg.embedding_model},
        timeout=15,
    )
    if r.status_code == 200:
        dim = len(r.json()["data"][0]["embedding"])
        return CheckResult("Voyage", True, f"{cfg.embedding_model} embedding dim={dim}")
    return CheckResult("Voyage", False, f"HTTP {r.status_code}: {r.text[:120]}")


CHECKS: list[Callable[[Config], CheckResult]] = [
    check_anthropic,
    check_happyscribe,
    check_notion,
    check_supabase,
    check_voyage,
    check_youtube,
    check_drive,
    check_apify,
]


def main() -> int:
    cfg = Config.from_env()
    results = [c(cfg) for c in CHECKS]
    print("\n═══ Reels Script Yazarı — Smoke Test ═══\n")
    for r in results:
        mark = "✅" if r.ok else "❌"
        print(f"  {mark}  {r.name:<12}  {r.detail}")
    print()
    failed = sum(1 for r in results if not r.ok)
    required = {"Anthropic", "HappyScribe", "Notion", "Supabase", "Voyage", "Drive", "Apify"}
    critical_failed = [r for r in results if not r.ok and r.name in required]
    if critical_failed:
        print(f"❌ {len(critical_failed)} kritik servis başarısız — Sprint 0 tamamlanamaz")
        return 1
    if failed:
        print(f"⚠️  {failed} opsiyonel servis hazır değil (Sprint 0 için engelleyici değil)")
    else:
        print("✅ Tüm servisler hazır — Sprint 0 bitti, Sprint 1'e geçilebilir")
    return 0


if __name__ == "__main__":
    sys.exit(main())
