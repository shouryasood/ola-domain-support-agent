from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from crewai import Agent, Crew, Process, Task

from ola_support.agents.mock_crewai_llm import MockCrewLLM
from ola_support.schemas import SupportResponse
from ola_support.tools.rag_tool import RagLookupTool
from ola_support.tools import ticket_lookup as ticket_runtime
from ola_support.tools.ticket_lookup import (
    TOOL_CALL_COUNTS,
    TicketLookupTool,
    write_escalation_report,
)


def _extract_result(result: Any) -> SupportResponse:
    pydantic_result = getattr(result, "pydantic", None)
    if pydantic_result is not None:
        return SupportResponse.model_validate(pydantic_result)

    json_dict = getattr(result, "json_dict", None)
    if json_dict:
        return SupportResponse.model_validate(json_dict)

    raw = getattr(result, "raw", result)
    if isinstance(raw, dict):
        return SupportResponse.model_validate(raw)
    return SupportResponse.model_validate_json(str(raw))


def run_support_crew(query: str) -> SupportResponse:
    if not query.strip():
        raise ValueError("Query must not be empty")

    # Set before kickoff so CrewAI telemetry does not make outbound calls.
    import os

    os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
    os.environ["OTEL_SDK_DISABLED"] = "true"
    os.environ["MOCK_LLM"] = "true"

    rag_tool = RagLookupTool()
    lookup_tool = TicketLookupTool()
    ticket_runtime.LAST_TOOL_RESULT = None

    # Give each tool-using agent a mock LLM registered only with its own
    # declared tool schema. CrewAI does not always pass `tools` into a
    # BaseLLM.call() implementation when ReAct text actions are used, so the
    # per-agent registration gives the deterministic adapter the schema it
    # needs without widening either agent's tool access.
    retrieval_llm = MockCrewLLM(registered_tools=[rag_tool])
    lookup_llm = MockCrewLLM(registered_tools=[lookup_tool])
    composer_llm = MockCrewLLM()

    retrieval_agent = Agent(
        role="Policy Retrieval Agent",
        goal="Retrieve only policy context relevant to the user question.",
        backstory="You search the local policy index and return its evidence.",
        llm=retrieval_llm,
        tools=[rag_tool],
        allow_delegation=False,
        verbose=True,
    )
    lookup_agent = Agent(
        role="Ticket Lookup Agent",
        goal="Look up the exact support ticket requested by the user.",
        backstory="You use the local generated ticket records for status lookup.",
        llm=lookup_llm,
        tools=[lookup_tool],
        allow_delegation=False,
        verbose=True,
    )
    composer_agent = Agent(
        role="Response Composer",
        goal="Compose a concise answer from the preceding tool result only.",
        backstory=(
            "You do not invent policy or ticket facts. "
            "Return the required structured response."
        ),
        llm=composer_llm,
        allow_delegation=False,
        verbose=True,
    )

    ticket_id = re.search(r"\bTKT-\d{5}\b", query, flags=re.I)

    if ticket_id:
        evidence_agent = lookup_agent
        evidence_task = Task(
            description=(
                "Use the ticket lookup tool for the exact record requested. "
                "Return the tool's JSON result. Do not infer status. "
                "USER_QUERY: {query}"
            ),
            expected_output="The JSON result returned by the ticket lookup tool.",
            agent=evidence_agent,
        )
    else:
        evidence_agent = retrieval_agent
        evidence_task = Task(
            description=(
                "Use the RAG tool to retrieve policy passages for this question. "
                "Return the tool's JSON result, including sources and fallback. "
                "USER_QUERY: {query}"
            ),
            expected_output="The JSON result returned by the RAG tool.",
            agent=evidence_agent,
        )

    composer_task = Task(
        description=(
            "Use only the preceding task result. Create the final answer in the "
            "SupportResponse schema. Do not add facts absent from the tool result. "
            "The original user question is: USER_QUERY: {query}"
        ),
        expected_output="A valid SupportResponse JSON object.",
        agent=composer_agent,
        context=[evidence_task],
        output_pydantic=SupportResponse,
    )

    crew = Crew(
        agents=[retrieval_agent, lookup_agent, composer_agent],
        tasks=[evidence_task, composer_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff(inputs={"query": query})
    return _extract_result(result)


def demonstrate_part2() -> list[dict[str, Any]]:
    TOOL_CALL_COUNTS["rag_lookup"] = 0
    TOOL_CALL_COUNTS["ticket_lookup"] = 0

    policy_response = run_support_crew("How are support tickets prioritized?")
    ticket_response = run_support_crew("What is the status of TKT-00001?")

    write_escalation_report()

    report = {
        "policy_response": policy_response.model_dump(),
        "ticket_response": ticket_response.model_dump(),
        "tool_call_counts": dict(TOOL_CALL_COUNTS),
    }

    if TOOL_CALL_COUNTS["rag_lookup"] < 1:
        raise AssertionError("RAG tool was not invoked")
    if TOOL_CALL_COUNTS["ticket_lookup"] < 1:
        raise AssertionError("Ticket lookup tool was not invoked")

    transcript_path = Path("transcripts/crew_tests.md")
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    transcript_path.write_text(
        "# Part 2 CrewAI tool demonstrations\n\n"
        "## Policy question\n\n"
        f"```json\n{json.dumps(report['policy_response'], indent=2)}\n```\n\n"
        "## Ticket question\n\n"
        f"```json\n{json.dumps(report['ticket_response'], indent=2)}\n```\n\n"
        f"Tool call counts: `{json.dumps(report['tool_call_counts'])}`\n",
        encoding="utf-8",
    )

    return [report]


if __name__ == "__main__":
    print(json.dumps(demonstrate_part2(), indent=2))
