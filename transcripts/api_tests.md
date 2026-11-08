# Part 3 API and privacy demonstration

This transcript records responses from the local `MOCK_LLM` app. The fabricated phone number used in the requests is omitted here; the stored document and JSONL records were checked for masking.

```json
{
  "mode": "MOCK_LLM",
  "http": {
    "ask_status": 200,
    "ask_trace_id": "f510e6751421441c97818ecc24fbf7d3",
    "ask_fallback": false,
    "ask_sources": [
      "communication_channels",
      "outage_communication",
      "chargeback_handling",
      "phone_number_change"
    ],
    "add_document_status": 200,
    "add_document_response": {
      "document_id": "api_demo_4f951cca94",
      "message": "Document saved and both indexes rebuilt.",
      "document_count": 56,
      "fixed_chunk_count": 56,
      "sentence_chunk_count": 168
    },
    "stored_document_phone_masked": true
  },
  "websocket": {
    "path": "/ws/chat",
    "turn_count": 2,
    "turns": [
      {
        "trace_id": "bcebda64379342abb064453286d402e8",
        "answer": "Ticket TKT-00001 is Closed. Reported resolution time: 91.32 hours.",
        "ticket_id": "TKT-00001",
        "ticket_status": "Closed"
      },
      {
        "trace_id": "4ccb82a8188a486aa7a12763b7e6169b",
        "answer": "Ticket TKT-00001 is Closed. Reported resolution time: 91.32 hours.",
        "ticket_id": "TKT-00001",
        "ticket_status": "Closed"
      }
    ],
    "disconnect_logged": true,
    "http_still_responded_after_disconnect": true
  },
  "jsonl": {
    "path": "logs\\api_requests.jsonl",
    "entries_checked": 6,
    "all_entries_have_trace_id": true,
    "all_entries_have_duration_ms": true,
    "raw_phone_absent": true,
    "masked_phone_present": true,
    "websocket_disconnect_event_logged": true
  }
}
```
