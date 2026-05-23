from app.adapters.base import AdapterResult, BaseAdapter
from app.llm.logic_engine import evaluate_logic


class LogicAdapter(BaseAdapter):
    """Houlsby adapter — layers 1, 2, 11, 12."""

    name = "logic"
    architecture = "houlsby"
    layers = [1, 2, 11, 12]

    def evaluate(self, student_answer: str, temperature: float = 0.3) -> AdapterResult:
        score, confidence, comment, errors, coherence = evaluate_logic(student_answer, temperature)
        return AdapterResult(
            score=score,
            confidence=confidence,
            comment=comment,
            extra={
                "logic_score": round(score * 100, 2),
                "logic_percent": round(score * 100, 2),
                "logic_errors": errors,
                "coherence_ratio": coherence,
            },
        )

    def predict(self, input_text: str, temperature: float = 0.3) -> AdapterResult:
        student = input_text.split("[SEP]")[-1].strip() if "[SEP]" in input_text else input_text
        return self.evaluate(student, temperature)
