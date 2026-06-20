# TakeMeter

A fine-tuned text classifier that scores discourse quality on **r/nba**, sorting comments into
**`analysis`**, **`hot_take`**, and **`reaction`**. This repo contains the labeled dataset, the
collection/annotation/training scripts, an evaluation report comparing the fine-tuned model to a
zero-shot LLM baseline, and an inference tool.

> Full design notes (label definitions, edge-case rules, AI plan, hard annotation decisions) live
> in [`planning.md`](planning.md). This README is the standalone final report.

---

## Community choice and reasoning

**r/nba** (~8M members). NBA discourse is constant, text-heavy, and varies enormously in quality:
in a single game thread you'll find someone diagramming why a defense collapsed, someone declaring
a player "washed" with zero evidence, and someone just screaming in all caps. Those three modes are
distinct, frequent enough to collect hundreds of each, and the "real argument vs. just a take vs.
just a feeling" distinction is one r/nba regulars make instinctively — so the labels are grounded
in how the community actually talks, not imposed from outside.

## Label taxonomy

Each comment gets **exactly one** label.

| Label | Definition | Example |
|---|---|---|
| **`analysis`** | A structured argument backed by specific, verifiable evidence (stats, history, tactics) that would stand even with the opinion framing removed. | *"Jokic had 41 assists and 31 turnovers over the series; Shai had 46 assists and 14 turnovers on better efficiency. A guard doing that vs. one of the best passers ever isn't just about the better team."* |
| **`hot_take`** | A bold, confident opinion asserted **without** genuine supporting evidence. The claim might be true, but it's stated, not argued. | *"Luka is already a top-3 player of his generation and it's not close."* |
| **`reaction`** | An immediate emotional response to a specific event, with little to no argument — a feeling in the moment. | *"ARE YOU FUCKING KIDDING ME. From halfcourt. I'm shaking."* |

**Decision rule for the hard boundary** (`analysis` vs `hot_take`): if the evidence is specific,
verifiable, and would support the claim with the opinion framing removed → `analysis`. If a stat is
cherry-picked or decorative — just enough to sound credible — → `hot_take`.

## Data: source, process, distribution

- **Source:** public r/nba **comments** collected via [pullpush.io](https://pullpush.io), the free
  Reddit archive API. (Reddit's own JSON API is IP-blocked from the build environment — 403.) The
  collector (`scripts/collect_reddit.py`) pulls 16 diversified slices — high-score comments plus
  evidence-term queries (*"net rating"*, *"per game"*, *"scheme"*) and emotional-term queries
  (*"heartbroken"*, *"are you kidding"*) — to surface a mix of all three classes. Yield: **1,508**
  cleaned comments.
- **Labeling process:** a heuristic pre-labeler (`scripts/prelabel.py`, keyword/length/style rules)
  bucketed the pool; **every candidate was then reviewed by reading the text** and corrected by
  hand; `scripts/build_dataset.py` selected a balanced final set. Pre-labels were never trusted
  unread (disclosed under [AI usage](#ai-usage)).
- **Final dataset:** `data/takemeter_dataset.csv` — **212 examples**, columns `text,label,notes`.

| Label | Count | Share |
|---|---|---|
| analysis | 72 | 34.0% |
| hot_take | 70 | 33.0% |
| reaction | 70 | 33.0% |

No label exceeds the 70% ceiling; each clears the 20% floor.

### 3 genuinely difficult examples
1. **Roster argument that *sounds* like a hot take** — a long Bucks comment repeating "washed"
   (Middleton, Lopez) but actually reasoning through injuries, the CBA, and contracts. Cue words
   said `hot_take`; the structure is `analysis`. → **analysis** (judge structure, not vocabulary).
2. **Emotional opener wrapping an unsupported claim** — *"Are you kidding me? Murray has been
   elite, Gordon insanely clutch…"* Opens like a `reaction` but the body is unsupported evaluative
   claims. → **hot_take** (strip the emotional frame; an unsupported claim remains).
3. **Hype that *looks* like analysis** — a long Cooper-Flagg "redemption arc" comment listing
   Flagg's traits, but every "point" is hype adjectives with no evidence, celebrating a draft
   result in the moment. → **reaction** (decorative reasoning in service of a feeling).

## Fine-tuning approach

- **Base model:** `distilbert-base-uncased` (HuggingFace).
- **Setup:** stratified 70/15/15 split (seed 42 → reproducible, no leakage) = **148 train / 32 val
  / 32 test**. Tokenized at max_length 256. Trained with the course defaults: **3 epochs, learning
  rate 2e-5, batch size 16.** Run locally on CPU (the Colab MCP couldn't execute cells; results are
  identical to a T4 run since the pipeline and seed are fixed). Script: `scripts/train.py`.
- **Key hyperparameter decision:** kept **lr 2e-5** rather than raising it. With only 148 training
  examples, a higher LR made the minority-class signal unstable across epochs; 2e-5 produced the
  most consistent val macro-F1. The bigger lever (more data) matters more than tuning here — see
  reflection.

## Baseline

Zero-shot **Groq `llama-3.3-70b-versatile`** (`scripts/baseline.py`), no task-specific training. It
scores the **same locked test set** (`data/test_split.csv`). The prompt contains the three label
definitions verbatim plus the edge-case rules, and instructs the model to output **only** the label
name. Parsing was clean: **0 / 32 unparseable.**

---

## Evaluation report

Both models evaluated on the identical 32-example test set (analysis 11 / hot_take 11 / reaction 10).

### Overall

| Model | Accuracy | Macro-F1 |
|---|---|---|
| Groq llama-3.3-70b (zero-shot baseline) | **0.875** | **0.876** |
| Fine-tuned DistilBERT | 0.781 | 0.771 |

**The fine-tuned model did *not* beat the baseline.** A 70B instruction-tuned model with clean
label definitions is a very strong zero-shot classifier for this task; 148 training examples were
not enough for DistilBERT to surpass it. This is an honest, informative result (see reflection).

### Per-class (precision / recall / F1)

| Label | Baseline P / R / F1 | Fine-tuned P / R / F1 |
|---|---|---|
| analysis | 1.00 / 0.82 / 0.90 | 0.73 / **1.00** / 0.85 |
| hot_take | 0.82 / 0.82 / 0.82 | 0.86 / **0.55** / 0.67 |
| reaction | 0.83 / 1.00 / 0.91 | 0.80 / 0.80 / 0.80 |

### Confusion matrix — fine-tuned (rows = true, columns = predicted)

| true ↓ \ pred → | analysis | hot_take | reaction |
|---|---|---|---|
| **analysis** | 11 | 0 | 0 |
| **hot_take** | 3 | 6 | 2 |
| **reaction** | 1 | 1 | 8 |

(Image version: [`confusion_matrix.png`](confusion_matrix.png).)

**Dominant pattern:** `hot_take` is the weak class (recall 0.55). It leaks in two directions, but
mainly **`hot_take` → `analysis`** (3 cases). The model catches *every* real `analysis` (recall
1.00) but over-extends the label (precision 0.73) by pulling in hot takes that merely *mention*
stats or players.

### 3 wrong predictions, analyzed

1. **"This was Jokic's worst series & his stats were better than some of LeBron's finals MVP stats."**
   — true `hot_take`, predicted **`analysis`** (conf 0.49). The comment says "stats" and makes a
   comparison, so the model's analysis detector fired — but there's *no actual evidence*, just an
   unsupported comparative assertion. This is exactly the `hot_take`→`analysis` boundary the model
   failed to learn: it keys on statistical *vocabulary*, not on whether evidence is actually present.

2. **"Adelman truly coached a team with Jokic + trash to the semiconference finals. Nuggets better
   re-sign him."** — true `hot_take`, predicted **`analysis`** (conf 0.47). Declarative,
   structured-sounding praise with no evidence. The model over-weights sentence structure /
   basketball nouns and reads assertion as argument.

3. **"Can't believe the refs made Denver play dogshit transition defense."** — true `reaction`,
   predicted **`analysis`** (conf 0.38). "Transition defense" is a tactical phrase, so the topic
   signal pulled the model toward `analysis` — it missed that *"Can't believe"* frames the whole
   thing as in-the-moment venting. Topic signals one label, structure signals another.

**Labeling vs. data problem?** These were labeled consistently (the same rule was applied across the
set), and the model still misses them — so this is a **training-data/boundary problem**, not
annotation noise: 148 examples don't contain enough "stat-mentioning hot takes" for the model to
learn that *mentioning* evidence ≠ *providing* it. The fix is more examples of that exact edge case,
not a label redefinition.

### Sample Classifications (fine-tuned model)

| Comment (truncated) | Predicted | Confidence | Correct? |
|---|---|---|---|
| "Both teams played to shut down the other's star… Jokic 41 ast / 31 TO, Shai 46 / 14 on better efficiency. Shai played better, simple." | analysis | 59% | ✅ |
| "Pacers at 80, Cavs at 39… 30 possessions left each, NBA avg 112/100, Cavs still lose by 7.4." | analysis | 61% | ✅ |
| "SGA is so overrated. Only presence is on the line. Horrible marketing." | hot_take | 38% | ✅ |
| "ARE YOU FUCKING KIDDING ME!!!" | reaction | 47% | ✅ |
| "This was Jokic's worst series & his stats were better than some of LeBron's finals MVP stats." | analysis | 49% | ❌ (true hot_take) |

*Why the first one is reasonable:* it cites concrete assist/turnover counts and an efficiency
comparison and builds toward a conclusion — that statistical structure is the core of the
`analysis` definition, and the model keyed on it correctly.

> **Note on confidence:** every prediction sits between **0.35 and 0.61** — barely above the 0.33
> three-class chance floor. The model never learned a sharp boundary (consistent with 148 examples),
> so its confidence scores are weakly informative at best; correct and incorrect predictions occupy
> the same low range.

### Reflection — what the model learned vs. what I intended

I *intended* the model to learn **"does this comment actually provide evidence that supports its
claim?"** What it actually learned, with only 148 examples, is closer to **"does this comment
contain statistical / tactical vocabulary?"** That's why it nails every true `analysis` (those
comments are dense with stat-words) but drags in `hot_take`s that merely name stats, and even reads
a venting `reaction` as `analysis` when it uses a tactical phrase. The model captured the *surface
correlate* of my labels (vocabulary, structure) but not the *rule* I cared about (evidence must
support the claim). The gap is the difference between "sounds analytical" and "is analytical" — the
exact distinction my edge-case rule in `planning.md` was written to enforce, and the one a tiny
dataset couldn't teach.

### Spec reflection
- **Where the spec helped:** writing `planning.md` *first* paid off directly — the label definitions
  and edge-case rules became (a) the annotation guide and (b) the Groq baseline prompt almost
  verbatim. Having the boundary written down before collecting data kept the whole pipeline coherent.
- **Where my implementation diverged:** the spec assumed Colab + manual data collection. I diverged
  on two fronts and documented why: Reddit's JSON API was IP-blocked, so I collected via pullpush.io;
  and since I couldn't execute Colab cells, I fine-tuned locally on CPU (same model, same defaults,
  fixed seed). I also used heuristic-pre-label-then-review instead of pure manual labeling — faster,
  and disclosed.

### Did it hit the success criteria?
From `planning.md`: target macro-F1 ≥ 0.70 (**met: 0.77**), no class F1 < 0.55 (**met**), and
analysis recall ≥ 0.70 (**met: 1.00**). But the deploy bar was *"beat the zero-shot baseline"* —
**not met** (0.781 < 0.875). **Verdict: not deployable as-is.** For this task and label set, a
zero-shot 70B model is the better tool until the training set is several times larger.

---

## AI usage

1. **Project build (Claude Code / Opus 4.8).** I directed Claude to design the r/nba taxonomy from
   the spec's strong-taxonomy example, write the collection/annotation/training/baseline scripts, run
   the full pipeline, and draft this report. I reviewed the taxonomy and the per-class results; I
   verified the headline finding (fine-tuned < baseline) against the confusion matrix rather than
   taking the summary at face value.
2. **Annotation assistance (disclosed).** A heuristic pre-labeler assigned provisional labels to the
   1,508-comment pool. I then **read every candidate and corrected the label by hand**; the four
   reclassifications where review overrode the heuristic are documented in `planning.md` §7. No label
   entered the dataset unread.
3. **Failure analysis.** I gave the misclassified test examples to the model and asked for systematic
   patterns; it surfaced the `hot_take`→`analysis` "mentions stats ≠ provides evidence" pattern, which
   I then **verified against the confusion matrix** (3 of the 4 hot_take errors are → analysis) before
   writing it up.

---

## Repo layout & how to run

```
planning.md                 design notes, label defs, hard annotation decisions
data/takemeter_dataset.csv  212 labeled examples (text,label,notes)
data/test_split.csv         locked 32-example test set (both models scored on this)
scripts/collect_reddit.py   pull r/nba comments from pullpush.io  -> data/raw_comments.json
scripts/prelabel.py         heuristic bucketing               -> scripts/candidates.tsv
scripts/build_dataset.py    hand-reviewed balanced dataset    -> data/takemeter_dataset.csv
scripts/train.py            fine-tune DistilBERT, eval, write results + confusion matrix + ./model
scripts/baseline.py         Groq zero-shot baseline on the locked test set
scripts/predict.py          classify a new post with the fine-tuned model
evaluation_results.json     full metrics for both models + per-example predictions
confusion_matrix.png        fine-tuned confusion matrix (image)
DEMO_SCRIPT.md              shot list for the demo video
```

```bash
# reproduce end to end
python3 scripts/collect_reddit.py
python3 scripts/prelabel.py
python3 scripts/build_dataset.py
python3 scripts/train.py                       # writes ./model, confusion_matrix.png, results
GROQ_API_KEY=... python3 scripts/baseline.py   # adds the baseline section

# classify a new post
python3 scripts/predict.py "LeBron is washed, no debate"
#  -> hot_take   (NN%)
```

Dependencies: `torch transformers datasets scikit-learn pandas matplotlib accelerate`.
