import logging
import time
from pathlib import Path

from fastapi import APIRouter

from app.adapters.correctness import CorrectnessAdapter
from app.adapters.logic import LogicAdapter
from app.adapters.normativity import NormativityAdapter
from app.adapters.relevance import RelevanceAdapter
from app.config import settings
from app.models import EvaluateRequest, EvaluateResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["evaluate"])

relevance_adapter = RelevanceAdapter()
correctness_adapter = CorrectnessAdapter()
normativity_adapter = NormativityAdapter()
logic_adapter = LogicAdapter()

DEFAULT_WEIGHTS = {
    "relevance": 0.25,
    "correctness": 0.35,
    "normativity": 0.20,
    "logic": 0.20,
}


def _model_version() -> str:
    path = Path(settings.model_path)
    if path.exists():
        return path.name
    return "heuristic-fallback"


def _join_context_materials(materials: list[str] | None) -> str:
    if not materials:
        return ""
    return "\n\n".join(part.strip() for part in materials if part and part.strip())


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    start_time = time.time()
    cfg = request.config
    passing_threshold = cfg.passing_threshold if cfg else settings.passing_threshold
    confidence_threshold = cfg.confidence_threshold if cfg else settings.confidence_threshold
    temperature = cfg.temperature if cfg else 0.3

    weights = DEFAULT_WEIGHTS.copy()
    if cfg and cfg.weights:
        weights = {
            "relevance": cfg.weights.relevance,
            "correctness": cfg.weights.correctness,
            "normativity": cfg.weights.normativity,
            "logic": cfg.weights.logic,
        }

    input_text = (
        f"[CLS] {request.question} [SEP] {request.reference_answer} "
        f"[SEP] {request.student_answer}"
    )

    rel = relevance_adapter.evaluate(
        question=request.question,
        student_answer=request.student_answer,
        lecture_material=_join_context_materials(request.context_materials),
        temperature=temperature,
        template_id=request.template_id,
    )
    cor = correctness_adapter.predict(input_text, temperature)
    norm = normativity_adapter.evaluate(request.student_answer, temperature)
    log = logic_adapter.evaluate(request.student_answer, temperature)

    total_normalized = (
        rel.score * weights["relevance"]
        + cor.score * weights["correctness"]
        + norm.score * weights["normativity"]
        + log.score * weights["logic"]
    )
    confidence = min(rel.confidence, cor.confidence, norm.confidence, log.confidence)
    score = round(total_normalized * request.max_score, 2)
    normalized_score = round(total_normalized, 4)

    if confidence < confidence_threshold:
        verdict = "review"
    elif total_normalized >= passing_threshold:
        verdict = "passed"
    else:
        verdict = "failed"

    weaknesses = []
    strengths = []
    adapter_map = {
        "relevance": rel,
        "correctness": cor,
        "normativity": norm,
        "logic": log,
    }
    for name, result in adapter_map.items():
        if result.score < 0.5:
            weaknesses.append(f"{name}: {result.comment or 'low score'}")
        elif result.score >= 0.7:
            strengths.append(f"{name}: {result.comment or 'good'}")
    for mismatch in rel.extra.get("topic_mismatches", []):
        weaknesses.append(f"relevance: {mismatch}")

    details = {}
    for name, result in adapter_map.items():
        block = {
            "score": round(result.score * 100, 2),
            "score_normalized": round(result.score, 4),
            "confidence": round(result.confidence, 4),
            "comment": result.comment,
            "architecture": getattr(
                {
                    "relevance": relevance_adapter,
                    "correctness": correctness_adapter,
                    "normativity": normativity_adapter,
                    "logic": logic_adapter,
                }[name],
                "architecture",
                "",
            ),
        }
        if result.extra:
            block.update(result.extra)
        details[name] = block
    details["weights"] = weights

    explanation = (
        f"Aggregated score {normalized_score:.2f} (confidence {confidence:.2f}). "
        f"relevance={rel.score:.2f}, correctness={cor.score:.2f}, "
        f"normativity={norm.score:.2f}, logic={log.score:.2f}."
    )

    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info("evaluate %s completed in %dms verdict=%s", request.request_id, elapsed_ms, verdict)

    return EvaluateResponse(
        request_id=request.request_id,
        score=score,
        normalized_score=normalized_score,
        confidence=confidence,
        verdict=verdict,
        explanation=explanation,
        weaknesses=weaknesses,
        strengths=strengths,
        details=details,
        model_version=_model_version(),
        raw_response=None,
        processing_time_ms=elapsed_ms,
    )


@router.get("/health")
def health():
    from app.llm.loader import get_model
    from app.ml.trained_models import ADAPTER_DIR, get_logic_model, get_normativity_model

    model = get_model()
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_version": _model_version(),
        "adapters": ["relevance", "correctness", "normativity", "logic"],
        "trained_heads": {
            "normativity": (ADAPTER_DIR / "normativity.joblib").exists(),
            "logic": (ADAPTER_DIR / "logic.joblib").exists(),
        },
        "ml_loaded": {
            "normativity": get_normativity_model() is not None,
            "logic": get_logic_model() is not None,
        },
    }
