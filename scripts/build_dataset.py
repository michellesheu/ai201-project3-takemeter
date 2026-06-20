#!/usr/bin/env python3
"""Build the final labeled dataset from the reviewed pool.

The heuristic pre-labeler (prelabel.py) bucketed the pool; I then read every
candidate and hand-picked a balanced set, CORRECTING the provisional label where
the heuristic was wrong (see HARD_NOTES below — those reclassifications are the
genuinely difficult cases logged in planning.md). Indices reference position in
data/raw_comments.json.

Output: data/takemeter_dataset.csv  (columns: text,label,notes) — single un-split file.
"""
import json, csv, os

HERE = os.path.dirname(__file__)
POOL = json.load(open(os.path.join(HERE, "..", "data", "raw_comments.json")))
OUT = os.path.join(HERE, "..", "data", "takemeter_dataset.csv")

ANALYSIS = [215,341,105,118,197,352,1501,238,242,225,228,241,248,252,254,285,304,
    309,332,548,679,1419,1437,1438,1456,1457,1463,260,201,219,221,244,246,249,270,
    277,296,302,306,308,321,323,335,338,345,348,355,367,535,697,713,1171,1203,1217,
    1272,1465,1466,1499,253,1470,275,279,283,291,293,295,299,312,331,340,344,1337]

HOT_TAKE = [1352,1381,483,572,623,639,706,729,1255,1320,1357,1371,418,567,568,580,
    586,587,593,598,601,603,605,613,628,631,634,636,637,638,641,642,644,646,647,652,
    661,667,670,678,685,704,712,733,766,773,775,782,783,787,793,804,805,816,818,832,
    837,841,842,843,845,847,848,1249,1270,1285,1312,1340,1350,866]

REACTION = [882,212,991,881,905,911,906,1307,1077,814,879,889,890,980,1090,54,1011,
    1092,57,13,21,24,48,81,899,869,250,39,853,860,867,896,902,903,918,920,927,934,
    936,983,986,995,1000,1005,1006,1007,1024,1031,1037,1038,1055,1057,1069,1076,1079,
    1081,1082,1087,1093,1097,1115,1116,1126,1056,1212,1186,858,868,925,992]

# Genuinely-hard cases where I overrode the heuristic's provisional label.
HARD_NOTES = {
    1337: "HARD: heuristic guessed hot_take (cue: 'washed'), but it's a structured "
          "roster-construction argument citing injuries/contracts -> analysis.",
    866:  "HARD: opens emotionally ('Are you kidding me?') so heuristic said reaction, "
          "but the substance is unsupported evaluative claims defending players -> hot_take.",
    906:  "HARD: long and reads like an argument, but it's emotional hype celebrating the "
          "Flagg pick; the reasoning is decorative -> reaction (a feeling in the moment).",
    992:  "HARD: heuristic said hot_take, but 'I can't believe we're on to the final...' "
          "is excitement with no claim -> reaction.",
}

def build():
    rows = []
    for label, idxs in (("analysis", ANALYSIS), ("hot_take", HOT_TAKE), ("reaction", REACTION)):
        for i in idxs:
            rows.append({"text": POOL[i]["text"], "label": label, "notes": HARD_NOTES.get(i, "")})
    # interleave so the file isn't grouped by label (cleaner for any naive viewer; the
    # notebook shuffles before splitting anyway)
    by_label = {"analysis": [], "hot_take": [], "reaction": []}
    for r in rows:
        by_label[r["label"]].append(r)
    interleaved = []
    maxlen = max(len(v) for v in by_label.values())
    for i in range(maxlen):
        for lbl in ("analysis", "hot_take", "reaction"):
            if i < len(by_label[lbl]):
                interleaved.append(by_label[lbl][i])
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["text", "label", "notes"])
        w.writeheader()
        w.writerows(interleaved)
    dist = {l: len(v) for l, v in by_label.items()}
    total = sum(dist.values())
    print(f"wrote {total} rows -> {OUT}")
    for l, c in dist.items():
        print(f"  {l:9} {c:3}  ({100*c/total:.1f}%)")
    assert total >= 200, "need >=200"
    assert max(dist.values()) / total <= 0.70, "a label exceeds 70%"
    assert min(dist.values()) / total >= 0.20, "a label under 20%"
    print("balance OK: >=200, each >=20%, none >70%")

if __name__ == "__main__":
    build()
