from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AdapterResult:
    score: float
    confidence: float
    comment: str
    extra: Dict[str, Any] = field(default_factory=dict)


class BaseAdapter(ABC):
    name: str = "base"
    architecture: str = "base"
    layers: List[int] = []

    @abstractmethod
    def predict(self, input_text: str, temperature: float = 0.3) -> AdapterResult:
        pass
