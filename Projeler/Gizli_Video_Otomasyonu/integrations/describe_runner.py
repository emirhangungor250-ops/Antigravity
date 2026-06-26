"""Açıklama motorunu (bu paketteki Youtube_Aciklama_Otomasyonu) KENDİ bağlamında
çalıştıran köprü.

Ayrı süreç olarak çağrılır ki iki projenin 'core' paketi çakışmasın. Girdiyi argv[1]
json'undan okur, açıklamayı üretir (ucuz/bedava OpenAI katmanı), istenirse Drive'a
Google Doc olarak yazar. Sonucu '__RESULT__<json>' satırı olarak basar.
"""
import json
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    p = Path(__file__).resolve()
    for a in [p] + list(p.parents):
        if (a / "Projeler").is_dir() and (a / "_knowledge").is_dir():
            return a
    return p.parents[3]


ROOT = _repo_root()

# master.env yükle (OPENAI_API_KEY = ucuz/bedava katman + Drive token)
_me = ROOT / "_knowledge" / "credentials" / "master.env"
if _me.exists():
    for line in _me.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            if k and k not in os.environ:
                os.environ[k] = v.strip().strip('"').strip("'")

# Açıklama motorunun klasör adı (config ile aynı env override'ı kullan)
_ENGINE_DIR_NAME = os.getenv("ACIKLAMA_ENGINE_DIR_NAME", "Youtube_Aciklama_Otomasyonu")
YT = ROOT / "Projeler" / _ENGINE_DIR_NAME
os.chdir(YT)
sys.path.insert(0, str(YT))

from core import description_builder, google_docs_service  # noqa: E402


def main():
    inp = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

    # Politika güvencesi: ucuz/bedava OpenAI katmanı yoksa pahalı modele düşmesin
    if not os.getenv("OPENAI_API_KEY"):
        print("__RESULT__" + json.dumps(
            {"ok": False, "error": "OPENAI_API_KEY yok — ucuz katman olmadan üretim durduruldu."},
            ensure_ascii=False))
        return

    ai = description_builder.build_description(
        video_name=inp["video_name"],
        video_url=inp.get("video_url", ""),
        brief=inp.get("brief", ""),
        transcript_with_timestamps=inp.get("transcript", ""),
        duration_sec=int(inp.get("duration_sec") or 0),
    )
    final_text = description_builder.assemble_final_description(
        ai_output=ai, video_name=inp["video_name"], brief=inp.get("brief", ""))

    result = {"ok": True, "description_text": final_text, "doc_link": None,
              "video_type": ai.get("marka_anahtari") or ("egitim" if ai.get("egitim_mi") else "organik")}

    if not inp.get("dry_run", True) and inp.get("drive_folder_url"):
        html = google_docs_service.build_html(title=inp["video_name"], description_text=final_text)
        folder_id = google_docs_service.extract_folder_id(inp["drive_folder_url"])
        doc_name = inp.get("doc_name") or f"Aciklama_Taslagi_{inp['video_name'][:40]}"
        f = google_docs_service.create_doc_in_folder(folder_id, doc_name, html)
        result["doc_link"] = f.get("webViewLink")

    print("__RESULT__" + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("__RESULT__" + json.dumps({"ok": False, "error": repr(e)[:600]}, ensure_ascii=False))
