from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request

from ola_support.api.logging_config import write_json_log
from ola_support.api.routes import router

app = FastAPI(
    title="Ola Domain Support Agent",
    version="1.0.0",
)

app.include_router(router)


@app.middleware("http")
async def log_http_request(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID") or uuid.uuid4().hex
    request.state.trace_id = trace_id
    request.state.safe_request_text = ""

    started = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception as exc:
        write_json_log(
            {
                "trace_id": trace_id,
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": 500,
                "duration_ms": round(
                    (time.perf_counter() - started) * 1000,
                    2,
                ),
                "request_text": request.state.safe_request_text,
                "error_type": type(exc).__name__,
            }
        )
        raise

    response.headers["X-Trace-ID"] = trace_id

    write_json_log(
        {
            "trace_id": trace_id,
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(
                (time.perf_counter() - started) * 1000,
                2,
            ),
            "request_text": request.state.safe_request_text,
        }
    )

    return response
