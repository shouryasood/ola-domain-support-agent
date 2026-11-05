from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    text: str
    strategy: str


def split_fixed_with_overlap(
    document_id: str,
    text: str,
    chunk_size_words: int = 90,
    overlap_words: int = 20,
) -> list[Chunk]:
    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be positive")
    if overlap_words < 0 or overlap_words >= chunk_size_words:
        raise ValueError(
            "overlap_words must be >= 0 and smaller than chunk size"
        )

    words = text.split()
    step = chunk_size_words - overlap_words
    chunks: list[Chunk] = []

    for start in range(0, len(words), step):
        piece = words[start : start + chunk_size_words]
        if not piece:
            break

        chunks.append(
            Chunk(
                chunk_id=f"fixed:{document_id}:{start}",
                document_id=document_id,
                text=" ".join(piece),
                strategy="fixed_overlap",
            )
        )

        if start + chunk_size_words >= len(words):
            break

    return chunks


def split_into_sentences(document_id: str, text: str) -> list[Chunk]:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
        if sentence.strip()
    ]

    return [
        Chunk(
            chunk_id=f"sentence:{document_id}:{index}",
            document_id=document_id,
            text=sentence,
            strategy="sentence",
        )
        for index, sentence in enumerate(sentences)
    ]


def chunk_documents(
    documents: dict[str, str],
) -> tuple[list[Chunk], list[Chunk]]:
    fixed_chunks: list[Chunk] = []
    sentence_chunks: list[Chunk] = []

    for document_id, text in sorted(documents.items()):
        fixed_chunks.extend(split_fixed_with_overlap(document_id, text))
        sentence_chunks.extend(split_into_sentences(document_id, text))

    return fixed_chunks, sentence_chunks
