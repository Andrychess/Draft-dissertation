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
_topics_cache: dict[int, tuple[float, List[str]]] = {}


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
        mtime = path.stat().st_mtime
        cached = _topics_cache.get(template_id)
        if cached and cached[0] == mtime:
            return cached[1]
        data = json.loads(path.read_text(encoding="utf-8"))
        topics = data.get("topics") or []
        _topics_cache[template_id] = (mtime, topics)
        return topics
    except Exception:
        return None


def predict_normativity(text: str) -> Tuple[float, float, List[dict]]:
    model = get_normativity_model()
    if model is None:
        return 0.0, 0.0, []

    sentences = [s for s in split_sentences(text) or [text] if len(s) >= 4]
    if not sentences:
        return 0.5, 0.5, []

    probas = model.predict_proba(sentences)[:, 1]
    errors: List[dict] = []
    for sent, proba in zip(sentences, probas):
        proba = float(proba)
        if proba < 0.5:
            errors.append(
                {
                    "type": "grammar",
                    "original": sent[:120],
                    "description": "Вероятная грамматическая/синтаксическая ошибка (модель нормативности).",
                    "severity": 2 if proba < 0.35 else 1,
                }
            )

    score = float(probas.mean())
    confidence = 0.55 + 0.4 * min(1.0, len(sentences) / 3)
    return round(score, 3), round(confidence, 3), errors[:5]


def predict_logic(text: str) -> Tuple[float, float, List[dict]]:
    model = get_logic_model()
    if model is None:
        return 0.0, 0.0, []

    sentences = split_sentences(text)
    if len(sentences) < 2:
        return 0.85, 0.6, []

    pairs = [f"{sentences[i]} {sentences[i + 1]}" for i in range(len(sentences) - 1)]
    issue_probas = model.predict_proba(pairs)[:, 1]
    pair_scores = [1.0 - float(p) for p in issue_probas]
    logic_errors: List[dict] = []
    for i, issue_proba in enumerate(issue_probas):
        issue_proba = float(issue_proba)
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
