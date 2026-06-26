"""Manuel URL ile uçtan uca pipeline run.

Kullanım:
    python -m scripts.run_single <reels_url> [--source-channel @nateherkai]

Çıktı:
    Notion kart URL'si + özet.
"""

from __future__ import annotations

import argparse
import sys
import time
import traceback
from pathlib import Path

from core.config import Config
from core.pipeline import run_pipeline


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("url", help="Instagram reels URL")
    p.add_argument("--source-channel", default="manuel",
                   help="@nateherkai gibi (Notion select değeri olmalı)")
    p.add_argument("--local-file", default=None,
                   help="Lokal mp4 path (downloader=local için)")
    p.add_argument("--downloader", choices=["apify", "ytdlp", "local"], default="apify")
    args = p.parse_args()
    if args.local_file:
        args.downloader = "local"

    cfg = Config.from_env()
    start = time.time()
    print(f"\n═══ Reels Script Yazarı — Single Run ═══\n")
    try:
        result = run_pipeline(
            cfg, args.url,
            source_channel=args.source_channel,
            local_file=Path(args.local_file) if args.local_file else None,
            downloader=args.downloader,
        )
    except Exception as e:
        print(f"\n❌ Pipeline başarısız: {e}")
        traceback.print_exc()
        return 1

    elapsed = time.time() - start
    print(f"\n═══ ✅ Tamamlandı ({elapsed:.1f}s) ═══")
    print(f"  Run ID:        {result.run_id}")
    print(f"  Notion kart:   https://www.notion.so/{result.notion_page_id.replace('-','')}")
    print(f"  Başlık:        {result.topic_title}")
    print(f"  Transcript:    {result.transcript_chars} char")
    print(f"  Script:        {result.script_chars} char")
    print(f"  Asset sayısı:  {result.asset_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
