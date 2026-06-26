#!/usr/bin/env python3
"""Underdog scoring with follower floor on the breakout tag.

Input: JSON array of adapted video objects (from adapt_scraptik.py).
Output: JSON with stats + top_n videos, creator-capped, scored and sorted.

Usage:
    python score_videos.py input.json output.json [top_n=80]

Scoring:
    FinalScore = ViewPower * CreatorUnderdog * EngagementQuality * Recency

The breakout flag requires views/followers >= 50 AND followers >= 100,
so burner/bot accounts (under 100 followers) never get tagged as
"pure breakouts" even if the ratio math is favorable.
"""
import json
import math
import sys
import time
from collections import defaultdict


def view_power(views: int) -> float:
    if views < 1000:
        return 0.1
    return min(math.log10(views) / 7.0, 1.0)


def creator_underdog(views: int, followers: int) -> float:
    if followers <= 0:
        return 1.0
    ratio = views / followers
    if ratio >= 100:
        return 3.0
    if ratio >= 20:
        return 2.0
    if ratio >= 5:
        return 1.5
    if ratio >= 1:
        return 1.0
    return 0.5


def engagement_quality(views, likes, comments, shares, saves):
    if views <= 0:
        return 0.7
    weighted = (likes + 3 * comments + 5 * shares + 5 * saves) / views
    if weighted > 0.15:
        return 1.5
    if weighted > 0.08:
        return 1.2
    if weighted > 0.04:
        return 1.0
    return 0.7


def recency(uploaded_at_unix):
    if not uploaded_at_unix:
        return 1.0
    age_days = (time.time() - uploaded_at_unix) / 86400
    if age_days < 7:
        return 1.3
    if age_days < 30:
        return 1.0
    if age_days < 60:
        return 0.8
    return 0.6


def hard_filter(v):
    if (v.get("views", 0) or 0) < 10000:
        return False
    duration = ((v.get("video") or {}).get("duration") or 0)
    if duration < 5 or duration > 180:
        return False
    if (v.get("shares", 0) or 0) == 0 and (v.get("comments", 0) or 0) < 5:
        return False
    if not ((v.get("channel") or {}).get("username")):
        return False
    uploaded_at = v.get("uploadedAt", 0) or 0
    if uploaded_at == 0:
        return False
    age_days = (time.time() - uploaded_at) / 86400
    if age_days > 90:
        return False
    return True


def score_video(v):
    views = v.get("views", 0) or 0
    likes = v.get("likes", 0) or 0
    comments = v.get("comments", 0) or 0
    shares = v.get("shares", 0) or 0
    saves = v.get("bookmarks", 0) or 0
    followers = ((v.get("channel") or {}).get("followers") or 0)
    uploaded_at = v.get("uploadedAt", 0) or 0

    vp = view_power(views)
    cu = creator_underdog(views, followers)
    eq = engagement_quality(views, likes, comments, shares, saves)
    rc = recency(uploaded_at)
    final = vp * cu * eq * rc

    vpf = (views / followers) if followers > 0 else 0
    underdog_flag = vpf >= 50 and followers >= 100

    return {
        "view_power": round(vp, 3),
        "creator_underdog": round(cu, 3),
        "engagement_quality": round(eq, 3),
        "recency": round(rc, 3),
        "final_score": round(final, 3),
        "views_per_follower": round(vpf, 1),
        "underdog_flag": underdog_flag,
    }


def creator_cap(videos, max_per=2):
    seen = defaultdict(int)
    kept = []
    for v in videos:
        u = (v.get("channel") or {}).get("username") or "unknown"
        if seen[u] < max_per:
            kept.append(v)
            seen[u] += 1
    return kept


def main():
    if len(sys.argv) < 3:
        print("Usage: python score_videos.py input.json output.json [top_n=80]", file=sys.stderr)
        sys.exit(1)
    top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 80

    raw = json.load(open(sys.argv[1]))
    if not isinstance(raw, list):
        raw = raw.get("items", []) if isinstance(raw, dict) else []

    scraped = len(raw)
    survivors = [v for v in raw if hard_filter(v)]
    for v in survivors:
        v["_scoring"] = score_video(v)
    survivors.sort(key=lambda v: v["_scoring"]["final_score"], reverse=True)
    capped = creator_cap(survivors, max_per=2)
    top = capped[:top_n]

    breakouts = sum(1 for v in top if v["_scoring"]["underdog_flag"])
    avg = sum(v["_scoring"]["final_score"] for v in top) / max(1, len(top))

    result = {
        "stats": {
            "scraped": scraped,
            "survivors": len(survivors),
            "capped": len(capped),
            "top_n": len(top),
            "breakouts": breakouts,
            "avg_score": round(avg, 3),
        },
        "top_n": top,
    }
    json.dump(result, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)

    print(f"Scraped: {scraped}")
    print(f"Survivors: {len(survivors)}")
    print(f"Top-{top_n}: {len(top)}")
    print(f"Breakouts: {breakouts}")
    print(f"Avg score: {avg:.3f}")


if __name__ == "__main__":
    main()
