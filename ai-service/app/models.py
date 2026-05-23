from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvaluationWeights(BaseModel):
    relevance: float = 0.25
    correctness: float = 0.35
    normativity: float = 0.20
    logic: float = 0.20


class EvaluationConfig(BaseModel):
    passing_threshold: float = 0.6
    confidence_threshold: float = 0.7
    temperature: float = 0.3
    weights: Optional[EvaluationWeights] = None


class EvaluateRequest(BaseModel):
    request_id: str
    question: str
    reference_answer: str
    student_answer: str
    max_score: float = 10.0
    context_materials: Optional[List[str]] = None
    template_id: Optional[int] = None
    config: Optional[EvaluationConfig] = None


class EvaluateResponse(BaseModel):
    request_id: str
    score: float
    normalized_score: float
    confidence: float
    verdict: str
    explanation: str
    weaknesses: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    details: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None
    raw_response: Optional[str] = None
    processing_time_ms: int
