from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .indexing import FIXED_COLLECTION, SENTENCE_COLLECTION
from .retrieval import retrieve

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = ROOT / "reports" / "retrieval_comparison.csv"

# Gold IDs are the policy documents that should answer each question.
# Use the same five queries for both chunking collections.
EVALUATION_QUERIES = [
    (
        "How are support tickets prioritized?",
        {"ticket_priority"},
    ),
    (
        "What are the response targets by severity?",
        {"sla_policy"},
    ),
    (
        "When should support escalate a ticket?",
        {"escalation_matrix"},
    ),
    (
        "How does a customer request refund review?",
        {"refund_compensation"},
    ),
    (
        "Which channel should be used for account-specific updates?",
        {"communication_channels"},
    ),
]


def score_query(
    query: str,
    gold_docs: set[str],
    collection_name: str,
    top_k: int = 4,
) -> dict[str, Any]:
    hits = retrieve(query, collection_name=collection_name, top_k=top_k)

    # Deduplicate parent documents before scoring. Multiple chunks from one
    # policy document count as one retrieved document.
    retrieved_docs = list(dict.fromkeys(hit["document_id"] for hit in hits))
    relevant_retrieved = sorted(set(retrieved_docs) & gold_docs)

    precision = (
        len(relevant_retrieved) / len(retrieved_docs)
        if retrieved_docs
        else 0.0
    )
    recall = len(relevant_retrieved) / len(gold_docs) if gold_docs else 0.0

    return {
        "query": query,
        "collection": collection_name,
        "gold_docs": "|".join(sorted(gold_docs)),
        "retrieved_docs": "|".join(retrieved_docs),
        "precision_arithmetic": (
            f"{len(relevant_retrieved)}/{len(retrieved_docs)}"
            if retrieved_docs
            else "0/0"
        ),
        "precision": precision,
        "recall_arithmetic": f"{len(relevant_retrieved)}/{len(gold_docs)}",
        "recall": recall,
    }


def evaluate() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for query, gold_docs in EVALUATION_QUERIES:
        for collection_name in (FIXED_COLLECTION, SENTENCE_COLLECTION):
            rows.append(
                score_query(
                    query=query,
                    gold_docs=gold_docs,
                    collection_name=collection_name,
                    top_k=4,
                )
            )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    return rows
