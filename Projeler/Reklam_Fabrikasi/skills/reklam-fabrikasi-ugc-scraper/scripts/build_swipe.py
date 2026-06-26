#!/usr/bin/env python3
"""Build the plain text UGC swipe file v2.

Input:
    gold25.json       , array of adapted video objects each with _scoring and _relevance
    transcripts.json  , array from scrape-creators: [{id, url, transcript (webvtt), success, ...}]
    niche_slug        , lowercase-hyphenated string for filename
    --output-dir DIR  , absolute path to the per-project root (e.g. /Users/foo/brands/coca-cola/Reklam Fabrikası)

Output: single .txt file at
    <output-dir>/05_UGC/scraper/<niche-slug>/ugc-winners-v2-<YYYY-MM-DD>.txt
falls back to
    <output-dir>/05_UGC/scraper/ugc-winners-v2-<YYYY-MM-DD>-<niche-slug>.txt
if the niche subdirectory cannot be created.

Usage:
    python build_swipe.py gold25.json transcripts.json <niche-slug> [niche-title] --output-dir <project-root>
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}")
CUE_ID_RE = re.compile(r"^\d+$")
TAG_RE = re.compile(r"<[^>]+>")


def parse_webvtt(content):
    if not content:
        return ""
    speech = []
    for line in content.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.upper().startswith("WEBVTT") or s.upper().startswith("NOTE") or s.startswith("STYLE"):
            continue
        if TIMESTAMP_RE.match(s) or CUE_ID_RE.match(s):
            continue
        s = TAG_RE.sub("", s).strip()
        if s:
            speech.append(s)
    text = " ".join(speech)
    return re.sub(r"\s+", " ", text).strip()


def extract_hook(text, max_words=12):
    if not text:
        return ""
    w = text.split()
    h = " ".join(w[:max_words])
    if len(w) > max_words:
        h += "..."
    return h


def fmt_num(n):
    n = int(n or 0)
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n/1000:.1f}K"
    return f"{n/1_000_000:.1f}M"


def fmt_ratio(r):
    r = float(r or 0)
    return f"{r:.1f}" if r < 100 else str(int(r))


def fmt_age(unix_ts):
    if not unix_ts:
        return "unknown"
    d = int((time.time() - unix_ts) / 86400)
    if d == 0:
        return "today"
    if d == 1:
        return "1 day ago"
    return f"{d} days ago"


def fmt_date(unix_ts):
    if not unix_ts:
        return "unknown"
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc).strftime("%B %-d, %Y")


def fmt_song(song):
    title = (song or {}).get("title") or ""
    artist = (song or {}).get("artist") or ""
    if not title:
        return "no audio info"
    if "original sound" in title.lower() and artist:
        return f"original sound by @{artist}"
    return (f"{title} by {artist}" if artist else title)[:60]


def fmt_hashtags(tags):
    tags = [t for t in (tags or []) if t][:5]
    return ", ".join(f"#{t}" for t in tags) if tags else "none"


def parse_args():
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Build the UGC swipe v2 plain-text deliverable.",
    )
    parser.add_argument("gold_path", nargs="?", help="Path to gold25.json")
    parser.add_argument("transcripts_path", nargs="?", help="Path to transcripts.json")
    parser.add_argument("niche_slug", nargs="?", help="lowercase-hyphenated niche slug")
    parser.add_argument("niche_title", nargs="?", default=None, help="Optional human-readable niche title")
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=None,
        help="Absolute path to the per-project root (the resolved $RFLAB).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.output_dir:
        print(
            "Missing --output-dir. This script must be invoked by the reklam-fabrikasi-ugc-scraper skill, "
            "which resolves the project path via FIRST-RUN PROTECTION.",
            file=sys.stderr,
        )
        sys.exit(2)

    if not args.gold_path or not args.transcripts_path or not args.niche_slug:
        print(
            "Usage: python build_swipe.py gold25.json transcripts.json <niche-slug> [niche-title] "
            "--output-dir <project-root>",
            file=sys.stderr,
        )
        sys.exit(1)

    gold_path = Path(args.gold_path)
    trans_path = Path(args.transcripts_path)
    niche_slug = args.niche_slug
    niche_title = args.niche_title if args.niche_title else niche_slug.replace("-", " ").title()
    output_dir = Path(args.output_dir).expanduser().resolve()

    with gold_path.open("r", encoding="utf-8") as fh:
        gold = json.load(fh)
    with trans_path.open("r", encoding="utf-8") as fh:
        trans_list = json.load(fh)

    tmap = {}
    for t in trans_list:
        vid_id = t.get("id")
        url = t.get("url") or ""
        key = vid_id or url.rstrip("/").split("/")[-1]
        raw = t.get("transcript")
        if raw:
            text = parse_webvtt(raw)
            tmap[key] = {"text": text, "hook": extract_hook(text), "source": "whisper_fallback"}
        else:
            tmap[key] = {"text": "", "hook": "", "source": "unavailable"}

    gold_sorted = sorted(gold, key=lambda v: (-v.get("_relevance", 0), -v["_scoring"]["final_score"]))
    whisper_n = sum(1 for v in gold_sorted if tmap.get(v["id"], {}).get("source") == "whisper_fallback")
    unavail_n = sum(1 for v in gold_sorted if tmap.get(v["id"], {}).get("source") == "unavailable")
    avg_rel = sum(v.get("_relevance", 0) for v in gold_sorted) / max(1, len(gold_sorted))
    avg_score = sum(v["_scoring"]["final_score"] for v in gold_sorted) / max(1, len(gold_sorted))
    breakouts = sum(1 for v in gold_sorted if v["_scoring"].get("underdog_flag"))

    sep_eq = "=" * 80
    out = []
    out.append(sep_eq)
    out.append(f"UGC SCRAPER 2.0, VIRAL TIKTOK WINNERS, {niche_title.upper()}")
    out.append(sep_eq)
    out.append("")
    out.append(f"Niche:             {niche_title}")
    out.append(f"Date:              {datetime.now().strftime('%Y-%m-%d')}")
    out.append(f"Source:            tiktok_organic")
    out.append(f"Pipeline:          scraptik (scrape) + LLM relevance vet + scrape-creators (transcripts)")
    out.append("")
    out.append(f"Final winners:     {len(gold_sorted)}")
    out.append(f"Transcripts:       {whisper_n} usable / {unavail_n} unavailable")
    out.append(f"Pure breakouts:    {breakouts}")
    out.append(f"Avg relevance:     {avg_rel:.1f}/10")
    out.append(f"Avg scoring:       {avg_score:.2f}")
    out.append("")

    for i, v in enumerate(gold_sorted, 1):
        s = v["_scoring"]
        ch = v.get("channel") or {}
        t = tmap.get(v["id"], {"text": "", "hook": "", "source": "unavailable"})
        header = f"  WINNER #{i}    |    REL: {v.get('_relevance', 0)}/10    |    SCORE: {s['final_score']}"
        if s.get("underdog_flag"):
            header += "    |    BREAKOUT WINNER"
        out.append(sep_eq)
        out.append(header)
        out.append(sep_eq)
        out.append("")
        verified = " (verified)" if ch.get("verified") else ""
        out.append(f"CREATOR:       @{ch.get('username') or 'unknown'}{verified}")
        out.append(f"FOLLOWERS:     {fmt_num(ch.get('followers'))}")
        out.append(f"RATIO:         {fmt_ratio(s.get('views_per_follower'))}x views per follower")
        out.append("")
        out.append(f"METRICS:       {fmt_num(v.get('views'))} views, {fmt_num(v.get('likes'))} likes, "
                   f"{fmt_num(v.get('shares'))} shares, {fmt_num(v.get('comments'))} comments, "
                   f"{fmt_num(v.get('bookmarks'))} saves")
        dur = (v.get("video") or {}).get("duration", 0)
        out.append(f"DURATION:      {dur} seconds")
        out.append(f"AGE:           {fmt_age(v.get('uploadedAt'))} ({fmt_date(v.get('uploadedAt'))})")
        out.append("")
        out.append(f"HASHTAGS:      {fmt_hashtags(v.get('hashtags'))}")
        out.append(f"AUDIO:         {fmt_song(v.get('song'))}")
        out.append(f"SEARCH QUERY:  {v.get('searchQuery') or 'unknown'}")
        out.append("")
        out.append(f"TIKTOK URL:    {v.get('postPage')}")
        out.append(f"CAPTION TEXT:  {(v.get('title') or '')[:500]}")
        out.append(f"TRANSCRIPT:    {'WHISPER AI (FALLBACK)' if t['source']=='whisper_fallback' else 'UNAVAILABLE'}")
        out.append("")
        out.append("HOOK LINE:")
        if t["source"] == "unavailable":
            out.append(">>> (transcript unavailable, rely on caption above)")
            out.append("")
            out.append("FULL TRANSCRIPT:")
            out.append("This video does not have usable speech content. Caption and hashtags are")
            out.append("above for reference. Text-overlay hooks may be present in the video itself.")
        else:
            out.append(f">>> {t['hook']}")
            out.append("")
            out.append("FULL TRANSCRIPT:")
            out.append(t["text"])
        out.append("")

    out.append(sep_eq)
    out.append("END OF SWIPE FILE")
    out.append(sep_eq)
    out.append("")
    out.append("HOW TO USE THIS FILE:")
    out.append("")
    out.append("1. Open the /ugc skill")
    out.append("2. Attach or paste this file when the skill asks for UGC inspiration")
    out.append("3. The script writer learns from these real viral hooks and writes new scripts")
    out.append("   grounded in actual language that stopped scroll in your niche")
    out.append("")
    out.append("v2 guarantee: every winner here passed an LLM relevance vet against your VOC.")
    out.append("No off-niche noise, no unrelated viral content padding the file.")
    out.append("")
    out.append("Scoring notes:")
    out.append("  REL (0-10) = VOC relevance. Higher is more directly on-niche.")
    out.append("  SCORE combines views, creator underdog ratio, engagement quality, recency.")
    out.append("  BREAKOUT WINNER = follower floor 100+ AND views/followers >= 50.")
    out.append("  These are cleanest examples of hooks carrying videos (not audience size).")

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"ugc-winners-v2-{today}.txt"
    scraper_root = output_dir / "05_UGC" / "scraper"
    niche_dir = scraper_root / niche_slug
    fallback_path = scraper_root / f"ugc-winners-v2-{today}-{niche_slug}.txt"

    path = None
    try:
        niche_dir.mkdir(parents=True, exist_ok=True)
        path = niche_dir / filename
    except OSError:
        scraper_root.mkdir(parents=True, exist_ok=True)
        path = fallback_path

    with path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print(f"Wrote: {path}")
    print(f"Size: {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
