# TakeMeter — Demo Video Shot List (3–5 min)

> The video is the only deliverable that must be recorded by hand. This script makes it quick:
> run `python3 scripts/predict.py` and read the beats below. Target 3–5 minutes.

## Setup (before recording)
```bash
python3 scripts/predict.py        # interactive mode, paste posts one per line
```

## Beat 1 — Intro (~30s)
- "This is TakeMeter, a fine-tuned DistilBERT classifier that labels r/nba comments as
  **analysis**, **hot_take**, or **reaction**." State the one-line definition of each.

## Beat 2 — 3–5 live classifications (~90s)
Paste these (have label + confidence visible on screen):
1. `Jokic had 28/14/6 on 59% TS while Shai had 30/6/7 on 63% TS with fewer turnovers — Shai outplayed him this series.`  → expect **analysis**
2. `Luka is already a top-3 player of his generation and it's not close.`  → expect **hot_take**
3. `ARE YOU FUCKING KIDDING ME. From halfcourt. I'm shaking.`  → expect **reaction**
4. `SGA is so overrated, only presence is at the free throw line.`  → expect **hot_take**
5. `The Pacers starting 5 had the 2nd-best net rating in the league this season, min 350 minutes.`  → expect **analysis**

## Beat 3 — One correct prediction, narrated (~45s)
- Pick #1 above. Narrate: "This is reasonable — the comment cites specific TS% and turnover
  numbers and builds a comparison, which is exactly the `analysis` definition. The model keyed
  on the statistical structure, not just the player names."

## Beat 4 — One incorrect prediction, narrated (~45s)
- Use one of the wrong test-set examples from the README's "wrong predictions" section
  (see Evaluation Report). Narrate which two labels got confused and why the boundary is hard
  (e.g. a single-stat hot take the model read as analysis).

## Beat 5 — Evaluation report walkthrough (~60s)
- Show the README evaluation table: baseline (Groq llama-3.3-70b) vs fine-tuned DistilBERT,
  overall accuracy + per-class F1, and the confusion matrix. One sentence on the headline
  finding (did fine-tuning beat the zero-shot baseline, and what that says about the task).
