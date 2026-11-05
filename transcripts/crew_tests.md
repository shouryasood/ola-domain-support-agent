# Part 2 CrewAI tool demonstrations

## Policy question

```json
{
  "answer": "# Ticket priority classification\n    \n    Assign priority based on urgency, customer impact, and the number of people affected. Record the reason for the selected priority in the ticket. # Ticket data retention\n    \n    Retain support tickets only for the documented operational and legal retention period. # SLA by severity\n    \n    Measure the response target from ticket creation to the first meaningful support response.",
  "sources": [
    "ticket_priority",
    "data_retention",
    "sla_policy"
  ],
  "ticket_id": null,
  "ticket_status": null,
  "resolution_time_hours": null,
  "escalation_score": null,
  "fallback": false
}
```

## Ticket question

```json
{
  "answer": "Ticket TKT-00001 is Closed. Reported resolution time: 91.32 hours.",
  "sources": [],
  "ticket_id": "TKT-00001",
  "ticket_status": "Closed",
  "resolution_time_hours": 91.32,
  "escalation_score": 0.191667,
  "fallback": false
}
```

Tool call counts: `{"ticket_lookup": 1, "rag_lookup": 1}`
