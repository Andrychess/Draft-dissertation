from app.adapters.base import AdapterResult, BaseAdapter
from app.llm.normativity_engine import evaluate_normativity


class NormativityAdapter(BaseAdapter):
    """Parallel adapter — layers 7-12."""

    name = "normativity"
    architecture = "parallel"
    layers = [7, 8, 9, 10, 11, 12]

    def evaluate(self, student_answer: str, temperature: float = 0.3) -> AdapterResult:
        score, confidence, comment, errors, error_count = evaluate_normativity(
            student_answer, temperature
        )
        return AdapterResult(
            score=score,
            confidence=confidence,
            comment=comment,
            extra={
                "normativity_score": round(score * 100, 2),
                "normativity_percent": round(score * 100, 2),
                "errors": errors,
                "error_count": error_count,
            },
        )

    def predict(self, input_text: str, temperature: float = 0.3) -> AdapterResult:
        student = input_text.split("[SEP]")[-1].strip() if "[SEP]" in input_text else input_text
        return self.evaluate(student, temperature)
