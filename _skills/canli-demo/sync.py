"""Canlı demo şablonunu projeye kopyala.

Kullanım:
    python _skills/canli-demo/sync.py <proje_klasoru>

- template/core/run_state.py  → <proje>/core/run_state.py (overwrite)
- template/dashboard_server.py → <proje>/dashboard_server.py (overwrite)
- template/dashboard/*         → <proje>/dashboard/ (overwrite — payloads.js HARİÇ)
- template/stages_example.py   → <proje>/stages.py (SADECE yoksa kopyala; varsa elleme)

requirements.txt içine canli demo bağımlılıklarını ekler (yoksa).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = Path(__file__).resolve().parent / "template"

DEPS = ["fastapi>=0.110", "uvicorn>=0.27", "qrcode>=7.4"]


def ensure_dep(line: str, requirements: list[str]) -> bool:
    base = line.split(">=")[0].split("==")[0].split("<")[0].lower()
    for r in requirements:
        head = r.strip().split("#")[0].split(">=")[0].split("==")[0].split("<")[0].lower()
        if head == base:
            return False
    return True


def sync_requirements(project_path: Path) -> None:
    req = project_path / "requirements.txt"
    if not req.exists():
        return
    lines = req.read_text().splitlines()
    additions = [d for d in DEPS if ensure_dep(d, lines)]
    if not additions:
        return
    if lines and lines[-1].strip():
        lines.append("")
    lines.append("# canli-demo (sync.py tarafından eklendi)")
    lines.extend(additions)
    req.write_text("\n".join(lines) + "\n")
    print(f"   ✓ requirements.txt güncellendi (+{len(additions)} satır)")


def copy_tree(src: Path, dst: Path, overwrite_existing: bool = True, skip_names: set[str] | None = None) -> None:
    skip_names = skip_names or set()
    dst.mkdir(parents=True, exist_ok=True)
    for entry in src.iterdir():
        if entry.name in skip_names:
            continue
        target = dst / entry.name
        if entry.is_dir():
            copy_tree(entry, target, overwrite_existing=overwrite_existing, skip_names=skip_names)
            continue
        if target.exists() and not overwrite_existing:
            continue
        shutil.copy2(entry, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Canlı demo şablonunu projeye kopyala")
    parser.add_argument("project", help="Proje klasör yolu")
    args = parser.parse_args()

    project_path = (ROOT / args.project).resolve()
    if not project_path.exists() or not project_path.is_dir():
        print(f"❌ Proje klasörü bulunamadı: {project_path}", file=sys.stderr)
        return 1

    print(f"📦 {project_path.relative_to(ROOT)} klasörüne canlı demo şablonu kopyalanıyor…")

    (project_path / "core").mkdir(parents=True, exist_ok=True)
    init_file = project_path / "core" / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

    src_runstate = TEMPLATE / "core" / "run_state.py"
    dst_runstate = project_path / "core" / "run_state.py"
    shutil.copy2(src_runstate, dst_runstate)
    print(f"   ✓ core/run_state.py")

    src_server = TEMPLATE / "dashboard_server.py"
    dst_server = project_path / "dashboard_server.py"
    shutil.copy2(src_server, dst_server)
    print(f"   ✓ dashboard_server.py")

    src_dashboard = TEMPLATE / "dashboard"
    dst_dashboard = project_path / "dashboard"
    has_payloads = (dst_dashboard / "payloads.js").exists()
    copy_tree(src_dashboard, dst_dashboard, overwrite_existing=True, skip_names={"payloads.example.js"})
    print(f"   ✓ dashboard/* (payloads.js {'korundu' if has_payloads else 'yok'})")

    src_stages = TEMPLATE / "stages_example.py"
    dst_stages = project_path / "stages.py"
    if dst_stages.exists():
        print(f"   ↷ stages.py mevcut, korundu")
    else:
        shutil.copy2(src_stages, dst_stages)
        print(f"   ✓ stages.py (şablon)")

    sync_requirements(project_path)
    print(f"\n✅ Şablon kopyalandı.\n")
    print("Sonraki adımlar:")
    print(f"  1. {project_path.relative_to(ROOT)}/stages.py — projeye özgün stage'leri tanımla")
    print(f"  2. main.py'a emitter.start_stage() / end_stage() çağrılarını yerleştir")
    print(f"  3. Test: python _skills/canli-demo/mock.py {project_path.relative_to(ROOT)}")
    print(f"  4. Canlı: python _skills/canli-demo/start.py {project_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
