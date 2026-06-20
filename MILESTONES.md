# TakeMeter — Project Milestones

> **STATUS (2026-06-19):** M1–M6 complete and committed (one commit each, see `git log`).
> Community = r/nba (`analysis`/`hot_take`/`reaction`); 212-example dataset; Groq baseline
> 0.875 acc vs fine-tuned DistilBERT 0.781. Report in `README.md`.
> **Remaining = manual only:** record the 3–5 min demo video (`DEMO_SCRIPT.md` is the shot
> list) and submit to the Course Portal. Deployed-interface stretch is partly covered by
> `scripts/predict.py`.


**Due:** Sunday, June 21st 2026, 11:59PM PDT
**Total time:** ~9–11 hours
**Build:** Fine-tuned text classifier scoring discourse quality in an online community.

**Stack:** `distilbert-base-uncased` (HuggingFace) · Google Colab (free T4 GPU) · `transformers` + `datasets` + `scikit-learn` · Groq `llama-3.3-70b-versatile` (baseline).

---

## Setup (do first)

- [ ] Create GitHub repo `ai201-project3-takemeter` (holds `planning.md`, dataset CSV, `README.md`, `evaluation_results.json`, `confusion_matrix.png`).
- [ ] Make copy of starter Colab notebook: File → Save a copy in Drive.
- [ ] Set runtime to T4 GPU: Runtime → Change runtime type → T4 GPU → Save. Do BEFORE running cells.
- [ ] Add Groq key via Colab Secrets: 🔑 sidebar → secret named `GROQ_API_KEY` → enable notebook access. Never commit key.

---

## Milestone 1 — Choose Community + Define Labels (~45 min)

- [ ] Pick one community: active, text-heavy, varied quality, ≥200 public posts collectable. (e.g. r/nba, r/soccer, r/LetsTalkMusic, r/television, r/smashbros).
- [ ] Read 30–40 real posts before designing labels. See what patterns emerge.
- [ ] Define 2–4 labels. Each must be: mutually exclusive, exhaustive (≥90% labelable, no "other" bucket), grounded in community norms.
- [ ] Per label write: 1-sentence definition, 2 clear examples, 1 uncertain post.
- [ ] Find one genuinely ambiguous post. Write the labels it could be + your decision rule.
- [ ] Check mutual exclusivity. Merge/redefine if labels overlap.
- [ ] Write 2–3 sentence description of community + labels + why distinctions matter.

**Checkpoint:** can state labels with defs + 2 examples each, and name hardest edge case + how you'll handle it.

---

## Milestone 2 — Write planning.md (~45 min)

Write BEFORE collecting any labeled data. Design structure yourself. Must address 6 questions:

- [ ] **Community** — what + why; why discourse is varied enough.
- [ ] **Labels** — 2–4 labels, full-sentence def each, 2 examples each.
- [ ] **Hard edge cases** — what post is ambiguous between two labels + handling rule.
- [ ] **Data collection plan** — where, how many per label, what if a label underrepresented after 200.
- [ ] **Evaluation metrics** — which + why right for this task (accuracy alone NOT enough).
- [ ] **Definition of success** — specific performance threshold for "good enough to deploy".
- [ ] Add **AI Tool Plan** section covering: label stress-testing, annotation assistance, failure analysis (explicit decision on each).

**Checkpoint:** all 6 questions answered substantively; defs precise; success = specific threshold.

---

## Milestone 3 — Collect + Annotate Dataset (~3–4 hours)

- [ ] Collect ≥200 public posts/comments. Manual copy-paste fine (~1–2h). Don't make it a coding project.
- [ ] Save ONE CSV, columns: `text`, `label`, + notes column. NOT pre-split (notebook splits 70/15/15).
- [ ] (Optional) LLM pre-label batch, then review+correct EVERY label. Disclose if used.
- [ ] Label each example by reading it. Keep running list of pause-cases (post, candidate labels, decision).
- [ ] Count per label. If any label >70%, collect more of underrepresented labels. Aim ≥20% per label.
- [ ] Put ≥3 difficult examples + decisions into planning.md Hard Edge Cases section.

**Checkpoint:** ≥200 examples in single CSV, no label >70%, 3 hard cases documented.

---

## Milestone 4 — Run Baseline (~1 hour)

Zero-shot Groq baseline on locked test set, BEFORE fine-tuning.

- [ ] Open Colab copy. Confirm T4 GPU.
- [ ] Run Section 1: define label map + upload CSV.
- [ ] Run Section 2: split (70/15/15) + tokenize. Review split sizes + label distribution.
- [ ] Section 5: add Groq key + write classification prompt (include label defs from planning.md, instruct model to output ONLY label name).
- [ ] Run baseline cells. Print accuracy + per-class metrics. If >~10% unparseable, fix prompt clarity.
- [ ] Note where baseline struggled + which labels it confuses. Write hypothesis to test post-fine-tune.

**Checkpoint:** baseline accuracy + per-class numbers saved. Fine-tuned model NOT yet run.

---

## Milestone 5 — Fine-Tune (~1.5–2 hours)

> Sections 1, 2, 5 already done from M4. Re-run only if Colab runtime reset.

- [ ] Run Section 3: load + fine-tune `distilbert-base-uncased`. ~5–15 min. Defaults: 3 epochs, lr 2e-5, batch 16. Note any hyperparameter changes + why (→ README).
- [ ] Run Section 4: evaluate fine-tuned model on test set. Per-class metrics + `confusion_matrix.png`. Pick 3 wrong predictions to analyze.
- [ ] Run Section 6: side-by-side baseline vs fine-tuned + write `evaluation_results.json`.
- [ ] Download `evaluation_results.json` + `confusion_matrix.png`. Commit to repo.

**Checkpoint:** fine-tuning ran clean, results comparable to baseline. If worse across board → check label leakage / imbalance / training bug.

---

## Milestone 6 — Evaluate, Document, Record (~1–2 hours)

- [ ] Use AI tool to surface patterns in wrong predictions, then VERIFY by re-reading. Note what you corrected/discarded.
- [ ] Write evaluation report in README:
  - [ ] Overall accuracy — both models.
  - [ ] Per-class metrics (precision/recall/F1) — both models.
  - [ ] Confusion matrix as markdown TABLE in README (not only the PNG).
  - [ ] ≥3 wrong predictions with deep analysis: which labels confused, why boundary hard, labeling vs data problem, what would fix it.
  - [ ] **Sample Classifications**: 3–5 posts run through model w/ predicted label + confidence; ≥1 correct example explained.
- [ ] Write reflection: what model captured vs what you intended (overfit? missed?).
- [ ] Write spec reflection: 1 way spec helped + 1 way implementation diverged + why.
- [ ] Write AI usage section: ≥2 specific instances (what directed, what produced, what changed/overrode). Disclose annotation assistance.
- [ ] Complete full README (all submission-checklist sections, each substantive).
- [ ] Record 3–5 min demo: 3–5 classifications w/ label+confidence, 1 correct narrated, 1 incorrect narrated, walkthrough of eval report.

**Checkpoint:** eval report w/ both models + confusion matrix + 3 analyzed failures; reflection on intended-vs-learned gap; README complete; demo recorded.

---

## Submit (Course Portal)

- [ ] GitHub repo link
- [ ] `planning.md` in repo root
- [ ] Labeled dataset CSV in repo (or linked from README)
- [ ] `README.md` with: community choice + reasoning · label taxonomy (defs + 2 examples) · data source/process/distribution + 3 hard examples · fine-tuning approach + 1 hyperparameter decision · baseline description + prompt · full eval report (both models, confusion matrix table, 3 wrong predictions, sample-classifications table) · reflection · spec reflection · AI usage section
- [ ] Demo video (3–5 min)

---

## Stretch (extra credit — update planning.md before starting each)

- [ ] **Inter-annotator reliability** — 2nd person labels 30+; report Cohen's kappa / % agreement; analyze disagreements.
- [ ] **Confidence calibration** — does 90%-confident beat 60%-confident?
- [ ] **Error pattern analysis** — systematic error pattern, not just individual cases.
- [ ] **Deployed interface** — UI takes post → shows label + confidence; commit code + run docs.
