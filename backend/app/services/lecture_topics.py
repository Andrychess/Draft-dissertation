"""Build per-template thematic vector T after lecture upload."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.services.lecture_text import load_lecture_text

ROOT = Path(__file__).resolve().parents[3]
RELEVANCE_DIR = ROOT / "ai-service" / "models" / "adapters" / "relevance"

_STOP = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "как", "а", "то", "все", "это",
    "для", "по", "из", "от", "при", "или", "же", "бы", "у", "о", "об", "до", "за",
}


def extract_topics(text: str, limit: int = 40) -> list[str]:
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9_-]+", text.lower())
    tokens = [w for w in words if len(w) > 3 and w not in _STOP]
    freq: dict[str, int] = {}
    for token in tokens:
        freq[token] = freq.get(token, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], -len(x[0])))
    return [w for w, _ in ranked[:limit]]


def process_lecture_for_template(template_id: int, file_path: str) -> dict:
    text = load_lecture_text(file_path)
    topics = extract_topics(text) if text else []
    payload = {
        "template_id": template_id,
        "topics": topics,
        "topic_count": len(topics),
        "architecture": "pfeiffer",
        "layers": [9, 10, 11, 12],
        "processed": bool(text),
    }
    RELEVANCE_DIR.mkdir(parents=True, exist_ok=True)
    out = RELEVANCE_DIR / f"template_{template_id}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
