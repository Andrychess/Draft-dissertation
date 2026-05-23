from typing import Optional

from app.adapters.base import AdapterResult, BaseAdapter
from app.llm.relevance_engine import evaluate_relevance


class RelevanceAdapter(BaseAdapter):
    """Pfeiffer-style relevance head — layers 9-12 (dissertation §2.2.4.2)."""

    name = "relevance"
    architecture = "pfeiffer"
    layers = [9, 10, 11, 12]

    def evaluate(
        self,
        question: str,
        student_answer: str,
        lecture_material: str = "",
        temperature: float = 0.3,
        template_id: Optional[int] = None,
    ) -> AdapterResult:
        score, confidence, comment, mismatches, covered = evaluate_relevance(
            question=question,
            student_answer=student_answer,
            lecture_material=lecture_material,
            temperature=temperature,
            template_id=template_id,
        )
        return AdapterResult(
            score=score,
            confidence=confidence,
            comment=comment,
            extra={
                "relevance_score": round(score * 100, 2),
                "relevance_percent": round(score * 100, 2),
                "topic_mismatches": mismatches,
                "covered_topics": covered,
            },
        )

    def predict(self, input_text: str, temperature: float = 0.3) -> AdapterResult:
        """Legacy [CLS] Q [SEP] ref [SEP] S format — uses only Q and S."""
        question = ""
        student = input_text
        if "[SEP]" in input_text:
            parts = input_text.split("[SEP]")
            if len(parts) >= 3:
                question = parts[0].replace("[CLS]", "").strip()
                student = parts[-1].strip()
            elif len(parts) == 2:
                question = parts[0].replace("[CLS]", "").strip()
                student = parts[1].strip()
        return self.evaluate(question, student, "", temperature)
