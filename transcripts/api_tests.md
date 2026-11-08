# Part 3 API and privacy demonstration

This transcript records responses from the local `MOCK_LLM` app. The fabricated phone number used in the requests is omitted here; the stored document and JSONL records were checked for masking.

```json
{
  "mode": "MOCK_LLM",
  "http": {
    "ask_status": 200,
    "ask_trace_id": "9ac9ca03eb3e4cc5bc83db39bc0a66ee",
    "ask_fallback": false,
    "ask_sources": [
      "communication_channels",
      "outage_communication",
      "chargeback_handling",
      "phone_number_change"
    ],
    "add_document_status": 200,
    "add_document_response": {
      "document_id": "api_demo_c660fa1adc",
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
        "trace_id": "3b420a491ab14bcc89d761cfe0f74efc",
        "answer": "Ticket TKT-00001 is Closed. Reported resolution time: 91.32 hours.",
        "ticket_id": "TKT-00001",
        "ticket_status": "Closed"
      },
      {
        "trace_id": "6c1f32e0e78c49e7b8519610f29e8201",
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
