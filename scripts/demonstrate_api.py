from __future__ import annotations

import json
import os
from pathlib import Path
import uuid
from typing import Any

os.environ["MOCK_LLM"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from fastapi.testclient import TestClient

from ola_support.api.logging_config import LOG_PATH
from ola_support.api.main import app
from ola_support.rag.indexing import KB_DIR, build_indexes


ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT_PATH = ROOT / "transcripts" / "api_tests.md"
RAW_PHONE = "9876543210"


def _read_new_log_entries(start_offset: int) -> list[dict[str, Any]]:
    with LOG_PATH.open("rb") as log_file:
        log_file.seek(start_offset)
        new_text = log_file.read().decode("utf-8")

    return [json.loads(line) for line in new_text.splitlines() if line.strip()]


def run_demo() -> dict[str, Any]:
    run_id = uuid.uuid4().hex[:10]
    document_id = f"api_demo_{run_id}"
    temporary_document = KB_DIR / f"{document_id}.md"
    document_was_created = False
    report: dict[str, Any] = {}

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_start_offset = LOG_PATH.stat().st_size if LOG_PATH.exists() else 0

    try:
        with TestClient(app) as client:
            ask_query = (
                "Which channel should support use for account-specific updates? "
                f"My phone is {RAW_PHONE}."
            )
            ask_response = client.post(
                "/ask",
                json={"query": ask_query},
            )
            assert ask_response.status_code == 200, ask_response.text
            ask_payload = ask_response.json()

            document_text = (
                "This temporary API demonstration document describes a "
                "fabricated support note and its masked contact number "
                f"{RAW_PHONE}. It is removed after the endpoint check."
            )
            add_response = client.post(
                "/add-document",
                json={"document_id": document_id, "text": document_text},
            )
            assert add_response.status_code == 200, add_response.text
            document_was_created = temporary_document.exists()
            assert document_was_created, "The add-document route did not save its document"
            stored_text = temporary_document.read_text(encoding="utf-8")
            assert RAW_PHONE not in stored_text
            assert "[PHONE REDACTED]" in stored_text

            websocket_turns = []
            with client.websocket_connect(
                f"/ws/chat?session_id=api-demo-{run_id}"
            ) as websocket:
                for message in (
                    "What is the status of TKT-00001?",
                    "What is its status?",
                ):
                    websocket.send_text(message)
                    websocket_turns.append(websocket.receive_json())

            # Exiting the websocket context closes the socket while the server
            # waits for the next message, exercising WebSocketDisconnect.
            after_disconnect = client.get("/openapi.json")
            assert after_disconnect.status_code == 200

        new_entries = _read_new_log_entries(log_start_offset)
        assert new_entries, "The API did not append structured JSONL records"
        assert all(entry.get("trace_id") for entry in new_entries)
        assert all("duration_ms" in entry for entry in new_entries)
        new_log_text = json.dumps(new_entries, ensure_ascii=False)
        assert RAW_PHONE not in new_log_text, "A raw phone number reached JSONL logs"
        assert "[PHONE REDACTED]" in new_log_text

        ws_entries = [
            entry
            for entry in new_entries
            if entry.get("endpoint") == "/ws/chat"
        ]
        assert len([entry for entry in ws_entries if entry.get("status_code") == 200]) >= 2
        assert any(entry.get("event") == "client_disconnected" for entry in ws_entries)

        report = {
            "mode": "MOCK_LLM",
            "http": {
                "ask_status": ask_response.status_code,
                "ask_trace_id": ask_response.headers.get("X-Trace-ID"),
                "ask_fallback": ask_payload["fallback"],
                "ask_sources": ask_payload["sources"],
                "add_document_status": add_response.status_code,
                "add_document_response": add_response.json(),
                "stored_document_phone_masked": True,
            },
            "websocket": {
                "path": "/ws/chat",
                "turn_count": len(websocket_turns),
                "turns": [
                    {
                        "trace_id": turn["trace_id"],
                        "answer": turn["response"]["answer"],
                        "ticket_id": turn["response"]["ticket_id"],
                        "ticket_status": turn["response"]["ticket_status"],
                    }
                    for turn in websocket_turns
                ],
                "disconnect_logged": True,
                "http_still_responded_after_disconnect": after_disconnect.status_code == 200,
            },
            "jsonl": {
                "path": str(LOG_PATH.relative_to(ROOT)),
                "entries_checked": len(new_entries),
                "all_entries_have_trace_id": True,
                "all_entries_have_duration_ms": True,
                "raw_phone_absent": True,
                "masked_phone_present": True,
                "websocket_disconnect_event_logged": True,
            },
        }

        assert report["http"]["ask_trace_id"]
        assert len(websocket_turns) == 2
        assert report["websocket"]["http_still_responded_after_disconnect"]
        if RAW_PHONE in json.dumps(report, ensure_ascii=False):
            raise AssertionError("The raw phone number reached the API transcript")

        TRANSCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
        TRANSCRIPT_PATH.write_text(
            "# Part 3 API and privacy demonstration\n\n"
            "This transcript records responses from the local `MOCK_LLM` app. "
            "The fabricated phone number used in the requests is omitted here; "
            "the stored document and JSONL records were checked for masking.\n\n"
            f"```json\n{json.dumps(report, indent=2, ensure_ascii=False)}\n```\n",
            encoding="utf-8",
        )
        return report
    finally:
        if temporary_document.exists():
            temporary_document.unlink()
            # Restore the index to the repository's checked-in knowledge base.
            build_indexes()


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, ensure_ascii=False))
