# TakeMeter — Planning

> Working design notes for a fine-tuned classifier that scores discourse quality on **r/nba**.
> Written before data collection. Expanded across Milestones 1–3.

## Community

**r/nba** — the main NBA subreddit (~8M members). Discourse is constant, text-heavy, and
varies wildly in quality: deep tactical breakdowns sit next to one-line hot takes and pure
emotional venting after a buzzer-beater. That spread is exactly what makes it a good
classification target — the "is this a real argument or just a take?" distinction is one
r/nba regulars make instinctively, and it maps cleanly to three grounded labels.

## Label taxonomy (3 labels)

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

## Hard edge case + decision rule

**The borderline post:** the single-stat "gotcha" — e.g.
> "LeBron is overrated — his playoff win rate against top-seeded opponents is below .500."

Could be `analysis` (cites a stat) or `hot_take` (bold accusatory claim). **Decision rule:**
if the evidence is specific and verifiable *and* would support the claim with the opinion
framing removed → `analysis`. If the stat is vague, cherry-picked, or decorative — just enough
to sound credible but not actually reasoning → `hot_take`. The example above is one
cherry-picked stat selected for effect with accusatory framing → **`hot_take`**.

Second recurring edge: **emotional venting that names a reason** (`reaction` vs `hot_take`).
Rule: if it's a feeling about a specific event with no claim about a general truth → `reaction`;
if it asserts a general evaluative claim ("worst-run franchise") → `hot_take`.
