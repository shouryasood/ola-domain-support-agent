from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Sequence

from crewai.llms.base_llm import BaseLLM

from ola_support.schemas import SupportResponse


@dataclass(frozen=True)
class ToolSpec:
    """The part of a tool schema needed for deterministic dispatch."""

    name: str
    properties: dict[str, Any]


def _message_role(message: Any) -> str:
    if isinstance(message, dict):
        return str(message.get("role", message.get("type", ""))).lower()

    return str(getattr(message, "role", getattr(message, "type", ""))).lower()


def _message_content(message: Any) -> str:
    if isinstance(message, dict):
        content = message.get("content", "")
    else:
        content = getattr(message, "content", "")

    if isinstance(content, str):
        return content

    return str(content)


def _schema_properties(schema: Any) -> dict[str, Any]:
    """Get Pydantic JSON-schema properties from a tool args schema."""
    if schema is None:
        return {}

    if isinstance(schema, dict):
        return dict(schema.get("properties", {}))

    model_json_schema = getattr(schema, "model_json_schema", None)
    if callable(model_json_schema):
        result = model_json_schema()
        return dict(result.get("properties", {}))

    schema_method = getattr(schema, "schema", None)
    if callable(schema_method):
        result = schema_method()
        return dict(result.get("properties", {}))

    return {}


def _tool_spec_from_runtime_schema(tool: Any) -> ToolSpec | None:
    """Read a CrewAI/OpenAI-style tool schema or a BaseTool instance."""
    if isinstance(tool, dict):
        function = tool.get("function", tool)
        name = function.get("name")
        parameters = function.get("parameters", {})
        properties = parameters.get("properties", {})

        if name and isinstance(properties, dict):
            return ToolSpec(str(name), dict(properties))

        return None

    name = getattr(tool, "name", None)
    args_schema = getattr(tool, "args_schema", None)
    properties = _schema_properties(args_schema)

    if name and properties:
        return ToolSpec(str(name), properties)

    return None


def _collect_runtime_specs(tools: Any) -> list[ToolSpec]:
    if not tools:
        return []

    if isinstance(tools, dict):
        tools = list(tools.values())

    specs: list[ToolSpec] = []
    for tool in tools:
        spec = _tool_spec_from_runtime_schema(tool)
        if spec is not None:
            specs.append(spec)

    return specs


def _collect_registered_specs(
    registered_tools: Sequence[Any] | None,
) -> list[ToolSpec]:
    specs: list[ToolSpec] = []

    for tool in registered_tools or []:
        spec = _tool_spec_from_runtime_schema(tool)
        if spec is not None:
            specs.append(spec)

    return specs


def _json_objects(text: str) -> list[dict[str, Any]]:
    """Extract JSON objects without relying on greedy regular expressions."""
    decoder = json.JSONDecoder()
    found: list[dict[str, Any]] = []

    for index, character in enumerate(text):
        if character != "{":
            continue

        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue

        if isinstance(value, dict):
            found.append(value)

    return found


def _latest_user_text(messages: list[Any]) -> str:
    for message in reversed(messages):
        if _message_role(message) in {"user", "human"}:
            return _message_content(message)

    return _message_content(messages[-1]) if messages else ""


def _extract_user_query(text: str) -> str:
    """Read the explicit query marker used in crew.py task descriptions."""
    match = re.search(
        r"USER_QUERY:\s*(.+?)(?:\r?\n|$)",
        text,
        flags=re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    return text.strip()


def _tool_observation_after_generated_action(
    messages: list[Any],
) -> str | None:
    """
    Find an observation only after an assistant-generated Action.

    This deliberately does not search the complete conversation or system
    prompt for Observation:. CrewAI's ReAct template can contain that word
    before any tool has run.
    """
    action_index: int | None = None

    for index, message in enumerate(messages):
        role = _message_role(message)
        content = _message_content(message)

        if role in {"assistant", "ai"} and re.search(
            r"(?m)^Action:\s*",
            content,
        ):
            action_index = index

    if action_index is None:
        return None

    for message in messages[action_index + 1 :]:
        role = _message_role(message)
        content = _message_content(message)

        if role in {"tool", "function"}:
            return content.strip()

        observation_match = re.search(
            r"(?s)Observation:\s*(.*)$",
            content,
        )
        if observation_match:
            return observation_match.group(1).strip()

    return None


def _tool_arguments(spec: ToolSpec, query: str) -> dict[str, Any]:
    """
    Build arguments from schema fields, not from a tool name.

    Part 2 declares `query` for RAG and `record_id` for ticket lookup.
    """
    if "record_id" in spec.properties:
        match = re.search(r"\bTKT-\d{5}\b", query, flags=re.IGNORECASE)
        if not match:
            raise ValueError(
                "The ticket lookup tool requires an ID such as TKT-00001."
            )
        return {"record_id": match.group(0).upper()}

    if "query" in spec.properties:
        return {"query": query}

    raise ValueError(
        f"Unsupported tool argument schema for {spec.name}: "
        f"{sorted(spec.properties)}"
    )


def _select_tool(specs: list[ToolSpec], query: str) -> ToolSpec:
    """
    Select the tool by its declared input schema.

    If the current agent has only one assigned tool, use it. If multiple
    schemas are present, choose the schema requiring record_id or query.
    """
    if not specs:
        raise ValueError(
            "No tool schemas reached MockCrewLLM. Assign the tool to the "
            "agent and pass that same tool to "
            "MockCrewLLM(registered_tools=[...])."
        )

    if len(specs) == 1:
        return specs[0]

    ticket_id_present = bool(
        re.search(r"\bTKT-\d{5}\b", query, flags=re.IGNORECASE)
    )

    if ticket_id_present:
        for spec in specs:
            if "record_id" in spec.properties:
                return spec

    for spec in specs:
        if "query" in spec.properties:
            return spec

    for spec in specs:
        if "record_id" in spec.properties:
            return spec

    raise ValueError(
        "No supplied tool has a supported `query` or `record_id` argument."
    )


def _find_tool_result(messages: list[Any]) -> dict[str, Any] | None:
    # Prefer the latest conversation messages, where task context/tool output
    # appears. Ignore tool schemas and unrelated JSON objects.
    for message in reversed(messages):
        for candidate in reversed(_json_objects(_message_content(message))):
            if (
                "sources" in candidate
                or "status" in candidate
                or "found" in candidate
            ):
                return candidate

    # Some CrewAI versions flatten prior task output into one message.
    combined = "\n".join(_message_content(message) for message in messages)
    for candidate in reversed(_json_objects(combined)):
        if (
            "sources" in candidate
            or "status" in candidate
            or "found" in candidate
        ):
            return candidate

    return None


def _composer_response(messages: list[Any]) -> str:
    tool_result = _find_tool_result(messages)

    if tool_result is None:
        return SupportResponse(
            answer="I don't know based on the available support policies.",
            fallback=True,
        ).model_dump_json()

    if "sources" in tool_result:
        return SupportResponse(
            answer=str(
                tool_result.get(
                    "answer",
                    "I don't know based on the available support policies.",
                )
            ),
            sources=list(tool_result.get("sources") or []),
            fallback=bool(tool_result.get("fallback", False)),
        ).model_dump_json()

    record_id = str(tool_result.get("record_id", ""))

    if not tool_result.get("found"):
        return SupportResponse(
            answer=f"No support ticket was found for {record_id}.",
            ticket_id=record_id or None,
            fallback=True,
        ).model_dump_json()

    status = str(tool_result["status"])
    hours = float(tool_result["resolution_time_hours"])
    score = float(tool_result["escalation_score"])

    return SupportResponse(
        answer=(
            f"Ticket {record_id} is {status}. "
            f"Reported resolution time: {hours} hours."
        ),
        ticket_id=record_id,
        ticket_status=status,
        resolution_time_hours=hours,
        escalation_score=score,
        sources=[],
        fallback=False,
    ).model_dump_json()


class MockCrewLLM(BaseLLM):
    """
    Deterministic, offline CrewAI LLM for the Part 2 demonstrations.

    Pass only the tools assigned to the agent that uses this instance:
        MockCrewLLM(registered_tools=[rag_tool])
        MockCrewLLM(registered_tools=[ticket_tool])
        MockCrewLLM()  # Composer has no tools
    """

    def __init__(
        self,
        registered_tools: Sequence[Any] | None = None,
    ) -> None:
        super().__init__(
            model="mock-deterministic",
            temperature=0,
        )
        self.registered_tools = list(registered_tools or [])
        self._tool_action_pending = False
        self._tool_action_finished = False
        self._last_tool_result: str | None = None

    def supports_function_calling(self) -> bool:
        # Return ReAct text actions for CrewAI's action parser.
        return False

    def supports_stop_words(self) -> bool:
        return False

    def get_context_window_size(self) -> int:
        return 8192

    def call(
        self,
        messages: str | list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        # CrewAI versions can pass additional values such as `from_task`.
        # Accept them so harmless framework metadata does not break the call.
        del callbacks, available_functions, kwargs

        if isinstance(messages, str):
            normalized_messages: list[Any] = [
                {"role": "user", "content": messages}
            ]
        else:
            normalized_messages = list(messages)

        # CrewAI calls the LLM again after executing a ReAct action. Its
        # follow-up prompt can be phrased as an instruction to continue, not
        # as the original user query. Once this agent has used its one
        # assigned tool, finish the task from the tool result instead of
        # interpreting that instruction as a new query and calling the tool
        # repeatedly.
        if self._tool_action_finished:
            if self._last_tool_result is not None:
                return f"Final Answer: {self._last_tool_result}"
            return (
                'Final Answer: {"answer":'
                '"I don\'t know based on the available support policies.",'
                '"sources":[],"fallback":true}'
            )

        if self._tool_action_pending:
            from ola_support.tools import ticket_lookup

            tool_result = ticket_lookup.LAST_TOOL_RESULT
            if tool_result is None:
                tool_result = _tool_observation_after_generated_action(
                    normalized_messages
                )

            self._tool_action_pending = False
            self._tool_action_finished = True
            self._last_tool_result = tool_result

            if tool_result is not None:
                return f"Final Answer: {tool_result}"

            return (
                'Final Answer: {"answer":'
                '"I don\'t know based on the available support policies.",'
                '"sources":[],"fallback":true}'
            )

        # If this call follows a model-generated Action and tool observation,
        # return the observation as the evidence task's result.
        observation = _tool_observation_after_generated_action(
            normalized_messages
        )
        if observation is not None:
            return observation

        # CrewAI may provide schemas through `tools`. Otherwise use the
        # schemas registered for this specific agent instance.
        runtime_specs = _collect_runtime_specs(tools)
        registered_specs = _collect_registered_specs(self.registered_tools)
        specs = runtime_specs or registered_specs

        if specs:
            query = _extract_user_query(_latest_user_text(normalized_messages))
            selected = _select_tool(specs, query)
            arguments = _tool_arguments(selected, query)

            self._tool_action_pending = True

            return (
                "Thought: I will use the tool assigned to this agent.\n"
                f"Action: {selected.name}\n"
                f"Action Input: {json.dumps(arguments, ensure_ascii=False)}"
            )

        # The Composer has no tools. It converts the preceding tool result
        # into the required Pydantic response JSON.
        return _composer_response(normalized_messages)
