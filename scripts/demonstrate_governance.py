from __future__ import annotations

import json
import os
from pathlib import Path

from ola_support.agents.crew import (
    LAST_TOOL_OWNERSHIP,
    validate_ticket_tool_ownership,
)
from ola_support.api.routes import process_query
from ola_support.governance.budget import (
    RequestBudgetExceeded,
    enforce_request_budget,
)
from ola_support.governance.cache import (
    clear_response_cache,
    response_cache_stats,
)
from ola_support.tools.rag_tool import RagLookupTool
from ola_support.tools.ticket_lookup import TOOL_CALL_COUNTS, TicketLookupTool

ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT = ROOT / "transcripts" / "governance_tests.md"

RISK_JUSTIFICATION = (
    "This is Medium risk because the agent handles customer-support tickets "
    "and can affect support routing. Its dataset is fabricated, it does not "
    "make medical, hiring, lending, or other high-impact determinations, and "
    "it cannot approve refunds; those require an authorized reviewer."
)


def demonstrate_tool_ownership() -> dict[str, object]:
    rag_tool = RagLookupTool()
    ticket_tool = TicketLookupTool()

    valid_map = {
        "Policy Retrieval Agent": [rag_tool],
        "Ticket Lookup Agent": [ticket_tool],
        "Response Composer": [],
    }
    owners = validate_ticket_tool_ownership(valid_map, ticket_tool.name)

    invalid_map = {
        role: list(tools)
        for role, tools in valid_map.items()
    }
    invalid_map["Response Composer"].append(ticket_tool)

    unauthorized_wiring_blocked = False
    try:
        validate_ticket_tool_ownership(invalid_map, ticket_tool.name)
    except PermissionError:
        unauthorized_wiring_blocked = True

    if not unauthorized_wiring_blocked:
        raise AssertionError("The ownership guard accepted unauthorized wiring")

    return {
        "tool": ticket_tool.name,
        "authorized_owners": owners,
        "unauthorized_composer_wiring_blocked": unauthorized_wiring_blocked,
        "guard_explanation": (
            "The crew builds one explicit role-to-tool map and checks ownership "
            "before kickoff. Retrieval receives only rag_lookup, Lookup receives "
            "check_support_ticket_status, and Composer receives no tools. All "
            "agents also have delegation disabled, so they cannot acquire the "
            "lookup tool indirectly."
        ),
    }


def demonstrate_budget_and_cache() -> dict[str, object]:
    os.environ["TOKEN_BUDGET_PER_REQUEST"] = "2000"
    clear_response_cache()
    TOOL_CALL_COUNTS.clear()
    TOOL_CALL_COUNTS.update({"rag_lookup": 0, "ticket_lookup": 0})

    accepted_query = "How are support tickets prioritized?"
    accepted_budget = enforce_request_budget(accepted_query)

    oversized_query = "support policy " * 2000
    tool_counts_before_rejection = dict(TOOL_CALL_COUNTS)
    rejected = False
    rejection_detail = ""
    try:
        process_query(oversized_query)
    except RequestBudgetExceeded as exc:
        rejected = True
        rejection_detail = str(exc)

    tool_counts_after_rejection = dict(TOOL_CALL_COUNTS)
    if not rejected:
        raise AssertionError("The oversized request was not rejected")
    if tool_counts_before_rejection != tool_counts_after_rejection:
        raise AssertionError("A tool ran before the budget rejected the request")

    first_response, _ = process_query(accepted_query)
    calls_after_first = dict(TOOL_CALL_COUNTS)
    ownership_after_first_run = dict(LAST_TOOL_OWNERSHIP)

    second_response, _ = process_query(accepted_query)
    calls_after_second = dict(TOOL_CALL_COUNTS)
    cache_stats = response_cache_stats()

    if first_response.answer != second_response.answer:
        raise AssertionError("The cached answer differs from the first answer")
    if calls_after_first != calls_after_second:
        raise AssertionError("The cache hit caused a redundant tool call")
    if cache_stats != {"hits": 1, "misses": 1, "producer_calls": 1}:
        raise AssertionError(f"Unexpected cache counters: {cache_stats}")
    if ownership_after_first_run.get("check_support_ticket_status") != [
        "Ticket Lookup Agent"
    ]:
        raise AssertionError("The executed crew has unexpected lookup owners")

    return {
        "budget": {
            "cap": accepted_budget["token_cap"],
            "accepted_request_estimated_tokens": accepted_budget[
                "estimated_tokens"
            ],
            "oversized_request_rejected": rejected,
            "rejection_detail": rejection_detail,
            "tool_counts_before_rejection": tool_counts_before_rejection,
            "tool_counts_after_rejection": tool_counts_after_rejection,
        },
        "cache": {
            "normalized_key": "how are support tickets prioritized?",
            "same_response": first_response.answer == second_response.answer,
            "cache_stats": cache_stats,
            "tool_counts_after_first_request": calls_after_first,
            "tool_counts_after_second_request": calls_after_second,
        },
        "executed_crew_tool_ownership": ownership_after_first_run,
    }


def main() -> dict[str, object]:
    os.environ["MOCK_LLM"] = "true"
    os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
    os.environ["OTEL_SDK_DISABLED"] = "true"
    os.environ["CREWAI_TRACING_ENABLED"] = "false"

    report = {
        "least_autonomy": demonstrate_tool_ownership(),
        "risk": {
            "level": "Medium",
            "justification": RISK_JUSTIFICATION,
        },
        **demonstrate_budget_and_cache(),
    }

    TRANSCRIPT.parent.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT.write_text(
        "# Part 4 governance and caching demonstrations\n\n"
        f"```json\n{json.dumps(report, indent=2, ensure_ascii=False)}\n```\n\n"
        f"**Risk classification: Medium.** {RISK_JUSTIFICATION}\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


if __name__ == "__main__":
    main()
