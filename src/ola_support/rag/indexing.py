from __future__ import annotations

from pathlib import Path

import chromadb

from .chunking import Chunk, chunk_documents
from .embeddings import embed_texts

ROOT = Path(__file__).resolve().parents[3]
KB_DIR = ROOT / "knowledge_base"
CHROMA_DIR = ROOT / "data" / "chroma"

FIXED_COLLECTION = "support_fixed_overlap"
SENTENCE_COLLECTION = "support_sentence"


def load_documents() -> dict[str, str]:
    documents: dict[str, str] = {}

    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            documents[path.stem] = text

    if len(documents) < 12:
        raise ValueError(
            f"Expected at least 12 non-empty documents in {KB_DIR}; "
            f"found {len(documents)}"
        )

    return documents


def get_client() -> chromadb.PersistentClient:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def _replace_collection(
    client: chromadb.PersistentClient,
    name: str,
):
    existing_names = set()
    for item in client.list_collections():
        existing_names.add(item if isinstance(item, str) else item.name)

    # These are derived indexes, so rebuilding replaces only these two
    # named collections and leaves source documents and other collections alone.
    if name in existing_names:
        client.delete_collection(name)

    return client.create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def _upsert_chunks(
    collection,
    chunks: list[Chunk],
    batch_size: int = 100,
) -> None:
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        vectors = embed_texts([chunk.text for chunk in batch])

        collection.upsert(
            ids=[chunk.chunk_id for chunk in batch],
            documents=[chunk.text for chunk in batch],
            metadatas=[
                {
                    "document_id": chunk.document_id,
                    "strategy": chunk.strategy,
                }
                for chunk in batch
            ],
            embeddings=vectors,
        )


def build_indexes() -> dict[str, int]:
    documents = load_documents()
    fixed, sentence = chunk_documents(documents)
    client = get_client()

    fixed_collection = _replace_collection(client, FIXED_COLLECTION)
    sentence_collection = _replace_collection(client, SENTENCE_COLLECTION)

    _upsert_chunks(fixed_collection, fixed)
    _upsert_chunks(sentence_collection, sentence)

    return {
        "document_count": len(documents),
        "fixed_chunk_count": fixed_collection.count(),
        "sentence_chunk_count": sentence_collection.count(),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(build_indexes(), indent=2))
