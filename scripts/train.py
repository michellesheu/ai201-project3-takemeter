#!/usr/bin/env python3
"""Fine-tune distilbert-base-uncased on the TakeMeter dataset (local CPU).

Mirrors the course Colab notebook: same base model, same default hyperparameters
(3 epochs, lr 2e-5, batch size 16), same 70/15/15 split. Runs on CPU here instead of a
T4 GPU. Writes:
  - confusion_matrix.png         (fine-tuned model, test set)
  - evaluation_results.json      (fine-tuned section; baseline.py fills the baseline section)
  - data/test_split.csv          (locked test set, so the Groq baseline scores the SAME rows)

Reproducible: fixed seed 42 for the stratified split.
"""
import json, os, numpy as np, pandas as pd
import torch
from datasets import Dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_recall_fscore_support,
                             classification_report, confusion_matrix)
from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                          TrainingArguments, Trainer, set_seed)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "takemeter_dataset.csv")
MODEL = "distilbert-base-uncased"
LABELS = ["analysis", "hot_take", "reaction"]
L2I = {l: i for i, l in enumerate(LABELS)}
I2L = {i: l for l, i in L2I.items()}
SEED = 42

def split(df):
    # 70/15/15 stratified, fixed seed -> reproducible, no leakage
    train, tmp = train_test_split(df, test_size=0.30, stratify=df["label"], random_state=SEED)
    val, test = train_test_split(tmp, test_size=0.50, stratify=tmp["label"], random_state=SEED)
    return train.reset_index(drop=True), val.reset_index(drop=True), test.reset_index(drop=True)

def main():
    set_seed(SEED)
    df = pd.read_csv(DATA)
    df = df[df["label"].isin(LABELS)].dropna(subset=["text"]).reset_index(drop=True)
    train_df, val_df, test_df = split(df)
    print("split sizes:", len(train_df), len(val_df), len(test_df))
    print("test label dist:", test_df["label"].value_counts().to_dict())
    test_df.to_csv(os.path.join(ROOT, "data", "test_split.csv"), index=False)

    tok = AutoTokenizer.from_pretrained(MODEL)
    def encode(b):
        out = tok(b["text"], truncation=True, padding="max_length", max_length=256)
        out["labels"] = [L2I[l] for l in b["label"]]
        return out
    ds = {n: Dataset.from_pandas(d[["text", "label"]]).map(
              encode, batched=True, remove_columns=["text", "label"])
          for n, d in (("train", train_df), ("val", val_df), ("test", test_df))}

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL, num_labels=len(LABELS), id2label=I2L, label2id=L2I)

    def metrics(p):
        preds = np.argmax(p.predictions, axis=1)
        acc = accuracy_score(p.label_ids, preds)
        pr, rc, f1, _ = precision_recall_fscore_support(p.label_ids, preds, average="macro", zero_division=0)
        return {"accuracy": acc, "macro_f1": f1, "macro_precision": pr, "macro_recall": rc}

    args = TrainingArguments(
        output_dir=os.path.join(ROOT, "model_out"),
        num_train_epochs=3, learning_rate=2e-5,
        per_device_train_batch_size=16, per_device_eval_batch_size=32,
        eval_strategy="epoch", save_strategy="no", logging_steps=10,
        seed=SEED, report_to=[])
    trainer = Trainer(model=model, args=args, train_dataset=ds["train"],
                      eval_dataset=ds["val"], compute_metrics=metrics)
    trainer.train()

    # persist final model + tokenizer for predict.py / demo / deployed interface
    save_dir = os.path.join(ROOT, "model")
    trainer.save_model(save_dir)
    tok.save_pretrained(save_dir)
    print("saved model ->", save_dir)

    # ---- evaluate on locked test set ----
    pred = trainer.predict(ds["test"])
    logits = torch.tensor(pred.predictions)
    probs = torch.softmax(logits, dim=1).numpy()
    y_pred = probs.argmax(axis=1)
    y_true = pred.label_ids
    conf = probs.max(axis=1)

    acc = accuracy_score(y_true, y_pred)
    report = classification_report(y_true, y_pred, target_names=LABELS, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(LABELS))))
    print(f"\nFINE-TUNED test accuracy: {acc:.3f}")
    print(classification_report(y_true, y_pred, target_names=LABELS, zero_division=0))

    # confusion matrix png
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(LABELS))); ax.set_yticks(range(len(LABELS)))
    ax.set_xticklabels(LABELS, rotation=45, ha="right"); ax.set_yticklabels(LABELS)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title("Fine-tuned DistilBERT — confusion matrix")
    for i in range(len(LABELS)):
        for j in range(len(LABELS)):
            ax.text(j, i, cm[i, j], ha="center", va="center",
                    color="white" if cm[i, j] > cm.max()/2 else "black")
    fig.colorbar(im); fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "confusion_matrix.png"), dpi=120)
    print("wrote confusion_matrix.png")

    # per-example records (for wrong-prediction analysis + sample classifications)
    examples = []
    for t, yt, yp, c in zip(test_df["text"], y_true, y_pred, conf):
        examples.append({"text": t, "true": I2L[int(yt)], "pred": I2L[int(yp)],
                         "confidence": round(float(c), 4), "correct": bool(yt == yp)})

    out_path = os.path.join(ROOT, "evaluation_results.json")
    existing = {}
    if os.path.exists(out_path):
        existing = json.load(open(out_path))
    existing["labels"] = LABELS
    existing["test_set_size"] = len(test_df)
    existing["finetuned"] = {
        "model": MODEL,
        "hyperparameters": {"epochs": 3, "learning_rate": 2e-5, "batch_size": 16, "max_length": 256},
        "accuracy": acc,
        "per_class": {l: {"precision": report[l]["precision"], "recall": report[l]["recall"],
                          "f1": report[l]["f1-score"], "support": report[l]["support"]} for l in LABELS},
        "macro_f1": report["macro avg"]["f1-score"],
        "confusion_matrix": cm.tolist(),
        "examples": examples,
    }
    json.dump(existing, open(out_path, "w"), indent=2)
    print("wrote evaluation_results.json (finetuned section)")

if __name__ == "__main__":
    main()
