import uuid
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from app import crud
from app.models import AICheckResult, Verdict
from app.services.ai_client import AIClient, EvaluateRequest, EvaluationConfig, EvaluationWeights
from app.services.cache import get_cached_lecture_text, get_cached_system_settings
from app.services.lecture_text import load_lecture_text

_ROOT = Path(__file__).resolve().parents[3]
_RELEVANCE_TOPICS_DIR = _ROOT / "ai-service" / "models" / "adapters" / "relevance"


class Orchestrator:
    def __init__(self, ai_client: AIClient, db_session: Session):
        self.ai_client = ai_client
        self.db = db_session

    def _lecture_context(self, tpl) -> Optional[list[str]]:
        if not tpl or not tpl.material_id:
            return None
        from app.models import LectureMaterial

        material = self.db.get(LectureMaterial, tpl.material_id)
        if not material:
            return None
        if (_RELEVANCE_TOPICS_DIR / f"template_{tpl.id}.json").exists():
            return None
        lecture_text = get_cached_lecture_text(material.file_path, load_lecture_text)
        return [lecture_text] if lecture_text else None

    async def process_submission(self, sheet_id: int) -> List[AICheckResult]:
        rows = crud.get_sheet_rows(self.db, sheet_id)
        if not rows:
            return []

        session = crud.get_session(self.db, rows[0].session_id)
        tpl = session.template if session else None
        context_materials = self._lecture_context(tpl)

        settings = get_cached_system_settings(self.db, crud.get_system_settings)
        passing = float(settings.get("passing_threshold", "0.6"))
        confidence = float(settings.get("confidence_threshold", "0.7"))

        weights = None
        if tpl:
            weights = EvaluationWeights(
                relevance=tpl.weight_relevance,
                correctness=tpl.weight_correctness,
                normativity=tpl.weight_normativity,
                logic=tpl.weight_logic,
            )

        config = EvaluationConfig(
            passing_threshold=passing,
            confidence_threshold=confidence,
            weights=weights,
        )

        pending_rows = [row for row in rows if row.student_answer and row.submitted_at]
        if not pending_rows:
            return []

        requests = [
            EvaluateRequest(
                request_id=str(uuid.uuid4()),
                question=row.question.text,
                reference_answer=row.question.correct_answer,
                student_answer=row.student_answer.answer_text,
                max_score=row.question.max_score,
                context_materials=context_materials,
                template_id=tpl.id if tpl else None,
                config=config,
            )
            for row in pending_rows
        ]

        ai_responses = await self.ai_client.evaluate_many(requests)

        bulk: list[dict] = []
        for row, ai_response in zip(pending_rows, ai_responses):
            bulk.append(
                {
                    "sheet_id": row.sheet_id,
                    "question_id": row.question_id,
                    "score": ai_response.score,
                    "confidence": ai_response.confidence,
                    "verdict": Verdict(ai_response.verdict),
                    "explanation": ai_response.explanation,
                    "weaknesses": ai_response.weaknesses,
                    "strengths": ai_response.strengths,
                    "details": ai_response.details,
                    "model_version": ai_response.model_version,
                }
            )

        return crud.create_ai_check_results_bulk(self.db, bulk)
