"""Manuel kapak üretimi — tek video için lokal pipeline (Notion/Drive yok).

API anahtarlarını .env dosyanızdan veya ortam değişkenlerinden okur.
Çalıştırmadan önce KIE_API_KEY, GEMINI_API_KEY, IMGBB_API_KEY tanımlı olmalı.
"""
import os, sys, random
from pathlib import Path

PROJ = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJ))

# API anahtarlarını .env dosyasından yükle (varsa)
_env_file = PROJ / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)

os.environ.setdefault("ENV", "production")  # dry-run KAPALI

from agents.reels_agent import generate_three_themes, run_autonomous_generation

# TODO: Kendi videonuzun bilgilerini girin.
VIDEO_NAME = "Ornek Video"
VIDEO_TOPIC = "Videonun kisa konu ozeti (Gemini'ye baglam saglar)"
SCRIPT = """Buraya videonuzun senaryo metnini yazin. Kapak temalari bu metinden
uretilir; somut detaylar (sayilar, fiyatlar, sureler) iyi sonuc verir."""

OUT_DIR = PROJ / "outputs" / "manuel_claude_code"
OUT_DIR.mkdir(parents=True, exist_ok=True)

cutout_dir = PROJ / "assets" / "cutouts"
cutouts = [str(cutout_dir / f) for f in os.listdir(cutout_dir) if f.endswith(".png")]

print(f"\n=== 3 tema üretiliyor: {VIDEO_NAME} ===\n")
themes = generate_three_themes(VIDEO_NAME, SCRIPT)

results = []
for i, theme in enumerate(themes, 1):
    name = theme.get("theme_name", f"theme{i}")
    txt = theme["cover_text"]
    scene = theme["scene_description"]
    print(f"\n--- Tema {i}: {name} → '{txt}' ---")
    cutout = random.choice(cutouts)
    out_path = OUT_DIR / f"claude_code_T{i}_{name.replace(' ', '_')}.png"
    try:
        run_autonomous_generation(
            local_person_image_path=cutout,
            video_topic=VIDEO_TOPIC,
            main_text=txt,
            output_path=str(out_path),
            max_retries=2,
            variant_index=1,
            script_text=SCRIPT,
            scene_description=scene,
        )
        if out_path.exists():
            results.append(str(out_path))
            print(f"  ✓ {out_path.name}")
        else:
            print(f"  ✗ Üretilemedi")
    except Exception as e:
        print(f"  ✗ Hata: {e}")

print(f"\n=== Tamamlandı: {len(results)}/{len(themes)} kapak ===")
for r in results:
    print(r)
