"""Canlı demo mock runner — gerçek API çağırmadan dashboard'ı test et.

Kullanım:
    python _skills/canli-demo/mock.py <proje_klasoru>

Projenin stages.py'sini okur, her stage için 2-4s sahte progress üretir,
dashboard'ı http://localhost:8000 üzerinden açılır halde tutar.
Ctrl+C ile durur.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


async def run_mock(project_path: Path, port: int) -> int:
    sys.path.insert(0, str(project_path))

    try:
        from dashboard_server import start_dashboard  # type: ignore
        from core.run_state import emitter  # type: ignore
        from stages import STAGES, META  # type: ignore
    except Exception as e:
        print(f"❌ İmport hatası: {e}", file=sys.stderr)
        print(
            f"   Önce şablonu kopyala: python _skills/canli-demo/sync.py {project_path.relative_to(ROOT)}",
            file=sys.stderr,
        )
        return 2

    os.environ["DASHBOARD_PORT"] = str(port)

    server_task = asyncio.create_task(start_dashboard())
    await asyncio.sleep(1.0)

    print(f"\n🎬 Mock demo: http://localhost:{port}")
    print("    (Ctrl+C ile dur)\n")

    # Determinist akış — random delay yerine sabit ritm.
    # Toplam koşu: ~stage_count × 6sn + sub_stages × 5sn ≈ 35-50sn.
    STAGE_DURATION_SEC = 6.0
    STEPS_PER_STAGE = 5
    SUB_STEPS = 5
    SUB_STEP_DELAY = 0.6

    try:
        while True:
            emitter.start_run(input_label="Mock koşusu — gerçek pipeline tetiklenmiyor")
            for stage in STAGES:
                emitter.start_stage(stage["id"], sub_text="Hazırlanıyor…")
                if stage.get("sub_stages"):
                    for sub in stage["sub_stages"]:
                        emitter.start_substage(stage["id"], sub["id"], sub_text="Başlıyor")
                        for step in range(1, SUB_STEPS + 1):
                            await asyncio.sleep(SUB_STEP_DELAY)
                            emitter.update_substage(
                                stage["id"], sub["id"],
                                sub_text=f"{sub['label']} · {step}/{SUB_STEPS}",
                                progress=step / SUB_STEPS,
                            )
                        emitter.end_substage(
                            stage["id"], sub["id"],
                            payload={"durum": "tamamlandı", "süre_sn": round(SUB_STEPS * SUB_STEP_DELAY, 1)},
                        )
                else:
                    step_delay = STAGE_DURATION_SEC / STEPS_PER_STAGE
                    for step in range(1, STEPS_PER_STAGE + 1):
                        await asyncio.sleep(step_delay)
                        emitter.update_stage(
                            stage["id"],
                            sub_text=f"{stage['label']} · {step}/{STEPS_PER_STAGE}",
                            progress=step / STEPS_PER_STAGE,
                        )
                emitter.end_stage(stage["id"], payload={
                    "durum": "tamamlandı",
                    "stage_id": stage["id"],
                    "süre_sn": STAGE_DURATION_SEC,
                })
            emitter.end_run(final_payload={"durum": "demo tamamlandı"})
            await asyncio.sleep(5.0)
            emitter.reset_idle()
            await asyncio.sleep(2.0)
    except asyncio.CancelledError:
        pass
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="Proje klasör yolu")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    project_path = (ROOT / args.project).resolve()
    if not project_path.is_dir():
        print(f"❌ Proje bulunamadı: {project_path}", file=sys.stderr)
        return 1

    try:
        return asyncio.run(run_mock(project_path, args.port))
    except KeyboardInterrupt:
        print("\n👋 Mock durduruldu.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
