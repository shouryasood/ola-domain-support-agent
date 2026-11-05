from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SupportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(description="Final response shown to the support user")
    sources: list[str] = Field(
        default_factory=list,
        description="Knowledge-base document IDs supporting the answer",
    )
    ticket_id: str | None = None
    ticket_status: str | None = None
    resolution_time_hours: float | None = None
    escalation_score: float | None = Field(default=None, ge=0.0, le=1.0)
    fallback: bool = False
