# Part 4 governance and caching demonstrations

```json
{
  "least_autonomy": {
    "tool": "check_support_ticket_status",
    "authorized_owners": [
      "Ticket Lookup Agent"
    ],
    "unauthorized_composer_wiring_blocked": true,
    "guard_explanation": "The crew builds one explicit role-to-tool map and checks ownership before kickoff. Retrieval receives only rag_lookup, Lookup receives check_support_ticket_status, and Composer receives no tools. All agents also have delegation disabled, so they cannot acquire the lookup tool indirectly."
  },
  "risk": {
    "level": "Medium",
    "justification": "This is Medium risk because the agent handles customer-support tickets and can affect support routing. Its dataset is fabricated, it does not make medical, hiring, lending, or other high-impact determinations, and it cannot approve refunds; those require an authorized reviewer."
  },
  "budget": {
    "cap": 2000,
    "accepted_request_estimated_tokens": 265,
    "oversized_request_rejected": true,
    "rejection_detail": "Estimated request size 7756 tokens exceeds the per-request cap of 2000.",
    "tool_counts_before_rejection": {
      "rag_lookup": 0,
      "ticket_lookup": 0
    },
    "tool_counts_after_rejection": {
      "rag_lookup": 0,
      "ticket_lookup": 0
    }
  },
  "cache": {
    "normalized_key": "how are support tickets prioritized?",
    "same_response": true,
    "cache_stats": {
      "hits": 1,
      "misses": 1,
      "producer_calls": 1
    },
    "tool_counts_after_first_request": {
      "rag_lookup": 1,
      "ticket_lookup": 0
    },
    "tool_counts_after_second_request": {
      "rag_lookup": 1,
      "ticket_lookup": 0
    }
  },
  "executed_crew_tool_ownership": {
    "check_support_ticket_status": [
      "Ticket Lookup Agent"
    ]
  }
}
```

**Risk classification: Medium.** This is Medium risk because the agent handles customer-support tickets and can affect support routing. Its dataset is fabricated, it does not make medical, hiring, lending, or other high-impact determinations, and it cannot approve refunds; those require an authorized reviewer.
