from __future__ import annotations

import json

from ola_support.rag.indexing import build_indexes
from ola_support.rag.retrieval import retrieve


def main() -> None:
    counts = build_indexes()

    sample = "How are support tickets prioritized?"
    fixed_hits = retrieve(sample, "support_fixed_overlap", top_k=2)
    sentence_hits = retrieve(sample, "support_sentence", top_k=2)

    result = {
        "counts": counts,
        "sample_query": sample,
        "fixed_results": fixed_hits,
        "sentence_results": sentence_hits,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
