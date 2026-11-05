from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .indexing import SENTENCE_COLLECTION
from .retrieval import retrieve

ROOT = Path(__file__).resolve().parents[3]
THRESHOLD_PATH = ROOT / "reports" / "rag_threshold.json"
FALLBACK = "I don't know based on the available support policies."


def load_threshold() -> float:
    if not THRESHOLD_PATH.exists():
        raise FileNotFoundError(
            f"Missing {THRESHOLD_PATH}; run scripts/calibrate_threshold.py first"
        )

    report = json.loads(THRESHOLD_PATH.read_text(encoding="utf-8"))
    return float(report["threshold"])


def grounded_answer(
    query: str,
    top_k: int = 4,
    collection_name: str | None = None,
) -> dict[str, Any]:
    selected_collection = (
        collection_name or os.getenv("RAG_COLLECTION") or SENTENCE_COLLECTION
    )
    threshold = load_threshold()
    hits = retrieve(query, selected_collection, top_k=top_k)

    if not hits or hits[0]["similarity"] < threshold:
        return {
            "answer": FALLBACK,
            "sources": [],
            "similarity": hits[0]["similarity"] if hits else 0.0,
            "fallback": True,
        }

    # Deterministic extractive mock generation: all answer text is copied
    # from retrieved context, so this stage cannot introduce unsupported claims.
    answer_parts: list[str] = []
    source_ids: list[str] = []

    for hit in hits:
        if hit["text"] not in answer_parts:
            answer_parts.append(hit["text"])
        if hit["document_id"] not in source_ids:
            source_ids.append(hit["document_id"])

    return {
        "answer": " ".join(answer_parts),
        "sources": source_ids,
        "similarity": hits[0]["similarity"],
        "fallback": False,
    }
