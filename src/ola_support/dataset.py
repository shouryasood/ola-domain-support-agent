import json
import random
from collections import Counter
from itertools import cycle, islice
from pathlib import Path

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


def generate_dataset():
    rng = random.Random(DATA_SEED)
    escalation_rng = random.Random(ESCALATION_SEED)

    # Ensure every category and status has balanced representation.
    categories = list(islice(cycle(CATEGORIES), TOTAL_RECORDS))
    statuses = list(islice(cycle(STATUSES), TOTAL_RECORDS))

    rng.shuffle(categories)
    rng.shuffle(statuses)

    tickets = []

    for i in range(TOTAL_RECORDS):
        ticket = {
            "record_id": f"TKT-{i + 1:05d}",
            "category": categories[i],
            "status": statuses[i],
            "resolution_time_hours": round(rng.uniform(0.5, 96.0), 2),
            "days_since_created": rng.randint(0, 30),
            "escalated": escalation_rng.random() < 0.20,
        }

        tickets.append(ticket)

    return tickets


def validate_dataset(tickets):
    assert len(tickets) >= 240

    category_counts = Counter(t["category"] for t in tickets)

    status_counts = Counter(t["status"] for t in tickets)

    for category in CATEGORIES:
        assert category_counts[category] >= 3

    for status in STATUSES:
        assert status_counts[status] >= 1

    escalated_count = sum(t["escalated"] for t in tickets)

    escalation_percentage = (escalated_count / len(tickets)) * 100

    assert 10 <= escalation_percentage <= 30

    return {
        "total_records": len(tickets),
        "category_counts": dict(category_counts),
        "status_counts": dict(status_counts),
        "escalated_count": escalated_count,
        "escalation_percentage": round(escalation_percentage, 2),
    }


if __name__ == "__main__":
    tickets = generate_dataset()

    report = validate_dataset(tickets)

    output_path = Path("data/generated")
    output_path.mkdir(parents=True, exist_ok=True)

    with open(
        output_path / "support_tickets.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(tickets, f, indent=2)

    print(json.dumps(report, indent=2))
