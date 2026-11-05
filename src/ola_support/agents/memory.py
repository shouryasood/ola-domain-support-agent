from __future__ import annotations

import re

from langchain_core.chat_history import InMemoryChatMessageHistory

SESSION_HISTORIES: dict[str, InMemoryChatMessageHistory] = {}


def history_for(session_id: str) -> InMemoryChatMessageHistory:
    return SESSION_HISTORIES.setdefault(
        session_id,
        InMemoryChatMessageHistory(),
    )


def answer_with_session_memory(session_id: str, message: str) -> str:
    history = history_for(session_id)

    # The teaching demonstration remembers a ticket ID from earlier turns.
    remembered_ids: list[str] = []
    for prior in history.messages:
        remembered_ids.extend(
            re.findall(r"\bTKT-\d{5}\b", prior.content, flags=re.I)
        )

    current_ids = re.findall(r"\bTKT-\d{5}\b", message, flags=re.I)
    if current_ids:
        answer = (
            f"I’ll remember ticket {current_ids[0].upper()} in this session."
        )
    elif "which ticket" in message.lower() and remembered_ids:
        answer = (
            f"The ticket mentioned earlier was {remembered_ids[-1].upper()}."
        )
    elif "which ticket" in message.lower():
        answer = "No ticket ID has been mentioned in this session."
    else:
        answer = "Session memory demonstration response."

    history.add_user_message(message)
    history.add_ai_message(answer)
    return answer


def demonstrate_memory() -> str:
    first = answer_with_session_memory(
        "session-A",
        "Remember ticket TKT-00001 for my next question.",
    )
    second = answer_with_session_memory(
        "session-A",
        "Which ticket did I mention?",
    )
    fresh = answer_with_session_memory(
        "session-B",
        "Which ticket did I mention?",
    )

    if "TKT-00001" not in second:
        raise AssertionError("Existing session did not carry the ticket ID")
    if "No ticket ID" not in fresh:
        raise AssertionError("Fresh session incorrectly inherited prior state")

    return (
        f"Session A, turn 1: {first}\n"
        f"Session A, turn 2: {second}\n"
        f"Fresh session B: {fresh}\n"
    )


if __name__ == "__main__":
    from pathlib import Path

    transcript = demonstrate_memory()
    path = Path("transcripts/memory_tests.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Session memory demonstration\n\n" + transcript, encoding="utf-8"
    )
    print(transcript)
