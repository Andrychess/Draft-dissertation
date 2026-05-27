"""Lightweight in-process caches (single-worker dev/small deploy)."""

from __future__ import annotations

import time
from functools import lru_cache
from pathlib import Path
from typing import Optional

_lecture_cache: dict[str, tuple[float, str]] = {}
_SETTINGS_TTL_SEC = 30.0
_settings_cache: tuple[float, dict[str, str]] | None = None


def get_cached_lecture_text(file_path: str, loader) -> str:
    """Cache extracted lecture text by path + mtime."""
    path = Path(file_path)
    if not path.exists():
        return ""
    mtime = path.stat().st_mtime
    key = str(path.resolve())
    cached = _lecture_cache.get(key)
    if cached and cached[0] == mtime:
        return cached[1]
    text = loader(file_path)
    _lecture_cache[key] = (mtime, text)
    return text


def invalidate_lecture_cache(file_path: str) -> None:
    key = str(Path(file_path).resolve())
    _lecture_cache.pop(key, None)


def get_cached_system_settings(db, loader) -> dict[str, str]:
    global _settings_cache
    now = time.monotonic()
    if _settings_cache and now - _settings_cache[0] < _SETTINGS_TTL_SEC:
        return _settings_cache[1]
    values = loader(db)
    _settings_cache = (now, values)
    return values


def invalidate_settings_cache() -> None:
    global _settings_cache
    _settings_cache = None
