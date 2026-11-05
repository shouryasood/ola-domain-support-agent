from __future__ import annotations

import json

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ola_support.rag.grounded_generation import grounded_answer
from ola_support.tools import ticket_lookup


class RagLookupInput(BaseModel):
    query: str = Field(
        description="A support-policy question to search in the knowledge base",
        min_length=3,
    )


class RagLookupTool(BaseTool):
    name: str = "rag_lookup"
    description: str = (
        "Search the indexed support policies. Returns an extractive answer, "
        "source document IDs, top similarity, and whether the fallback fired."
    )
    args_schema: type[BaseModel] = RagLookupInput

    def _run(self, query: str) -> str:
        ticket_lookup.TOOL_CALL_COUNTS["rag_lookup"] = (
            ticket_lookup.TOOL_CALL_COUNTS.get("rag_lookup", 0) + 1
        )
        result = json.dumps(grounded_answer(query))
        ticket_lookup.LAST_TOOL_RESULT = result
        return result
