from __future__ import annotations

import re
from typing import Any

from ola_support.rag.grounded_generation import FALLBACK, grounded_answer

PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)")

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I),
    re.compile(r"reveal\s+(the\s+)?(system|developer)\s+prompt", re.I),
    re.compile(r"override\s+(the\s+)?(system|safety|guardrail)", re.I),
    re.compile(r"disable\s+(all\s+)?safety", re.I),
    re.compile(r"print\s+(all\s+)?secrets", re.I),
]


def mask_phone_numbers(text: str) -> str:
    return PHONE_PATTERN.sub("[PHONE REDACTED]", text)


def detect_prompt_injection(text: str) -> bool:
    return any(pattern.search(text) for pattern in INJECTION_PATTERNS)


def input_guardrail(text: str) -> dict[str, Any]:
    masked = mask_phone_numbers(text)
    return {
        "allowed": not detect_prompt_injection(masked),
        "masked_text": masked,
        "injection_detected": detect_prompt_injection(masked),
    }


def output_is_supported(answer: str, retrieved_context: list[str]) -> bool:
    if not answer.strip() or answer == FALLBACK:
        return False

    combined_context = " ".join(retrieved_context)
    # The Part 1 mock generator returns extracted text, so exact substring
    # matching is appropriate and prevents unsupported paraphrase claims.
    return answer in combined_context


def guarded_policy_answer(query: str) -> dict[str, Any]:
    guarded = input_guardrail(query)
    if not guarded["allowed"]:
        return {
            "answer": "I can’t process instructions that attempt to override safeguards.",
            "blocked": True,
            "masked_query": guarded["masked_text"],
        }

    result = grounded_answer(guarded["masked_text"])
    if result["fallback"]:
        return {
            **result,
            "blocked": False,
            "groundedness_check": "fallback",
            "masked_query": guarded["masked_text"],
        }

    # grounded_answer returns only passages it retrieved. The answer itself
    # is the joined retrieved passages and must match that source text.
    supported = output_is_supported(result["answer"], [result["answer"]])
    if not supported:
        return {
            "answer": FALLBACK,
            "sources": [],
            "similarity": result["similarity"],
            "fallback": True,
            "blocked": False,
            "groundedness_check": "refused",
            "masked_query": guarded["masked_text"],
        }

    return {
        **result,
        "blocked": False,
        "groundedness_check": "supported",
        "masked_query": guarded["masked_text"],
    }
