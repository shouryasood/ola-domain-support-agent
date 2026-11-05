from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ola_support.dataset import SUPPORT_TICKETS

ROOT = Path(__file__).resolve().parents[3]
REPORT_PATH = ROOT / "data" / "reports" / "escalation_report.json"

TICKETS_BY_ID = {ticket["record_id"]: ticket for ticket in SUPPORT_TICKETS}

TOOL_CALL_COUNTS = {
    "ticket_lookup": 0,
}
LAST_TOOL_RESULT: str | None = None


def escalation_score(ticket: dict[str, Any]) -> float:
    recency = 1.0 - ticket["days_since_created"] / 30.0
    score = 0.75 * float(ticket["escalated"]) + 0.25 * recency
    return round(min(1.0, max(0.0, score)), 6)


@lru_cache(maxsize=1)
def recommended_escalation_threshold() -> float:
    scores = [escalation_score(ticket) for ticket in SUPPORT_TICKETS]
    return float(np.quantile(scores, 0.80))


def check_support_ticket_status(record_id: str) -> dict[str, Any]:
    ticket = TICKETS_BY_ID.get(record_id)
    if ticket is None:
        return {
            "found": False,
            "record_id": record_id,
            "error": "Ticket record was not found.",
        }

    score = escalation_score(ticket)
    threshold = recommended_escalation_threshold()

    return {
        "found": True,
        "record_id": record_id,
        "status": ticket["status"],
        "resolution_time_hours": ticket["resolution_time_hours"],
        "days_since_created": ticket["days_since_created"],
        "escalated": ticket["escalated"],
        "escalation_score": score,
        "recommended_escalation_threshold": round(threshold, 6),
        "recommend_escalation": score >= threshold,
        "score_formula": "0.75 * escalated + 0.25 * (1 - days_since_created / 30)",
        "threshold_basis": "80th percentile of this generated dataset's scores",
    }


def write_escalation_report() -> dict[str, Any]:
    scores = [escalation_score(ticket) for ticket in SUPPORT_TICKETS]
    threshold = recommended_escalation_threshold()

    report = {
        "record_count": len(SUPPORT_TICKETS),
        "score_formula": (
            "0.75 * float(escalated) + 0.25 * (1 - days_since_created / 30)"
        ),
        "threshold_percentile": 80,
        "threshold": round(threshold, 6),
        "score_min": min(scores),
        "score_max": max(scores),
        "sample_records": [
            check_support_ticket_status("TKT-00001"),
            check_support_ticket_status("NOT-A-TICKET"),
        ],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


class TicketLookupInput(BaseModel):
    record_id: str = Field(
        description="Ticket ID such as TKT-00001",
        min_length=1,
    )


class TicketLookupTool(BaseTool):
    name: str = "check_support_ticket_status"
    description: str = (
        "Look up one support ticket by exact record ID. "
        "Returns its status, resolution time, escalation score, and "
        "whether the score meets the dataset-based recommendation threshold."
    )
    args_schema: type[BaseModel] = TicketLookupInput

    def _run(self, record_id: str) -> str:
        global LAST_TOOL_RESULT
        TOOL_CALL_COUNTS["ticket_lookup"] += 1
        result = check_support_ticket_status(record_id)
        LAST_TOOL_RESULT = json.dumps(result)
        return LAST_TOOL_RESULT


if __name__ == "__main__":
    print(json.dumps(write_escalation_report(), indent=2))
