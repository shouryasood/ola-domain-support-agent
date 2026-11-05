from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

CATEGORIES = [
    "Billing",
    "Technical Issue",
    "Account Access",
    "Product Defect",
    "General Inquiry",
]

STATUSES = [
    "Open",
    "In Progress",
    "Escalated",
    "Resolved",
    "Closed",
]

TOTAL_RECORDS = 240
DATA_SEED = 2026
ESCALATION_SEED = 10
ESCALATION_PROBABILITY = 0.20

RESOLUTION_MIN_HOURS = 0.5
RESOLUTION_MAX_HOURS = 96.0
AMOUNT_MIN_INR = 50
AMOUNT_MAX_INR = 5_000


def generate_dataset() -> list[dict[str, Any]]:
    """Generate a reproducible synthetic dataset of support tickets."""
    rng = random.Random(DATA_SEED)
    escalation_rng = random.Random(ESCALATION_SEED)

    # Equal category and status weights. Cycling guarantees equal counts;
    # shuffling makes the sequence deterministic but not ordered by value.
    categories = [
        CATEGORIES[index % len(CATEGORIES)] for index in range(TOTAL_RECORDS)
    ]
    statuses = [
        STATUSES[index % len(STATUSES)] for index in range(TOTAL_RECORDS)
    ]
    rng.shuffle(categories)
    rng.shuffle(statuses)

    tickets: list[dict[str, Any]] = []
    for index in range(TOTAL_RECORDS):
        tickets.append(
            {
                "record_id": f"TKT-{index + 1:05d}",
                "category": categories[index],
                "status": statuses[index],
                "resolution_time_hours": round(
                    rng.uniform(RESOLUTION_MIN_HOURS, RESOLUTION_MAX_HOURS),
                    2,
                ),
                "days_since_created": rng.randint(0, 30),
                "escalated": (
                    escalation_rng.random() < ESCALATION_PROBABILITY
                ),
                # Synthetic field added to document the requested amount range.
                "amount_inr": rng.randint(AMOUNT_MIN_INR, AMOUNT_MAX_INR),
            }
        )

    return tickets


def validate_dataset(tickets: list[dict[str, Any]]) -> dict[str, Any]:
    if len(tickets) < 40:
        raise ValueError(f"Expected at least 40 records; found {len(tickets)}")

    required_fields = {
        "record_id",
        "category",
        "status",
        "resolution_time_hours",
        "days_since_created",
        "escalated",
    }

    for ticket in tickets:
        missing = required_fields.difference(ticket)
        if missing:
            raise ValueError(
                f"{ticket.get('record_id', '<unknown>')} missing {sorted(missing)}"
            )

        if ticket["category"] not in CATEGORIES:
            raise ValueError(f"Unknown category: {ticket['category']}")

        if ticket["status"] not in STATUSES:
            raise ValueError(f"Unknown status: {ticket['status']}")

        age = ticket["days_since_created"]
        if not isinstance(age, int) or not 0 <= age <= 30:
            raise ValueError(
                f"days_since_created must be an integer from 0 through 30; got {age}"
            )

        hours = ticket["resolution_time_hours"]
        if not RESOLUTION_MIN_HOURS <= hours <= RESOLUTION_MAX_HOURS:
            raise ValueError(f"Invalid resolution duration: {hours}")

        if not isinstance(ticket["escalated"], bool):
            raise ValueError("escalated must be a boolean")

        amount = ticket.get("amount_inr")
        if (
            amount is not None
            and not AMOUNT_MIN_INR <= amount <= AMOUNT_MAX_INR
        ):
            raise ValueError(f"Invalid amount_inr: {amount}")

    category_counts = Counter(ticket["category"] for ticket in tickets)
    status_counts = Counter(ticket["status"] for ticket in tickets)
    escalated_count = sum(ticket["escalated"] for ticket in tickets)
    escalation_percentage = 100 * escalated_count / len(tickets)

    for category in CATEGORIES:
        if category_counts[category] < 3:
            raise ValueError(
                f"{category} must occur at least 3 times; "
                f"found {category_counts[category]}"
            )

    for status in STATUSES:
        if status_counts[status] < 1:
            raise ValueError(f"Required status is missing: {status}")

    if not 10 <= escalation_percentage <= 30:
        raise ValueError(
            f"Escalation rate is {escalation_percentage:.2f}%, outside 10–30%. "
            "Change a seed or escalation probability, then regenerate. "
            "Do not hand-edit records."
        )

    return {
        "total_records": len(tickets),
        "category_counts": dict(category_counts),
        "status_counts": dict(status_counts),
        "escalated_count": escalated_count,
        "escalation_percentage": round(escalation_percentage, 2),
        "design": {
            "data_seed": DATA_SEED,
            "escalation_seed": ESCALATION_SEED,
            "category_weights": "equal; 20% each",
            "status_weights": "equal; 20% each",
            "escalation_probability": ESCALATION_PROBABILITY,
            "resolution_time_hours_range": [
                RESOLUTION_MIN_HOURS,
                RESOLUTION_MAX_HOURS,
            ],
            "amount_inr_range": [AMOUNT_MIN_INR, AMOUNT_MAX_INR],
        },
    }


def write_outputs(
    tickets: list[dict[str, Any]],
    report: dict[str, Any],
) -> None:
    generated_dir = ROOT / "data" / "generated"
    reports_dir = ROOT / "data" / "reports"
    generated_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    (generated_dir / "support_tickets.json").write_text(
        json.dumps(tickets, indent=2),
        encoding="utf-8",
    )
    (reports_dir / "dataset_report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )


# Expose the required list for later tools to import.
SUPPORT_TICKETS = generate_dataset()


if __name__ == "__main__":
    dataset_report = validate_dataset(SUPPORT_TICKETS)
    write_outputs(SUPPORT_TICKETS, dataset_report)
    print(json.dumps(dataset_report, indent=2))
