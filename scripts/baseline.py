#!/usr/bin/env python3
"""Zero-shot baseline: Groq llama-3.3-70b-versatile classifies the SAME locked test set.

No task-specific training — just the label definitions in the prompt, instructed to emit
only the label name. Reads GROQ_API_KEY from the environment. Scores data/test_split.csv
(written by train.py so both models see identical rows) and writes the "baseline" section
into evaluation_results.json.

Run:  GROQ_API_KEY=... python3 scripts/baseline.py
"""
import json, os, time, urllib.request, urllib.error
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
TEST = os.path.join(ROOT, "data", "test_split.csv")
LABELS = ["analysis", "hot_take", "reaction"]
MODEL = "llama-3.3-70b-versatile"
ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

PROMPT = """You are classifying r/nba comments by discourse type. Assign exactly ONE label.

analysis  - a structured argument backed by specific, verifiable evidence (stats, historical
            comparison, tactical/scheme observation) that would stand even if the opinion
            framing were removed.
hot_take  - a bold, confident opinion asserted WITHOUT genuine supporting evidence. The claim
            might be true, but it is stated rather than argued.
reaction  - an immediate emotional response to a specific event, with little to no argument;
            the post is expressing a feeling in the moment.

Rules:
- A single cherry-picked/decorative stat used as ammunition is hot_take, not analysis.
- An emotional opener wrapping an unsupported evaluative claim is hot_take.
- Decorative reasoning in service of an in-the-moment feeling is reaction.

Respond with ONLY the label: analysis, hot_take, or reaction. No other text.

Comment:
\"\"\"{text}\"\"\""""

def classify(text, key):
    body = json.dumps({
        "model": MODEL, "temperature": 0,
        "messages": [{"role": "user", "content": PROMPT.format(text=text[:2000])}],
    }).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        # default urllib UA is 403'd by Groq's edge; use a normal one
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) takemeter-baseline/0.1"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                out = json.load(r)
            return out["choices"][0]["message"]["content"].strip().lower()
        except urllib.error.HTTPError as e:
            if e.code == 429:           # rate limit -> back off
                time.sleep(8 * (attempt + 1)); continue
            raise
    return ""

def parse(raw):
    raw = raw.lower()
    for l in LABELS:
        if l in raw or l.replace("_", " ") in raw:
            return l
    return None

def main():
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise SystemExit("set GROQ_API_KEY (the same key in your Colab secrets)")
    test = pd.read_csv(TEST)
    y_true, y_pred, unparsed = [], [], 0
    for i, row in test.iterrows():
        raw = classify(row["text"], key)
        lab = parse(raw)
        if lab is None:
            unparsed += 1
            lab = "hot_take"   # fallback for scoring; counted as unparsed below
        y_true.append(row["label"]); y_pred.append(lab)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(test)} done")
        time.sleep(0.4)        # stay under free-tier rate limit

    acc = accuracy_score(y_true, y_pred)
    report = classification_report(y_true, y_pred, labels=LABELS, target_names=LABELS,
                                   output_dict=True, zero_division=0)
    frac_unparsed = unparsed / len(test)
    print(f"\nBASELINE accuracy: {acc:.3f}   unparseable: {unparsed}/{len(test)} ({frac_unparsed:.1%})")
    print(classification_report(y_true, y_pred, labels=LABELS, target_names=LABELS, zero_division=0))
    if frac_unparsed > 0.10:
        print("WARNING: >10% unparseable — consider tightening the prompt's output instruction.")

    out_path = os.path.join(ROOT, "evaluation_results.json")
    existing = json.load(open(out_path)) if os.path.exists(out_path) else {}
    existing["baseline"] = {
        "model": MODEL, "approach": "zero-shot prompt, no training",
        "prompt": PROMPT,
        "accuracy": acc,
        "unparseable": unparsed, "unparseable_frac": frac_unparsed,
        "per_class": {l: {"precision": report[l]["precision"], "recall": report[l]["recall"],
                          "f1": report[l]["f1-score"], "support": report[l]["support"]} for l in LABELS},
        "macro_f1": report["macro avg"]["f1-score"],
    }
    json.dump(existing, open(out_path, "w"), indent=2)
    print("wrote evaluation_results.json (baseline section)")

if __name__ == "__main__":
    main()
