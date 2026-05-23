"""Load sklearn adapter heads trained in training/."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

ADAPTER_DIR = Path(__file__).resolve().parents[2] / "models" / "adapters"

_normativity_model = None
_logic_model = None


def _load_joblib(name: str):
    path = ADAPTER_DIR / f"{name}.joblib"
    if not path.exists():
        return None
    try:
        import joblib

        return joblib.load(path)
    except Exception as exc:
        logger.warning("Failed to load %s: %s", path, exc)
        return None


def get_normativity_model():
    global _normativity_model
    if _normativity_model is None:
        _normativity_model = _load_joblib("normativity")
    return _normativity_model


def get_logic_model():
    global _logic_model
    if _logic_model is None:
        _logic_model = _load_joblib("logic")
    return _logic_model


def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?…])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def load_template_topics(template_id: int) -> Optional[List[str]]:
    path = ADAPTER_DIR / "relevance" / f"template_{template_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("topics") or []
    except Exception:
        return None


def predict_normativity(text: str) -> Tuple[float, float, List[dict]]:
    model = get_normativity_model()
    if model is None:
        return 0.0, 0.0, []

    sentences = split_sentences(text) or [text]
    probs = []
    errors: List[dict] = []
    for sent in sentences:
        if len(sent) < 4:
            continue
        proba = float(model.predict_proba([sent])[0][1])
        probs.append(proba)
        if proba < 0.5:
            errors.append(
                {
                    "type": "grammar",
                    "original": sent[:120],
                    "description": "Вероятная грамматическая/синтаксическая ошибка (модель нормативности).",
                    "severity": 2 if proba < 0.35 else 1,
                }
            )

    if not probs:
        return 0.5, 0.5, errors

    score = sum(probs) / len(probs)
    confidence = 0.55 + 0.4 * min(1.0, len(probs) / 3)
    return round(score, 3), round(confidence, 3), errors[:5]


def predict_logic(text: str) -> Tuple[float, float, List[dict]]:
    model = get_logic_model()
    if model is None:
        return 0.0, 0.0, []

    sentences = split_sentences(text)
    if len(sentences) < 2:
        return 0.85, 0.6, []

    pair_scores = []
    logic_errors: List[dict] = []
    for i in range(len(sentences) - 1):
        s1, s2 = sentences[i], sentences[i + 1]
        combined = f"{s1} {s2}"
        issue_proba = float(model.predict_proba([combined])[0][1])
        pair_scores.append(1.0 - issue_proba)
        if issue_proba >= 0.55:
            logic_errors.append(
                {
                    "type": "contradiction" if issue_proba >= 0.7 else "gap",
                    "description": f"Возможная логическая несогласованность между фрагментами {i + 1} и {i + 2}.",
                    "severity": 3 if issue_proba >= 0.7 else 2,
                }
            )

    score = sum(pair_scores) / len(pair_scores)
    confidence = 0.5 + 0.45 * min(1.0, len(pair_scores) / 4)
    return round(score, 3), round(confidence, 3), logic_errors[:5]
