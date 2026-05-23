"""Logic coherence evaluation with trained Houlsby adapter head."""

from typing import List, Tuple

from app.llm.inference import run_llm_prompt
from app.llm.loader import get_model
from app.llm.relevance_engine import _parse_json_block
from app.ml.trained_models import get_logic_model, predict_logic


def evaluate_logic(student_answer: str, temperature: float = 0.3) -> Tuple[float, float, str, List[dict], float]:
    ml_score, ml_conf, ml_errors = predict_logic(student_answer)
    if get_logic_model() is not None:
        coherence = round(ml_score, 2)
        comment = f"Оценка логики обученной моделью (Houlsby). coherence={coherence}."
        return ml_score, ml_conf, comment, ml_errors, coherence

    llm = get_model()
    if llm is None:
        return 0.75, 0.5, "Эвристическая оценка логики.", [], 0.75

    prompt = f"""<s>[INST] Оцени логическую связность и непротиворечивость текста.
Верни JSON:
{{"logic_score": 0-100, "confidence": 0-1, "comment": "...", "logic_errors": [{{"type":"contradiction|gap|tautology","description":"..."}}], "coherence_ratio": 0-1}}

Текст:
{student_answer}
[/INST]"""
    raw = run_llm_prompt(prompt, temperature)
    data = _parse_json_block(raw)
    score_raw = float(data.get("logic_score", 70))
    score = max(0.0, min(1.0, score_raw / 100.0 if score_raw > 1 else score_raw))
    confidence = max(0.0, min(1.0, float(data.get("confidence", 0.7))))
    errors = data.get("logic_errors") or []
    coherence = float(data.get("coherence_ratio", score))
    return round(score, 3), round(confidence, 3), str(data.get("comment", "")), errors, coherence
