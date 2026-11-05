from __future__ import annotations

import json
from pathlib import Path

from ola_support.rag.indexing import SENTENCE_COLLECTION
from ola_support.rag.retrieval import retrieve

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "rag_threshold.json"

IN_SCOPE = [
    "How are support tickets prioritized?",
    "What are the response targets by severity?",
    "When should support escalate a ticket?",
    "How does a customer request refund review?",
    "Which channel should be used for account-specific updates?",
]

OUT_OF_SCOPE = [
    "What is the capital of France?",
    "How do I bake sourdough bread?",
]


def top_one_similarity(query: str) -> float:
    hits = retrieve(query, collection_name=SENTENCE_COLLECTION, top_k=1)
    if not hits:
        raise RuntimeError(f"No retrieval results for query: {query}")
    return hits[0]["similarity"]


def main() -> None:
    in_scores = {query: top_one_similarity(query) for query in IN_SCOPE}
    out_scores = {query: top_one_similarity(query) for query in OUT_OF_SCOPE}

    lowest_in_scope = min(in_scores.values())
    highest_out_scope = max(out_scores.values())

    print("In-scope top-1 scores:")
    print(json.dumps(in_scores, indent=2))
    print("Out-of-scope top-1 scores:")
    print(json.dumps(out_scores, indent=2))

    if highest_out_scope >= lowest_in_scope:
        raise RuntimeError(
            "The measured score clusters overlap. Improve the knowledge-base "
            "wording or revise the calibration queries, then measure again. "
            "Do not guess a threshold."
        )

    threshold = (highest_out_scope + lowest_in_scope) / 2
    report = {
        "collection": SENTENCE_COLLECTION,
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "in_scope_scores": in_scores,
        "out_of_scope_scores": out_scores,
        "lowest_in_scope": lowest_in_scope,
        "highest_out_of_scope": highest_out_scope,
        "threshold": threshold,
        "rule": "fallback when top-1 cosine similarity is below threshold",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Chosen threshold: {threshold:.6f}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
