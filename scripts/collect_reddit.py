#!/usr/bin/env python3
"""Collect a diversified pool of public r/nba comments via the pullpush.io archive API.

Reddit's own JSON API is IP-blocked from this environment (403), so we use pullpush.io,
the free public Reddit archive (no auth). We pull several slices designed to surface a
mix of discourse quality:
  - high-score comments (tend to include substantive analysis + popular takes)
  - comments matching evidence terms (more likely `analysis`)
  - comments matching emotional terms (more likely `reaction`)
  - general recent comments (everything else)
Output: data/raw_comments.json  (cleaned, deduped pool — NOT yet labeled)
"""
import json, re, time, urllib.parse, urllib.request, os

UA = "takemeter/0.1 (AI201 course project)"
BASE = "https://api.pullpush.io/reddit/search/comment/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw_comments.json")

# (params) slices. q terms bias the sample toward different labels; we still re-label by hand.
SLICES = [
    {"sort_type": "score", "sort": "desc", "size": 100},
    {"sort_type": "score", "sort": "desc", "size": 100, "q": "because"},
    {"sort_type": "score", "sort": "desc", "size": 100, "q": "net rating"},
    {"sort_type": "score", "sort": "desc", "size": 100, "q": "per game"},
    {"sort_type": "score", "sort": "desc", "size": 100, "q": "the reason"},
    {"sort_type": "score", "sort": "desc", "size": 100, "q": "stats"},
    {"size": 100, "q": "overrated"},
    {"size": 100, "q": "best player"},
    {"size": 100, "q": "trash"},
    {"size": 100, "q": "are you kidding"},
    {"size": 100, "q": "can't believe"},
    {"size": 100, "q": "heartbroken"},
    {"size": 100, "q": "buzzer"},
    {"size": 100, "q": "MVP"},
    {"size": 100, "q": "washed"},
    {"size": 100, "q": "scheme"},
]

BOT_MARKERS = ("i am a bot", "this action was performed automatically", "^^^", "AutoModerator")

def fetch(params):
    params = dict(params, subreddit="nba")
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r).get("data", [])
    except Exception as e:
        print("  fetch error:", e)
        return []

def clean(body):
    if not body:
        return None
    b = body.strip()
    if b.lower() in ("[deleted]", "[removed]"):
        return None
    if any(m.lower() in b.lower() for m in BOT_MARKERS):
        return None
    b = re.sub(r"&gt;", ">", b)
    b = re.sub(r"&amp;", "&", b)
    b = re.sub(r"https?://\S+", "", b)        # drop urls
    b = re.sub(r"/?u/\w+|/?r/\w+", "", b)      # drop user/sub mentions
    b = re.sub(r"\s+", " ", b).strip()
    if len(b) < 15 or len(b) > 1200:
        return None
    if b.count(" ") < 2:                       # need at least a few words
        return None
    return b

def main():
    seen, pool = set(), []
    for i, params in enumerate(SLICES):
        rows = fetch(params)
        kept = 0
        for r in rows:
            b = clean(r.get("body", ""))
            if not b:
                continue
            key = b.lower()[:120]
            if key in seen:
                continue
            seen.add(key)
            pool.append({"text": b, "score": r.get("score", 0)})
            kept += 1
        print(f"slice {i+1}/{len(SLICES)} {params.get('q','(top)'):16} -> {len(rows)} fetched, {kept} kept (pool={len(pool)})")
        time.sleep(1.2)   # be polite to the API
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(pool, f, indent=1, ensure_ascii=False)
    print(f"\nTOTAL clean pool: {len(pool)} -> {OUT}")

if __name__ == "__main__":
    main()
