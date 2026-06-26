#!/usr/bin/env python3
"""Parse WebVTT (from scrape-creators/best-tiktok-transcripts-scraper) into clean plain text.

Usage:
    python parse_webvtt.py <url_or_text>                     # prints transcript to stdout
    python parse_webvtt.py <url_or_text> --hook-only         # prints just the hook
    echo "<vtt content>" | python parse_webvtt.py -          # read from stdin

The scrape-creators actor returns WebVTT directly in the `transcript` field
(no URL fetch needed). If called with a string that looks like WebVTT,
parse it in place. If called with a URL, fetch first then parse.
"""
import re
import sys
import urllib.request
import urllib.error

TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}")
CUE_ID_RE = re.compile(r"^\d+$")
TAG_RE = re.compile(r"<[^>]+>")


def fetch_webvtt(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        raise RuntimeError(f"Failed to fetch WebVTT: {e}")


def parse_webvtt(content: str) -> str:
    if not content:
        return ""
    speech_lines = []
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
            speech_lines.append(s)
    text = " ".join(speech_lines)
    return re.sub(r"\s+", " ", text).strip()


def extract_hook(transcript: str, max_words: int = 12) -> str:
    if not transcript:
        return ""
    words = transcript.split()
    hook = " ".join(words[:max_words])
    if len(words) > max_words:
        hook += "..."
    return hook


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_webvtt.py <url_or_text_or_-> [--hook-only]", file=sys.stderr)
        sys.exit(1)

    arg = sys.argv[1]
    hook_only = "--hook-only" in sys.argv

    if arg == "-":
        content = sys.stdin.read()
    elif arg.startswith("http://") or arg.startswith("https://"):
        try:
            content = fetch_webvtt(arg)
        except RuntimeError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        content = arg

    transcript = parse_webvtt(content)
    if not transcript:
        print("ERROR: Empty transcript after parsing", file=sys.stderr)
        sys.exit(3)

    print(extract_hook(transcript) if hook_only else transcript)


if __name__ == "__main__":
    main()
