from __future__ import annotations

import asyncio
import json
import re
from threading import Lock
from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import StructuredMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from pydantic import BaseModel, ConfigDict

from ola_support.agents.mock_autogen_client import make_mock_client
from ola_support.rag.grounded_generation import FALLBACK
from ola_support.schemas import SupportResponse
from ola_support.tools import ticket_lookup as ticket_runtime


class ReviewVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    final_answer: str
    reason: str


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+", text.strip())
        if item.strip()
    ]


def _ticket_verdict(
    draft: str,
    source: dict[str, Any],
) -> tuple[ReviewVerdict, str]:
    if not source.get("found"):
        expected = str(source.get("error", "Ticket record was not found."))
        approved = expected.casefold() in draft.casefold()
        final = draft if approved else expected
        reason = (
            "The not-found response matches the lookup result."
            if approved
            else "Replaced the draft with the lookup result."
        )
        return ReviewVerdict(
            approved=approved,
            final_answer=final,
            reason=reason,
        ), reason

    record_id = str(source["record_id"])
    status = str(source["status"])
    known_statuses = [
        "Open",
        "In Progress",
        "Escalated",
        "Resolved",
        "Closed",
    ]

    mentioned_ids = re.findall(r"\bTKT-\d{5}\b", draft, flags=re.IGNORECASE)
    mentioned_statuses = [
        value
        for value in known_statuses
        if re.search(rf"\b{re.escape(value)}\b", draft, re.IGNORECASE)
    ]

    context_numbers = set(re.findall(r"\d+(?:\.\d+)?", json.dumps(source)))
    draft_numbers = set(re.findall(r"\d+(?:\.\d+)?", draft))

    mismatch = (
        any(value.upper() != record_id.upper() for value in mentioned_ids)
        or any(
            value.casefold() != status.casefold()
            for value in mentioned_statuses
        )
        or not draft_numbers.issubset(context_numbers)
    )

    if not mismatch:
        return ReviewVerdict(
            approved=True,
            final_answer=draft,
            reason="Ticket claims match the structured lookup result.",
        ), "Ticket claims match the structured lookup result."

    final = (
        f"Ticket {record_id} status: {status}. "
        f"Resolution time: {source['resolution_time_hours']} hours. "
        f"Escalation score: {source['escalation_score']}."
    )
    reason = "Replaced ticket claims that did not match the lookup result."
    return ReviewVerdict(
        approved=False,
        final_answer=final,
        reason=reason,
    ), reason


def _mock_review_decision(
    draft: str,
    context: str,
) -> tuple[ReviewVerdict, str]:
    if draft.strip() == FALLBACK:
        reason = "The safe fallback is appropriate for unsupported questions."
        return ReviewVerdict(
            approved=True,
            final_answer=draft,
            reason=reason,
        ), reason

    try:
        parsed = json.loads(context)
    except (json.JSONDecodeError, TypeError):
        parsed = None

    if isinstance(parsed, dict) and "record_id" in parsed:
        return _ticket_verdict(draft, parsed)

    context_normalized = _normalize(context)
    sentences = _sentences(draft)
    supported = [
        sentence
        for sentence in sentences
        if _normalize(sentence) and _normalize(sentence) in context_normalized
    ]
    unsupported = [
        sentence
        for sentence in sentences
        if _normalize(sentence) not in context_normalized
    ]

    if not unsupported:
        reason = "Every draft sentence is present in retrieved context."
        return ReviewVerdict(
            approved=True,
            final_answer=draft,
            reason=reason,
        ), reason

    revised = " ".join(supported).strip() or FALLBACK
    reason = (
        "Removed claim(s) not supported by retrieved context: "
        + "; ".join(unsupported)
    )
    return ReviewVerdict(
        approved=False,
        final_answer=revised,
        reason=reason,
    ), reason


async def review_draft(
    draft: str,
    retrieved_context: str,
) -> tuple[ReviewVerdict, Any]:
    expected, review_note = _mock_review_decision(
        draft,
        retrieved_context,
    )

    reviewer_client = make_mock_client([review_note])
    editor_client = make_mock_client([expected.model_dump_json()])

    reviewer = AssistantAgent(
        name="policy_compliance_reviewer",
        model_client=reviewer_client,
        system_message=(
            "Compare the draft to the original retrieved context. "
            "Report unsupported or unsafe claims to the Final Editor."
        ),
        reflect_on_tool_use=False,
    )

    final_editor = AssistantAgent(
        name="final_editor",
        model_client=editor_client,
        system_message=(
            "Use the original context and reviewer findings. Preserve a "
            "supported draft unchanged. Otherwise remove unsupported claims. "
            "Return the required verdict schema."
        ),
        output_content_type=ReviewVerdict,
        reflect_on_tool_use=False,
    )

    task = (
        "Review this CrewAI Composer draft.\n\n"
        f"ORIGINAL RETRIEVED CONTEXT:\n{retrieved_context}\n\n"
        f"COMPOSER DRAFT:\n{draft}"
    )

    team = RoundRobinGroupChat(
        participants=[reviewer, final_editor],
        max_turns=2,
        custom_message_types=[StructuredMessage[ReviewVerdict]],
    )

    try:
        result = await team.run(task=task)
        structured = [
            message
            for message in result.messages
            if isinstance(message, StructuredMessage)
        ]
        if not structured:
            raise AssertionError("Final Editor returned no structured verdict")

        verdict = ReviewVerdict.model_validate(structured[-1].content)
        if verdict.model_dump() != expected.model_dump():
            raise AssertionError(
                "AutoGen verdict differs from mock review result"
            )
        return verdict, result
    finally:
        await reviewer_client.close()
        await editor_client.close()


_PIPELINE_LOCK = Lock()


def run_reviewed_support_crew(query: str) -> SupportResponse:
    """Run CrewAI, capture its tool evidence, then review before returning."""
    from ola_support.agents.crew import run_support_crew

    # LAST_TOOL_RESULT is a module-level value, so protect capture from overlap.
    with _PIPELINE_LOCK:
        draft = run_support_crew(query)
        raw_tool_result = ticket_runtime.LAST_TOOL_RESULT

        if not raw_tool_result:
            context = ""
        else:
            payload = json.loads(raw_tool_result)
            if "answer" in payload:
                context = str(payload["answer"])
            else:
                context = json.dumps(payload, ensure_ascii=False)

        verdict, _ = asyncio.run(review_draft(draft.answer, context))

    return draft.model_copy(update={"answer": verdict.final_answer})
