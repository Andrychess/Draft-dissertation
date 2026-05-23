"""Extract thematic vector T from lecture material for relevance adapter (per template)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_RU_STOP = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "как", "а", "то", "все", "это",
    "для", "по", "из", "от", "при", "или", "же", "бы", "у", "о", "об", "до", "за",
}


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9_-]+", text.lower())
    return [w for w in words if len(w) > 3 and w not in _RU_STOP]


def extract_topics(lecture_text: str, limit: int = 40) -> list[str]:
    freq: dict[str, int] = {}
    for token in _tokenize(lecture_text):
        freq[token] = freq.get(token, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], -len(x[0])))
    return [w for w, _ in ranked[:limit]]


def save_template_topics(template_id: int, lecture_text: str, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or (ROOT / "ai-service" / "models" / "adapters" / "relevance")
    out_dir.mkdir(parents=True, exist_ok=True)
    topics = extract_topics(lecture_text)
    payload = {
        "template_id": template_id,
        "topics": topics,
        "topic_count": len(topics),
        "architecture": "pfeiffer",
        "layers": [9, 10, 11, 12],
    }
    path = out_dir / f"template_{template_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    sample = (
        "Объектно-ориентированное программирование использует классы, объекты, "
        "наследование, полиморфизм и инкапсуляцию."
    )
    p = save_template_topics(0, sample)
    print("saved", p)
