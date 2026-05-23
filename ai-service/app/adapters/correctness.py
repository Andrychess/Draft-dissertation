from app.adapters.base import AdapterResult, BaseAdapter
from app.llm.inference import score_dimension


class CorrectnessAdapter(BaseAdapter):
    """Houlsby adapter — layers 11-12."""

    name = "correctness"
    architecture = "houlsby"
    layers = [11, 12]

    def predict(self, input_text: str, temperature: float = 0.3) -> AdapterResult:
        score, confidence, comment = score_dimension(input_text, "correctness", temperature)
        return AdapterResult(score=score, confidence=confidence, comment=comment)
