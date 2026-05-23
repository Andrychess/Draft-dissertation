"""Prepare unified JSONL datasets from dataset/ for adapter training."""

from __future__ import annotations

import csv
import json
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "dataset"
OUT_DIR = ROOT / "training" / "processed"


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def prepare_normativity() -> Path:
    rows: list[dict] = []

    gec_path = DATASET_DIR / "russian_gec_dataset_final (1).csv"
    if gec_path.exists():
        with gec_path.open(encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for item in reader:
                incorrect = (item.get("incorrect") or "").strip()
                correct = (item.get("correct") or "").strip()
                if not incorrect or not correct:
                    continue
                sim = _ratio(incorrect, correct)
                score = round(max(0.0, min(100.0, sim * 100)), 2)
                rows.append(
                    {
                        "text": incorrect,
                        "label": 0,
                        "normativity_score": score,
                        "reference_correct": correct,
                        "source": "russian_gec",
                        "error_type": "mixed",
                    }
                )
                rows.append(
                    {
                        "text": correct,
                        "label": 1,
                        "normativity_score": 100.0,
                        "reference_correct": correct,
                        "source": "russian_gec",
                        "error_type": "none",
                    }
                )

    lor_path = DATASET_DIR / "LORuGEC.xlsx"
    if lor_path.exists():
        df = pd.read_excel(lor_path)
        for _, item in df.iterrows():
            initial = str(item.get("Initial sentence", "") or "").strip()
            correct = str(item.get("Correct sentence", "") or "").strip()
            rule = str(item.get("The rule", "") or "").strip()
            if not initial or not correct or initial == "nan":
                continue
            sim = _ratio(initial, correct)
            score = round(max(0.0, min(100.0, sim * 100)), 2)
            rows.append(
                {
                    "text": initial,
                    "label": 0,
                    "normativity_score": score,
                    "reference_correct": correct,
                    "source": "lorugec",
                    "error_type": rule or "grammar",
                }
            )
            rows.append(
                {
                    "text": correct,
                    "label": 1,
                    "normativity_score": 100.0,
                    "reference_correct": correct,
                    "source": "lorugec",
                    "error_type": "none",
                }
            )

    in_domain = DATASET_DIR / "in_domain_train.csv"
    if in_domain.exists():
        with in_domain.open(encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for item in reader:
                sentence = (item.get("sentence") or "").strip()
                if not sentence:
                    continue
                acceptable = int(item.get("acceptable") or 0)
                err = item.get("error_type") or "0"
                rows.append(
                    {
                        "text": sentence,
                        "label": acceptable,
                        "normativity_score": 100.0 if acceptable else 45.0,
                        "reference_correct": sentence if acceptable else "",
                        "source": "in_domain",
                        "error_type": str(err),
                    }
                )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "normativity.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out


def prepare_logic() -> Path:
    rows: list[dict] = []
    lid_path = DATASET_DIR / "LiDiRus.jsonl"
    if lid_path.exists():
        with lid_path.open(encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                s1 = (item.get("sentence1") or "").strip()
                s2 = (item.get("sentence2") or "").strip()
                label = item.get("label") or "entailment"
                logic = item.get("logic") or ""
                is_issue = 1 if label == "not_entailment" else 0
                combined = f"{s1} {s2}".strip()
                rows.append(
                    {
                        "sentence1": s1,
                        "sentence2": s2,
                        "combined": combined,
                        "label": is_issue,
                        "logic_type": logic,
                        "source": "lidirus",
                    }
                )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "logic.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out


def main() -> None:
    n_path = prepare_normativity()
    l_path = prepare_logic()
    n_count = sum(1 for _ in n_path.open(encoding="utf-8"))
    l_count = sum(1 for _ in l_path.open(encoding="utf-8"))
    print(f"normativity -> {n_path} ({n_count} rows)")
    print(f"logic       -> {l_path} ({l_count} rows)")


if __name__ == "__main__":
    main()
