"""Bekleyen iş sinyalleri.

Lokalde duran ipuçlarını tarar:
1. Kökte HANDOVER_*.md / TODO_*.md → ilgili projeyi 'beklemede' işaretler
2. Railway FAILED/CRASHED → 'kırık' (railway_data parametre olarak gelir)
3. .env.example var ama Railway servisi yok → 'deploy edilmemiş'
4. README'de TODO/BEKLİYOR/PENDING → 'yarım'
5. Sistem_Nasil_Calisir.html eksik → 'doküman eksik' (düşük öncelik)

Öncelik sırası: FAILED > HANDOVER > deploy yok > yarım > doküman eksik.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ANTIGRAVITY_ROOT = Path(__file__).resolve().parents[3]
PROJELER_DIR = ANTIGRAVITY_ROOT / "Projeler"

TODO_PATTERNS = re.compile(
    r"(?m)^\s*[-*#>]*\s*(TODO|PENDING|YARIM|BEKL[İI]YOR)\b",
    re.IGNORECASE,
)

PRIORITY = {
    "failed": 1,
    "handover": 2,
    "deploy_yok": 3,
    "yarim": 4,
    "doc_eksik": 5,
}

REASON_LABELS = {
    "failed": "Railway hata veriyor",
    "handover": "Bekleyen el devri notu",
    "deploy_yok": "Deploy edilmedi",
    "yarim": "README'de yarım iş notu",
    "doc_eksik": "Sistem dokümanı eksik",
}


def _scan_handover_files() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in sorted(ANTIGRAVITY_ROOT.glob("HANDOVER*.md")) + sorted(
        ANTIGRAVITY_ROOT.glob("TODO*.md")
    ):
        try:
            first_line = path.read_text(errors="ignore").splitlines()[0].strip("# ").strip()
        except Exception:
            first_line = ""
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        m = re.search(r"HANDOVER_(.+?)(?:_v\d+)?\.md$", path.name)
        proj_hint = m.group(1) if m else path.stem
        out.append(
            {
                "kind": "handover",
                "file": path.name,
                "first_line": first_line[:140],
                "mtime": mtime.isoformat(),
                "project_hint": proj_hint,
            }
        )
    return out


def _list_local_projects() -> list[Path]:
    if not PROJELER_DIR.exists():
        return []
    out: list[Path] = []
    for p in sorted(PROJELER_DIR.iterdir()):
        if not p.is_dir():
            continue
        if p.name.startswith("_") or p.name == "_arsiv":
            continue
        out.append(p)
    return out


def _check_failed_deployments(railway_services: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for svc in railway_services or []:
        dep = svc.get("latest_deployment") or {}
        status = (dep.get("status") or "").upper()
        if status in {"FAILED", "CRASHED"}:
            out.append(
                {
                    "kind": "failed",
                    "project": svc.get("project_name"),
                    "service": svc.get("service_name"),
                    "status": status,
                    "deployment_id": dep.get("id"),
                    "deployment_time": dep.get("createdAt"),
                }
            )
    return out


def _check_missing_deploys(
    project_folders: list[Path],
    railway_services: list[dict[str, Any]],
    deployed_folders: set[str],
) -> list[dict[str, Any]]:
    """Yerel proje var, .env.example var, ama Railway'de bağlı servis yok.

    `deployed_folders` projects.yaml'dan gelen kesin folder→railway eşleşmesi.
    Burada bu listede olmayanlar 'deploy edilmemiş' sayılır.
    """
    out: list[dict[str, Any]] = []
    for folder in project_folders:
        if not (folder / ".env.example").exists():
            continue
        if folder.name in deployed_folders:
            continue
        # Dashboard projesinin kendisi sinyal vermesin (deploy planlı değil)
        if folder.name == "Proje_Dashboard":
            continue
        out.append(
            {
                "kind": "deploy_yok",
                "project": folder.name,
                "folder": str(folder.relative_to(ANTIGRAVITY_ROOT)),
            }
        )
    return out


def _check_readme_todos(project_folders: list[Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for folder in project_folders:
        readme = folder / "README.md"
        if not readme.exists():
            continue
        try:
            content = readme.read_text(errors="ignore")
        except Exception:
            continue
        matches = TODO_PATTERNS.findall(content)
        if not matches:
            continue
        # İlk eşleşen satırı çıkar
        sample = ""
        for line in content.splitlines():
            if TODO_PATTERNS.search(line):
                sample = line.strip("#- ").strip()[:140]
                break
        out.append(
            {
                "kind": "yarim",
                "project": folder.name,
                "match_count": len(matches),
                "sample": sample,
            }
        )
    return out


def _check_missing_docs(project_folders: list[Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for folder in project_folders:
        if not (folder / "Sistem_Nasil_Calisir.html").exists():
            out.append(
                {
                    "kind": "doc_eksik",
                    "project": folder.name,
                }
            )
    return out


def _load_deployed_folders() -> set[str]:
    """projects.yaml'dan railway servisine bağlı folder isimlerini al."""
    import yaml as _yaml

    cfg_path = Path(__file__).resolve().parents[1] / "config" / "projects.yaml"
    if not cfg_path.exists():
        return set()
    cfg = _yaml.safe_load(cfg_path.read_text()) or {}
    out: set[str] = set()
    for p in cfg.get("projects") or []:
        folder = p.get("folder")
        if folder:
            out.add(folder)
    return out


def _load_ignored() -> set[tuple[str, str]]:
    """ignored_signals.yaml'dan (kind, project) listesi."""
    import yaml as _yaml

    cfg_path = Path(__file__).resolve().parents[1] / "config" / "ignored_signals.yaml"
    if not cfg_path.exists():
        return set()
    cfg = _yaml.safe_load(cfg_path.read_text()) or {}
    out: set[tuple[str, str]] = set()
    for item in cfg.get("ignored") or []:
        out.add((item.get("kind"), item.get("project")))
    return out


def _filter_ignored(signals: list[dict], ignored: set[tuple[str, str]]) -> list[dict]:
    filtered = []
    for s in signals:
        kind = s.get("kind")
        # project_hint handover için, project diğerleri için
        proj = s.get("project") or s.get("project_hint") or ""
        if (kind, proj) in ignored:
            continue
        filtered.append(s)
    return filtered


def collect(railway_services: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    project_folders = _list_local_projects()
    deployed_folders = _load_deployed_folders()
    ignored = _load_ignored()
    signals: list[dict[str, Any]] = []
    signals.extend(_scan_handover_files())
    signals.extend(_check_failed_deployments(railway_services or []))
    signals.extend(_check_missing_deploys(project_folders, railway_services or [], deployed_folders))
    signals.extend(_check_readme_todos(project_folders))
    signals.extend(_check_missing_docs(project_folders))

    # Ignored filtresi
    signals = _filter_ignored(signals, ignored)

    # Önceliğe göre sırala
    signals.sort(key=lambda s: (PRIORITY.get(s["kind"], 99), s.get("project", "")))

    return {
        "ok": True,
        "signals": signals,
        "ignored_count": len(ignored),
        "summary_by_kind": {
            kind: len([s for s in signals if s["kind"] == kind])
            for kind in PRIORITY
        },
        "labels": REASON_LABELS,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(collect(), indent=2, default=str))
