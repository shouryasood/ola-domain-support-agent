from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from ola_support.agents.crew import run_support_crew
from ola_support.agents.review_team import review_draft
from ola_support.tools import ticket_lookup as ticket_runtime


ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT = ROOT / "transcripts" / "autogen_tests.md"


def context_from_last_tool() -> str:
    raw = ticket_runtime.LAST_TOOL_RESULT
    if not raw:
        raise AssertionError("CrewAI did not leave a tool result for review")

    payload = json.loads(raw)
    return str(payload.get("answer", json.dumps(payload)))


def summarize_messages(result: Any) -> list[dict[str, Any]]:
    summary = []
    for message in result.messages:
        content = getattr(message, "content", "")
        if hasattr(content, "model_dump"):
            content = content.model_dump()
        summary.append(
            {
                "type": type(message).__name__,
                "source": getattr(message, "source", ""),
                "content": content,
            }
        )
    return summary


async def main() -> dict[str, Any]:
    query = "What is the service credit policy?"

    # CrewAI's synchronous kickoff cannot run inside this script's active
    # asyncio loop. Keep the crew execution in a worker thread, then run the
    # AutoGen review on the event-loop thread.
    clean_draft = await asyncio.to_thread(run_support_crew, query)
    clean_context = context_from_last_tool()
    approved, approved_run = await review_draft(
        clean_draft.answer,
        clean_context,
    )

    injected_draft = (
        clean_draft.answer + " Every rider is guaranteed ₹500 within one hour."
    )
    revised, revised_run = await review_draft(
        injected_draft,
        clean_context,
    )

    assert approved.approved is True
    assert approved.final_answer == clean_draft.answer
    assert revised.approved is False
    assert "guaranteed ₹500" not in revised.final_answer

    report = {
        "approval_case": {
            "approved": approved.model_dump(),
            "draft_unchanged": approved.final_answer == clean_draft.answer,
            "messages": summarize_messages(approved_run),
        },
        "revision_case": {
            "injected_draft": injected_draft,
            "verdict": revised.model_dump(),
            "unsupported_claim_removed": (
                "guaranteed ₹500" not in revised.final_answer
            ),
            "messages": summarize_messages(revised_run),
        },
    }

    TRANSCRIPT.parent.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT.write_text(
        "# Part 4 AutoGen review demonstrations\n\n"
        "## Approved unchanged\n\n"
        f"```json\n{json.dumps(report['approval_case'], indent=2, ensure_ascii=False)}\n```\n\n"
        "## Revised unsupported claim\n\n"
        f"```json\n{json.dumps(report['revision_case'], indent=2, ensure_ascii=False)}\n```\n",
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main()), indent=2, ensure_ascii=False))
