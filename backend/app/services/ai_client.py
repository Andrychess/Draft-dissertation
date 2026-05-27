from typing import Any, Dict, List, Optional

import httpx
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
    processing_time_ms: int = 0


class AIClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _client_instance(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def evaluate(self, request: EvaluateRequest) -> EvaluateResponse:
        try:
            client = await self._client_instance()
            response = await client.post(
                f"{self.base_url}/evaluate",
                json=request.model_dump(),
            )
            response.raise_for_status()
            return EvaluateResponse(**response.json())
        except Exception:
            return EvaluateResponse(
                request_id=request.request_id,
                score=0.0,
                normalized_score=0.0,
                confidence=0.0,
                verdict="review",
                explanation="AI service unavailable; manual review required.",
                weaknesses=[],
                strengths=[],
                details=None,
                model_version=None,
                processing_time_ms=0,
            )

    async def evaluate_many(self, requests: List[EvaluateRequest]) -> List[EvaluateResponse]:
        import asyncio

        return await asyncio.gather(*(self.evaluate(req) for req in requests))

    async def health(self) -> dict:
        client = await self._client_instance()
        response = await client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
