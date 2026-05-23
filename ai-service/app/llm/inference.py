import json
import logging
import re
from typing import Optional, Tuple

from app.config import settings
from app.llm.loader import get_model

logger = logging.getLogger(__name__)


def _heuristic_score(text: str, dimension: str) -> Tuple[float, float]:
    """Fallback when GGUF model is unavailable."""
    student = text.split("[SEP]")[-1].strip() if "[SEP]" in text else text
    ref = text.split("[SEP]")[1].strip() if text.count("[SEP]") >= 2 else ""
    if not student.strip():
        return 0.0, 0.2
    overlap = len(set(student.lower().split()) & set(ref.lower().split()))
    base = min(1.0, overlap / max(len(ref.split()), 1))
    weights = {"relevance": 0.9, "correctness": 1.0, "normativity": 0.85, "logic": 0.8}
    score = base * weights.get(dimension, 0.8)
    confidence = 0.5 + 0.3 * min(1.0, len(student) / 50)
    return round(score, 3), round(confidence, 3)


def _parse_json_block(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {}


def run_llm_prompt(prompt: str, temperature: float = 0.3) -> str:
    llm = get_model()
    if llm is None:
        return ""
    output = llm(
        prompt,
        max_tokens=512,
        temperature=temperature,
        stop=["</s>", "[/INST]"],
    )
    return output["choices"][0]["text"]


def score_dimension(input_text: str, dimension: str, temperature: float) -> Tuple[float, float, str]:
    llm = get_model()
    if llm is None:
        score, conf = _heuristic_score(input_text, dimension)
        return score, conf, f"Heuristic {dimension} evaluation."

    prompt = f"""<s>[INST] You are an academic assessor. Evaluate the student answer on "{dimension}".
Return JSON only: {{"score": 0-1, "confidence": 0-1, "comment": "brief"}}

Input:
{input_text}
[/INST]"""
    raw = run_llm_prompt(prompt, temperature)
    data = _parse_json_block(raw)
    score = float(data.get("score", 0.5))
    confidence = float(data.get("confidence", 0.6))
    comment = str(data.get("comment", ""))
    return max(0.0, min(1.0, score)), max(0.0, min(1.0, confidence)), comment
