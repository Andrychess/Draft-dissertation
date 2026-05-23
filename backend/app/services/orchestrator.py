import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app import crud
from app.models import AICheckResult, Verdict
from app.services.ai_client import AIClient, EvaluateRequest, EvaluationConfig, EvaluationWeights
from app.services.lecture_text import load_lecture_text


class Orchestrator:
    def __init__(self, ai_client: AIClient, db_session: Session):
        self.ai_client = ai_client
        self.db = db_session

    async def process_submission(self, sheet_id: int) -> List[AICheckResult]:
        rows = crud.get_sheet_rows(self.db, sheet_id)
        if not rows:
            return []

        session = crud.get_session(self.db, rows[0].session_id)
        context_materials = None
        tpl = session.template if session else None
        if session and tpl and tpl.material_id:
            from app.models import LectureMaterial

            material = self.db.get(LectureMaterial, tpl.material_id)
            if material:
                lecture_text = load_lecture_text(material.file_path)
                if lecture_text:
                    context_materials = [lecture_text]

        settings = crud.get_system_settings(self.db)
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

        results: List[AICheckResult] = []
        for row in rows:
            if not row.student_answer or not row.submitted_at:
                continue

            request = EvaluateRequest(
                request_id=str(uuid.uuid4()),
                question=row.question.text,
                reference_answer=row.question.correct_answer,
                student_answer=row.student_answer.answer_text,
                max_score=row.question.max_score,
                context_materials=context_materials,
                template_id=tpl.id if tpl else None,
                config=config,
            )
            ai_response = await self.ai_client.evaluate(request)

            verdict = Verdict(ai_response.verdict)
            result = crud.create_ai_check_result(
                self.db,
                sheet_id=row.sheet_id,
                question_id=row.question_id,
                score=ai_response.score,
                confidence=ai_response.confidence,
                verdict=verdict,
                explanation=ai_response.explanation,
                weaknesses=ai_response.weaknesses,
                strengths=ai_response.strengths,
                details=ai_response.details,
                model_version=ai_response.model_version,
            )
            results.append(result)

        return results
