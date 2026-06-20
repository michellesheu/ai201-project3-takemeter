#!/usr/bin/env python3
"""Heuristic PRE-labeler for the r/nba comment pool.

This produces *provisional* labels only. Every provisional label is reviewed and
corrected by hand (by reading the text) before it enters the final dataset — see
README AI-usage / planning.md annotation plan. The heuristic just buckets the pool
so review is balanced across the three classes.

Labels: analysis / hot_take / reaction  (see planning.md for definitions).
Outputs scripts/candidates.tsv : idx<TAB>provisional<TAB>margin<TAB>text
selecting up to CAP per provisional class, sorted by confidence margin desc.
"""
import json, re, os, math

HERE = os.path.dirname(__file__)
POOL = os.path.join(HERE, "..", "data", "raw_comments.json")
OUT = os.path.join(HERE, "candidates.tsv")
CAP = 110  # per provisional class

EVID = ["because", "the reason", "due to", "which means", "scheme", "spacing",
        "rotation", "net rating", "per game", "per 100", "usage", "efficiency",
        "true shooting", "ts%", "fg%", "splits", "sample size", "regular season",
        "playoff", "advanced stat", "on/off", "defensive rating", "offensive rating",
        "compared to", "historically", "if you look at", "the issue is", "the problem is"]
HOT = ["overrated", "underrated", "washed", "trash", "goat", "best player",
       "worst", "easily", "not close", "top 5", "top 3", "top 10", "mid",
       "carried", "fraud", "clown", "cooked", "better than", "no debate",
       "hot take", "unpopular opinion", "should be", "needs to", "deserves"]
REACT = ["heartbroken", "crying", "shaking", "can't believe", "cant believe",
         "are you kidding", "omg", "lmao", "lmfao", "insane", "unreal", "wtf",
         "let's go", "lets go", "i'm done", "im done", "no way", "holy", "wow",
         "speechless", "devastated", "ecstatic", "so happy", "i hate", "i love"]

def caps_ratio(t):
    letters = [c for c in t if c.isalpha()]
    if not letters:
        return 0.0
    return sum(c.isupper() for c in letters) / len(letters)

def score(t):
    tl = t.lower()
    words = tl.split()
    n = len(words)
    has_num = 1 if re.search(r"\b\d+(\.\d+)?%?\b", t) else 0
    a = sum(tl.count(k) for k in EVID) + 1.5 * has_num
    h = sum(tl.count(k) for k in HOT)
    r = sum(tl.count(k) for k in REACT) + 2.0 * t.count("!") * 0  # exclam handled below
    # length / style nudges
    excl = t.count("!")
    cr = caps_ratio(t)
    if n <= 12:
        r += 1.2
    if excl >= 1:
        r += 0.8 * min(excl, 3)
    if cr > 0.3 and len(t) > 6:
        r += 1.5
    if n >= 40:
        a += 1.0
    if has_num and any(k in tl for k in EVID):
        a += 1.5
    # an assertive opinion with no evidence and not very emotional -> hot_take
    if h > 0 and a < 1 and r < 1:
        h += 1.0
    return {"analysis": a, "hot_take": h, "reaction": r}

def main():
    pool = json.load(open(POOL))
    scored = []
    for i, item in enumerate(pool):
        t = item["text"]
        s = score(t)
        ranked = sorted(s.items(), key=lambda kv: kv[1], reverse=True)
        top, second = ranked[0], ranked[1]
        margin = top[1] - second[1]
        scored.append((i, top[0], round(margin, 2), top[1], t))
    buckets = {"analysis": [], "hot_take": [], "reaction": []}
    for row in sorted(scored, key=lambda x: x[2], reverse=True):
        lbl = row[1]
        if len(buckets[lbl]) < CAP and row[3] > 0:
            buckets[lbl].append(row)
    with open(OUT, "w") as f:
        for lbl in ("analysis", "hot_take", "reaction"):
            for idx, prov, margin, top, t in buckets[lbl]:
                f.write(f"{idx}\t{prov}\t{margin}\t{t}\n")
    print("provisional bucket sizes:", {k: len(v) for k, v in buckets.items()})
    print("wrote", OUT)

if __name__ == "__main__":
    main()
