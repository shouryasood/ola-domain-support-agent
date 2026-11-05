from __future__ import annotations

from typing import Any

from .embeddings import embed_texts
from .indexing import (
    FIXED_COLLECTION,
    SENTENCE_COLLECTION,
    get_client,
)


def retrieve(
    query: str,
    collection_name: str = SENTENCE_COLLECTION,
    top_k: int = 4,
) -> list[dict[str, Any]]:
    if not query.strip():
        raise ValueError("Query must not be empty")
    if collection_name not in {FIXED_COLLECTION, SENTENCE_COLLECTION}:
        raise ValueError(f"Unknown collection: {collection_name}")

    client = get_client()
    collection = client.get_collection(collection_name)
    count = collection.count()

    if count == 0:
        raise ValueError(
            f"Collection {collection_name} is empty; run scripts/build_index.py"
        )

    query_vector = embed_texts([query])[0]
    result = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )

    hits: list[dict[str, Any]] = []
    for text, metadata, distance in zip(
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        # For a cosine collection, Chroma returns cosine distance.
        similarity = 1.0 - float(distance)
        hits.append(
            {
                "text": text,
                "document_id": metadata["document_id"],
                "strategy": metadata["strategy"],
                "distance": float(distance),
                "similarity": similarity,
            }
        )

    return hits
