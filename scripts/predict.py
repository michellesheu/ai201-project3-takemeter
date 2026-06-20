#!/usr/bin/env python3
"""Classify new r/nba posts with the fine-tuned TakeMeter model.

Loads the saved model in ./model and prints the predicted label + confidence.

Usage:
  python3 scripts/predict.py "LeBron is washed, no debate"
  python3 scripts/predict.py            # then type/paste posts, one per line
"""
import os, sys
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

HERE = os.path.dirname(__file__)
MODEL_DIR = os.path.join(HERE, "..", "model")

def load():
    tok = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()
    return tok, model

def classify(text, tok, model):
    enc = tok(text, truncation=True, padding=True, max_length=256, return_tensors="pt")
    with torch.no_grad():
        probs = torch.softmax(model(**enc).logits, dim=1)[0]
    idx = int(probs.argmax())
    return model.config.id2label[idx], float(probs[idx])

def main():
    tok, model = load()
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        label, conf = classify(text, tok, model)
        print(f"{label}\t{conf:.1%}\t{text}")
        return
    print("Enter a post (Ctrl-D to quit):")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        label, conf = classify(line, tok, model)
        print(f"  -> {label}  ({conf:.1%})")

if __name__ == "__main__":
    main()
