import logging
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_llm = None


def load_model():
    global _llm
    if _llm is not None:
        return _llm

    model_path = Path(settings.model_path)
    if not model_path.exists():
        logger.warning("GGUF model not found at %s — using heuristic evaluation", model_path)
        _llm = None
        return _llm

    try:
        from llama_cpp import Llama

        _llm = Llama(
            model_path=str(model_path),
            n_ctx=settings.n_ctx,
            n_gpu_layers=settings.n_gpu_layers,
            verbose=False,
        )
        logger.info("Loaded Mistral 7B from %s", model_path)
    except Exception as exc:
        logger.warning("Failed to load llama-cpp model: %s", exc)
        _llm = None
    return _llm


def get_model():
    return _llm or load_model()
