#!/usr/bin/env python3
"""Adapt scraptik/tiktok-api search output to the scoring schema.

scraptik returns one item per query run. The video list lives in
`search_item_list[].aweme_info` (NOT `aweme_list` which is always empty).

Input: JSON array of aweme_info objects (with optional `_query` tag).
Output: JSON array of normalized video dicts matching score_videos.py schema.

Usage:
    python adapt_scraptik.py input.json output.json
"""
import json
import re
import sys


def adapt_one(info: dict) -> dict:
    stats = info.get("statistics") or {}
    author = info.get("author") or {}
    video = info.get("video") or {}
    music = info.get("music") or {}

    hashtags = []
    for chunk in (info.get("text_extra") or []):
        name = chunk.get("hashtag_name")
        if name:
            hashtags.append(name)
    if not hashtags:
        hashtags = re.findall(r"#([^\s#]+)", info.get("desc") or "")

    aid = info.get("aweme_id")
    username = author.get("unique_id") or ""
    post_url = f"https://www.tiktok.com/@{username}/video/{aid}" if username and aid else None

    duration_raw = video.get("duration") or 0
    duration = duration_raw // 1000 if duration_raw > 1000 else duration_raw

    return {
        "id": aid,
        "title": info.get("desc") or "",
        "views": stats.get("play_count") or 0,
        "likes": stats.get("digg_count") or 0,
        "comments": stats.get("comment_count") or 0,
        "shares": stats.get("share_count") or 0,
        "bookmarks": stats.get("collect_count") or 0,
        "hashtags": hashtags,
        "channel": {
            "username": username,
            "followers": author.get("follower_count") or 0,
            "verified": bool(author.get("custom_verify") or author.get("enterprise_verify_reason")),
        },
        "uploadedAt": info.get("create_time") or 0,
        "video": {"duration": duration},
        "song": {"title": music.get("title") or "", "artist": music.get("author") or ""},
        "postPage": post_url,
        "searchQuery": info.get("_query"),
    }


def main():
    if len(sys.argv) != 3:
        print("Usage: python adapt_scraptik.py input.json output.json", file=sys.stderr)
        sys.exit(1)

    raw = json.load(open(sys.argv[1]))
    adapted = [adapt_one(i) for i in raw]
    json.dump(adapted, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
    print(f"Adapted {len(adapted)} items -> {sys.argv[2]}")


if __name__ == "__main__":
    main()
