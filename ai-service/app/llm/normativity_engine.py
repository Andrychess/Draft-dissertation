"""Normativity evaluation with trained Parallel adapter head."""

from typing import List, Tuple

from app.llm.inference import run_llm_prompt
from app.llm.loader import get_model
from app.llm.relevance_engine import _parse_json_block
from app.ml.trained_models import get_normativity_model, predict_normativity


def evaluate_normativity(student_answer: str, temperature: float = 0.3) -> Tuple[float, float, str, List[dict], int]:
    ml_score, ml_conf, ml_errors = predict_normativity(student_answer)
    if get_normativity_model() is not None:
        comment = f"Оценка нормативности обученной моделью (Parallel). Ошибок: {len(ml_errors)}."
        return ml_score, ml_conf, comment, ml_errors, len(ml_errors)

    llm = get_model()
    if llm is None:
        return 0.7, 0.5, "Эвристическая оценка нормативности.", [], 0

    prompt = f"""<s>[INST] Проверь русский текст на орфографические, пунктуационные и грамматические ошибки.
Верни JSON:
{{"normativity_score": 0-100, "confidence": 0-1, "comment": "...", "errors": [{{"type":"orthography|punctuation|grammar","original":"...","suggestion":"..."}}]}}

Текст:
{student_answer}
[/INST]"""
    raw = run_llm_prompt(prompt, temperature)
    data = _parse_json_block(raw)
    score_raw = float(data.get("normativity_score", 70))
    score = max(0.0, min(1.0, score_raw / 100.0 if score_raw > 1 else score_raw))
    confidence = max(0.0, min(1.0, float(data.get("confidence", 0.7))))
    errors = data.get("errors") or []
    return round(score, 3), round(confidence, 3), str(data.get("comment", "")), errors, len(errors)
