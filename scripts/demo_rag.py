from __future__ import annotations

import json
from pathlib import Path

from ola_support.rag.grounded_generation import grounded_answer
from ola_support.rag.indexing import SENTENCE_COLLECTION

IN_SCOPE = [
    "How are support tickets prioritized?",
    "What are the response targets by severity?",
    "When should support escalate a ticket?",
    "How does a customer request refund review?",
    "Which channel should be used for account-specific updates?",
]
OUT_OF_SCOPE = "What is the capital of France?"


def main() -> None:
    results = []

    for query in IN_SCOPE + [OUT_OF_SCOPE]:
        result = grounded_answer(
            query,
            collection_name=SENTENCE_COLLECTION,
        )
        results.append({"query": query, **result})
        print(json.dumps(results[-1], indent=2))

    transcript = Path("transcripts/rag_tests.md")
    transcript.parent.mkdir(parents=True, exist_ok=True)
    with transcript.open("w", encoding="utf-8") as file:
        file.write("# Part 1 RAG demonstrations\n\n")
        for item in results:
            file.write(f"## Query: {item['query']}\n\n")
            file.write(f"Answer: {item['answer']}\n\n")
            file.write(f"Sources: {item['sources']}\n\n")
            file.write(f"Top similarity: {item['similarity']:.6f}\n\n")
            file.write(f"Fallback: {item['fallback']}\n\n")


if __name__ == "__main__":
    main()
