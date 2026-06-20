# TakeMeter — Planning

> Working design notes for a fine-tuned classifier that scores discourse quality on **r/nba**.
> Written before data collection. Expanded across Milestones 1–3.

---

## 1. Community

**r/nba** — the main NBA subreddit (~8M members). Discourse is constant, text-heavy, and
varies wildly in quality: deep tactical breakdowns sit next to one-line hot takes and pure
emotional venting after a buzzer-beater.

**Why it's a good fit for classification:** the spread of quality is the point. In a single
game thread you'll find a poster diagramming why a defense collapsed, another declaring a
player "washed" with zero evidence, and a third just screaming in all caps. Those three modes
are genuinely distinct, frequent enough to collect hundreds of each, and the
"real argument vs. just a take vs. just a feeling" distinction is one r/nba regulars make
instinctively. That makes the labels grounded in community norms rather than imposed from
outside.

## 2. Label taxonomy (3 labels)

The classifier assigns each post/comment **exactly one** of:

### `analysis`
**Definition:** The post makes a structured argument backed by specific, verifiable evidence —
statistics, historical comparison, or tactical observation — that would stand even if the
opinion framing were removed.

- *Example 1:* "Jokic's assist numbers go up because Denver runs everything through the elbow.
  When he's at the top of the key the spacing collapses and his AST% drops from 38 to 29 —
  it's a scheme thing, not a passing-ability thing."
- *Example 2:* "Three straight series the Celtics lost the non-Tatum/Brown minutes by double
  digits. Their bench net rating in the playoffs was -8.4. That's the actual problem, not the
  stars."
- *Uncertain:* "Embiid is the best center in the league, his per-game numbers prove it." —
  cites stats but vaguely and decoratively; leans `hot_take` (see decision rule).

### `hot_take`
**Definition:** A bold, confident opinion asserted without genuine supporting evidence — the
claim might be true, but the post states it rather than argues it.

- *Example 1:* "Luka is already a top-3 player of his generation and it's not close."
- *Example 2:* "The Lakers are flat-out wasting the back half of LeBron's career, worst-run
  franchise in the league right now."
- *Uncertain:* "Wemby changes everything about how you build a defense." — bold assertion,
  but borderline tactical; → `hot_take` unless it actually explains the mechanism.

### `reaction`
**Definition:** An immediate emotional response to a specific event, with little to no argument —
the post is expressing a feeling in the moment.

- *Example 1:* "ARE YOU KIDDING ME. From halfcourt. I'm shaking."
- *Example 2:* "I can't watch this team anymore man. Every single night. Heartbroken."
- *Uncertain:* "Worst loss of the season, the defense was a joke." — emotional, but "defense
  was a joke" gestures at a reason; → `reaction` because there's no actual evidence, just venting.

## 3. Hard edge cases

**The single-stat "gotcha"** (`analysis` vs `hot_take`) — e.g.
> "LeBron is overrated — his playoff win rate against top-seeded opponents is below .500."

Could be `analysis` (cites a stat) or `hot_take` (bold accusatory claim). **Decision rule:**
if the evidence is specific and verifiable *and* would support the claim with the opinion
framing removed → `analysis`. If the stat is vague, cherry-picked, or decorative — just enough
to sound credible but not actually reasoning → `hot_take`. The example above is one
cherry-picked stat selected for effect with accusatory framing → **`hot_take`**.

**Emotional venting that names a reason** (`reaction` vs `hot_take`). Rule: if it's a feeling
about a specific event with no claim about a general truth → `reaction`; if it asserts a
general evaluative claim ("worst-run franchise") → `hot_take`.

> Concrete annotation decisions made during labeling are logged in **§7. Hard annotation
> decisions** below.

## 4. Data collection plan

- **Source:** public r/nba **comments** (where takes actually live). Reddit's own JSON API is
  IP-blocked from the build environment (403), so collection goes through **pullpush.io**, the
  free public Reddit archive. The collector pulls 16 diversified slices (high-score comments +
  evidence-term queries like "net rating"/"per game" + emotional-term queries like
  "heartbroken"/"are you kidding") to surface a mix of all three classes. Reproducible:
  `scripts/collect_reddit.py` → 1,508 cleaned comments; `scripts/prelabel.py` buckets them;
  `scripts/build_dataset.py` produces the final balanced set.
- **Target:** ≥ 200 examples. Goal balance ~⅓ per label; hard floor **≥ 20% per label** and
  **no label > 70%** (per spec; I'll aim much tighter than that ceiling).
- **Underrepresented labels:** `analysis` is the rarest in the wild (substantive comments are
  outnumbered by reactions). If after a first pass a label is short, I'll targeted-collect:
  for `analysis`, pull from post-game tactical threads and high-score long comments; for
  `reaction`, pull from live game-thread bursts; then re-balance.
- **Format:** one CSV `data/takemeter_dataset.csv`, columns `text,label,notes` — single
  un-split file (the notebook does the 70/15/15 split). `notes` flags difficult cases.

## 5. Evaluation metrics

Accuracy alone is insufficient: the classes are not perfectly balanced and the *cost of each
confusion differs* (mislabeling `analysis` as `hot_take` is the failure that matters most for
a "discourse quality" tool). So I'll report:

- **Overall accuracy** — headline number, and the honest baseline-vs-fine-tuned comparison.
- **Per-class precision / recall / F1** — to see *which* distinction the model learned. F1 is
  the key per-class number; `analysis` recall matters most (catching real argumentation).
- **Macro-F1** — unweighted mean across classes, so a strong majority class can't hide a
  collapsed minority class.
- **Confusion matrix** — to read the *direction* of errors (e.g. analysis→hot_take), which is
  the actionable signal for what boundary the model missed.

## 6. Definition of success

A genuinely useful TakeMeter would:

- **Beat the zero-shot Groq baseline** on overall accuracy by a meaningful margin (the point of
  fine-tuning). If fine-tuning barely beats baseline, the labels are too easy or too noisy.
- Hit **macro-F1 ≥ 0.70** with **no single class F1 < 0.55** — i.e. it learned all three
  distinctions, not just the easy one.
- Keep the most important confusion — true `analysis` predicted as `hot_take` — **below ~25%**
  of `analysis` examples, since surfacing real argumentation is the tool's main job.

"Good enough to deploy" in a real r/nba tool (e.g. auto-flagging high-effort posts) =
macro-F1 ≥ 0.70 **and** `analysis` recall ≥ 0.70. Below that it would mislabel too much
substantive discussion to be trusted. These thresholds are objective — I can check each at the
end and state pass/fail.

## AI Tool Plan

This project generates little code, so AI tools help at three specific points:

- **Label stress-testing:** before annotating, I gave the label definitions + edge rules to an
  LLM and asked for 5–10 boundary posts. Any I couldn't classify cleanly → tightened the
  definition. (Outcome logged in §7.)
- **Annotation assistance:** I will use an LLM to **pre-label** the collected posts against the
  §2 definitions, then **review and correct every single label** by reading the post. This is
  disclosed in the README AI-usage section; pre-labels are never trusted unread.
- **Failure analysis:** after evaluation, I'll paste the misclassified test examples to an LLM
  and ask it to surface systematic patterns (label pair, post length, sarcasm), then **verify
  each pattern by re-reading** the examples before putting it in the report.

> Update this file before starting any stretch feature.

## 7. Hard annotation decisions

Final dataset: **212 examples**, distribution **analysis 72 (34%) / hot_take 70 (33%) /
reaction 70 (33%)** — well within the spec's ≤70% ceiling and ≥20% floor. The genuinely
difficult cases I had to rule on (these are the ones where my judgment overrode the heuristic
pre-label; full text in `data/takemeter_dataset.csv`, flagged in the `notes` column):

1. **Roster-construction argument that *sounds* like a hot take** — a long Bucks comment that
   repeatedly says "washed" (Middleton, Lopez) and reads like venting, but is actually a
   structured argument: it cites injuries, the CBA, contract situations, and reasons through
   why no coach was getting that roster past the second round. The cue words screamed
   `hot_take`; the *structure* is `analysis`. → **analysis**. Rule applied: judge the
   reasoning structure, not the vocabulary.

2. **Emotional opener wrapping an unsupported claim** — "Are you kidding me? Murray has been
   elite this series, Gordon has been insanely clutch, and Strawther just won them this game."
   Starts like a `reaction` (caps-adjacent outburst) but the body is a string of evaluative
   claims with no evidence — it's defending players by assertion. → **hot_take**. Rule:
   if the emotional frame is removed and an unsupported evaluative claim remains, it's a take.

3. **Hype that *looks* like analysis** — a long Mavs/Cooper-Flagg comment with a "redemption
   arc" narrative and a list of Flagg's traits. It has the length and structure of an argument,
   but every "point" is hype adjectives ("elite two-way potential, insane IQ") with zero
   evidence, and the whole thing is celebrating a draft result in the moment. → **reaction**.
   Rule: decorative reasoning in service of an in-the-moment feeling is still `reaction`.

4. **The single-stat gotcha** (per §3 rule) — short comments citing one cherry-picked stat
   with accusatory framing (e.g. SGA/Jokic FTA-disparity one-liners) were labeled by whether
   the stat actually *supports an argument* (→ analysis) or is *decorative ammunition*
   (→ hot_take). Most one-stat zingers landed as `hot_take`.

**Annotation process:** heuristic pre-label (keyword/length/style rules in `prelabel.py`) →
I read every candidate and corrected the label by hand → balanced selection in
`build_dataset.py`. Pre-labels were never trusted unread; the four reclassifications above are
where review changed the heuristic's guess. (Disclosed in README AI-usage.)
