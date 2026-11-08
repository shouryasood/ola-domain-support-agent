from __future__ import annotations

import re
from threading import Lock
from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from ola_support.agents.crew import run_support_crew
from ola_support.agents.memory import history_for
from ola_support.guardrails import input_guardrail, mask_phone_numbers
from ola_support.rag.indexing import KB_DIR, build_indexes
from ola_support.schemas import SupportResponse
from ola_support.api.logging_config import write_json_log

router = APIRouter()
_ADD_DOCUMENT_LOCK = Lock()
TICKET_ID_PATTERN = re.compile(r"\bTKT-\d{5}\b", re.IGNORECASE)


class AskRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    session_id: str | None = Field(default=None, max_length=100)


class AddDocumentRequest(BaseModel):
    document_id: str = Field(
        min_length=2,
        max_length=80,
        pattern=r"^[a-z0-9][a-z0-9_-]+$",
    )
    text: str = Field(min_length=50, max_length=20000)


class AddDocumentResponse(BaseModel):
    document_id: str
    message: str
    document_count: int
    fixed_chunk_count: int
    sentence_chunk_count: int


def process_query(query: str) -> tuple[SupportResponse, str]:
    """Mask and guard the input before sending it to the CrewAI crew."""
    guarded = input_guardrail(query)
    safe_query = guarded["masked_text"]

    if not query.strip():
        return (
            SupportResponse(
                answer="Please enter a support question.",
                fallback=True,
            ),
            safe_query,
        )

    if not guarded["allowed"]:
        return (
            SupportResponse(
                answer="I can’t process instructions that attempt to override safeguards.",
                fallback=True,
            ),
            safe_query,
        )

    response = run_support_crew(safe_query)
    return SupportResponse.model_validate(response), safe_query


def _write_document_and_rebuild(
    document_id: str,
    text: str,
) -> dict[str, int]:
    """Store one validated document and rebuild both Part 1 indexes."""
    with _ADD_DOCUMENT_LOCK:
        path = KB_DIR / f"{document_id}.md"
        if path.exists():
            raise FileExistsError(document_id)

        title = document_id.replace("_", " ").replace("-", " ").title()
        path.write_text(f"# {title}\n\n{text.strip()}\n", encoding="utf-8")

        return build_indexes()


def _query_with_session_context(query: str, history: Any) -> str:
    """Resolve a simple status follow-up using a ticket mentioned earlier."""
    if TICKET_ID_PATTERN.search(query):
        return query

    if not re.search(r"\b(status|progress)\b", query, re.IGNORECASE):
        return query

    prior_text = " ".join(str(message.content) for message in history.messages)
    ticket_ids = TICKET_ID_PATTERN.findall(prior_text)

    if not ticket_ids:
        return query

    ticket_id = ticket_ids[-1].upper()
    return f"What is the status of {ticket_id}? Follow-up question: {query}"


@router.post("/ask", response_model=SupportResponse)
async def ask(payload: AskRequest, request: Request) -> SupportResponse:
    # Set the safe log value before calling the crew, in case it raises.
    request.state.safe_request_text = mask_phone_numbers(payload.query)

    response, safe_query = await run_in_threadpool(
        process_query,
        payload.query,
    )
    request.state.safe_request_text = safe_query
    return response


@router.post("/add-document", response_model=AddDocumentResponse)
async def add_document(
    payload: AddDocumentRequest,
    request: Request,
) -> AddDocumentResponse:
    guarded = input_guardrail(payload.text)
    safe_text = guarded["masked_text"]

    # Store and log only the masked text.
    request.state.safe_request_text = (
        f"{payload.document_id}: {safe_text[:500]}"
    )

    if not guarded["allowed"]:
        raise HTTPException(
            status_code=400,
            detail="Document text failed the input guardrail.",
        )

    try:
        counts = await run_in_threadpool(
            _write_document_and_rebuild,
            payload.document_id,
            safe_text,
        )
    except FileExistsError:
        raise HTTPException(
            status_code=409,
            detail="A document with that ID already exists.",
        )

    return AddDocumentResponse(
        document_id=payload.document_id,
        message="Document saved and both indexes rebuilt.",
        **counts,
    )


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    session_id = websocket.query_params.get("session_id", "default")

    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", session_id):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    history = history_for(session_id)

    try:
        while True:
            raw_query = await websocket.receive_text()
            safe_query = mask_phone_numbers(raw_query)
            trace_id = __import__("uuid").uuid4().hex

            if len(raw_query) > 2000:
                write_json_log(
                    {
                        "trace_id": trace_id,
                        "endpoint": "/ws/chat",
                        "status_code": 413,
                        "duration_ms": 0,
                        "request_text": safe_query[:2000],
                    }
                )
                await websocket.send_json(
                    {
                        "error": "Message is too long.",
                        "trace_id": trace_id,
                    }
                )
                continue

            import time

            started = time.perf_counter()

            try:
                guarded = input_guardrail(raw_query)
                safe_query = guarded["masked_text"]

                if not guarded["allowed"]:
                    response = SupportResponse(
                        answer=(
                            "I can’t process instructions that attempt "
                            "to override safeguards."
                        ),
                        fallback=True,
                    )
                else:
                    effective_query = _query_with_session_context(
                        safe_query,
                        history,
                    )
                    response, _ = await run_in_threadpool(
                        process_query,
                        effective_query,
                    )

                history.add_user_message(safe_query)
                history.add_ai_message(response.answer)

                await websocket.send_json(
                    {
                        "trace_id": trace_id,
                        "response": response.model_dump(),
                    }
                )

                write_json_log(
                    {
                        "trace_id": trace_id,
                        "endpoint": "/ws/chat",
                        "status_code": 200,
                        "duration_ms": round(
                            (time.perf_counter() - started) * 1000,
                            2,
                        ),
                        "request_text": safe_query[:2000],
                    }
                )

            except Exception as exc:
                # Log the exception type only, not its message or request data.
                write_json_log(
                    {
                        "trace_id": trace_id,
                        "endpoint": "/ws/chat",
                        "status_code": 500,
                        "duration_ms": round(
                            (time.perf_counter() - started) * 1000,
                            2,
                        ),
                        "request_text": safe_query[:2000],
                        "error_type": type(exc).__name__,
                    }
                )
                await websocket.send_json(
                    {
                        "error": "The request could not be completed.",
                        "trace_id": trace_id,
                    }
                )

    except WebSocketDisconnect:
        # A client disconnect ends this connection’s loop; the app stays up.
        write_json_log(
            {
                "trace_id": __import__("uuid").uuid4().hex,
                "endpoint": "/ws/chat",
                "event": "client_disconnected",
                "status_code": 200,
                "duration_ms": 0,
                "request_text": "",
            }
        )
