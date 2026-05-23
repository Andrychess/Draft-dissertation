"""Train logic adapter head (Houlsby) on LiDiRus pairs."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "training" / "processed" / "logic.jsonl"
MODEL_DIR = ROOT / "ai-service" / "models" / "adapters"
REPORT_DIR = ROOT / "training" / "reports"


def load_rows() -> pd.DataFrame:
    rows = [json.loads(line) for line in PROCESSED.open(encoding="utf-8")]
    return pd.DataFrame(rows)


def main() -> None:
    if not PROCESSED.exists():
        raise SystemExit("Run prepare_datasets.py first")

    df = load_rows()
    df = df[df["combined"].astype(str).str.len() > 10].copy()
    X = df["combined"].astype(str)
    y = df["label"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=30000, min_df=2)),
            (
                "clf",
                LogisticRegression(max_iter=300, class_weight="balanced", n_jobs=-1),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)
    pred = pipeline.predict(X_test)

    metrics = {
        "adapter": "logic",
        "architecture": "houlsby",
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "accuracy": float(accuracy_score(y_test, pred)),
        "f1": float(f1_score(y_test, pred)),
        "report": classification_report(y_test, pred, output_dict=True),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_DIR / "logic.joblib")

    meta = {
        **metrics,
        "datasets": ["LiDiRus"],
        "description": "Logical consistency detector for sentence pairs (contradiction / entailment)",
    }
    (MODEL_DIR / "logic.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (REPORT_DIR / "logic_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("Logic model saved.")
    print(f"  accuracy={metrics['accuracy']:.4f}  f1={metrics['f1']:.4f}")


if __name__ == "__main__":
    main()
