from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any, Callable

_CACHE: dict[str, Any] = {}
_STATS = {
    "hits": 0,
    "misses": 0,
    "producer_calls": 0,
}
_LOCK = RLock()


def normalize_query(query: str) -> str:
    return " ".join(query.casefold().split())


def clear_response_cache() -> None:
    with _LOCK:
        _CACHE.clear()
        for key in _STATS:
            _STATS[key] = 0


def response_cache_stats() -> dict[str, int]:
    with _LOCK:
        return dict(_STATS)


def get_or_compute_grounded_response(
    query: str,
    producer: Callable[[], Any],
) -> Any:
    key = normalize_query(query)

    with _LOCK:
        if key in _CACHE:
            _STATS["hits"] += 1
            return deepcopy(_CACHE[key])

        _STATS["misses"] += 1
        _STATS["producer_calls"] += 1
        value = producer()

        if hasattr(value, "model_dump"):
            value = value.model_dump(mode="json")

        _CACHE[key] = deepcopy(value)
        return deepcopy(value)
