"""Semantic relevance evaluation: question Q, student answer S, optional lecture L."""

import json
import logging
import re
from typing import List, Optional, Tuple

from app.llm.inference import run_llm_prompt
from app.llm.loader import get_model
from app.ml.trained_models import load_template_topics

logger = logging.getLogger(__name__)

_RU_STOPWORDS = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все",
    "она", "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за", "бы", "по",
    "только", "ее", "мне", "было", "вот", "от", "меня", "еще", "нет", "о", "из",
    "ему", "теперь", "когда", "даже", "ну", "ли", "если", "уже", "или", "ни", "быть",
    "был", "него", "до", "вас", "нибудь", "оп", "для", "при", "это", "этот", "эта",
    "эти", "такой", "такая", "такие", "который", "которая", "которые", "где", "какой",
    "какая", "какие", "чем", "чтобы", "также", "может", "можно", "является", "являются",
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "must", "shall", "can", "need", "dare", "ought", "used", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during", "before",
    "after", "above", "below", "between", "under", "again", "further", "then", "once",
}


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9_-]+", text.lower())
    return [w for w in words if len(w) > 2 and w not in _RU_STOPWORDS]


def _extract_topics(text: str, limit: int = 12) -> List[str]:
    if not text.strip():
        return []
    tokens = _tokenize(text)
    if not tokens:
        return []
    freq: dict[str, int] = {}
    for token in tokens:
        freq[token] = freq.get(token, 0) + 1
    ranked = sorted(freq.items(), key=lambda item: (-item[1], -len(item[0])))
    return [word for word, _ in ranked[:limit]]


def _truncate(text: str, max_chars: int = 2500) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _parse_json_block(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {}


def _heuristic_relevance(
    question: str,
    student_answer: str,
    lecture_material: str = "",
    preset_topics: Optional[List[str]] = None,
) -> Tuple[float, float, str, List[str], List[str]]:
    """Fallback: overlap with question and lecture topics (not reference answer)."""
    if not student_answer.strip():
        return 0.0, 0.2, "Пустой ответ.", ["Ответ не содержит текста"], []

    question_topics = _extract_topics(question, limit=8)
    lecture_topics = preset_topics or (
        _extract_topics(lecture_material, limit=12) if lecture_material else []
    )
    expected = list(dict.fromkeys(question_topics + lecture_topics))
    student_tokens = set(_tokenize(student_answer))

    covered = [topic for topic in expected if topic in student_tokens]
    mismatches: List[str] = []
    for topic in expected:
        if topic not in student_tokens:
            label = "понятие" if len(topic) > 5 else "термин"
            mismatches.append(f"В ответе не раскрыт {label} «{topic}»")

    if not expected:
        overlap_q = len(set(_tokenize(question)) & student_tokens)
        base = min(1.0, overlap_q / max(len(_tokenize(question)), 1))
    else:
        base = len(covered) / len(expected)

    if lecture_material and lecture_topics:
        lecture_hits = sum(1 for t in lecture_topics if t in student_tokens)
        lecture_ratio = lecture_hits / max(len(lecture_topics), 1)
        base = 0.4 * base + 0.6 * lecture_ratio

    if student_answer.strip() and base < 0.15 and len(student_tokens) >= 5:
        base = min(0.35, base + 0.15)

    confidence = 0.45 + 0.35 * min(1.0, len(student_tokens) / 20)
    score = round(max(0.0, min(1.0, base)), 3)
    comment = (
        f"Эвристическая оценка релевантности: покрыто {len(covered)} из {len(expected) or 1} тем."
    )
    return score, round(confidence, 3), comment, mismatches[:5], covered


def _llm_relevance(
    question: str,
    student_answer: str,
    lecture_material: str,
    temperature: float,
) -> Tuple[float, float, str, List[str], List[str]]:
    lecture_block = ""
    if lecture_material.strip():
        lecture_block = f"\nЛекционный материал (ключевые темы):\n{_truncate(lecture_material)}\n"

    prompt = f"""<s>[INST] Ты — эксперт по оценке письменных ответов студентов.
Оцени СЕМАНТИЧЕСКУЮ РЕЛЕВАНТНОСТЬ ответа студента теме вопроса.
Не сравнивай с эталоном — только соответствие вопросу и (если есть) лекции.

Вопрос:
{question.strip()}

Ответ студента:
{student_answer.strip()}
{lecture_block}
Верни ТОЛЬКО JSON:
{{
  "relevance_score": 0-100,
  "confidence": 0-1,
  "comment": "краткое обоснование",
  "topic_mismatches": ["тематические несоответствия"],
  "covered_topics": ["раскрытые темы/понятия"]
}}
[/INST]"""

    raw = run_llm_prompt(prompt, temperature)
    data = _parse_json_block(raw)
    if not data:
        logger.warning("Relevance LLM returned unpinned JSON, falling back to heuristic")
        return _heuristic_relevance(question, student_answer, lecture_material)

    score_raw = float(data.get("relevance_score", data.get("relevance_percent", 50)))
    score = max(0.0, min(1.0, score_raw / 100.0 if score_raw > 1 else score_raw))
    confidence = max(0.0, min(1.0, float(data.get("confidence", 0.7))))
    comment = str(data.get("comment", "LLM relevance evaluation."))
    mismatches = [str(x) for x in data.get("topic_mismatches", []) if x]
    covered = [str(x) for x in data.get("covered_topics", []) if x]
    return round(score, 3), round(confidence, 3), comment, mismatches, covered


def evaluate_relevance(
    question: str,
    student_answer: str,
    lecture_material: str = "",
    temperature: float = 0.3,
    template_id: Optional[int] = None,
) -> Tuple[float, float, str, List[str], List[str]]:
    """R = f(Q, S, L) per dissertation §2.2.4.2."""
    lecture_topics: List[str] = []
    if template_id is not None:
        lecture_topics = load_template_topics(template_id) or []

    if lecture_topics and not lecture_material.strip():
        lecture_material = ", ".join(lecture_topics)

    if get_model() is None:
        return _heuristic_relevance(
            question, student_answer, lecture_material, preset_topics=lecture_topics
        )
    return _llm_relevance(question, student_answer, lecture_material, temperature)
