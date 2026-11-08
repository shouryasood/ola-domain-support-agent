from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from threading import Lock
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOG_PATH = PROJECT_ROOT / "logs" / "api_requests.jsonl"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("ola_support.api.jsonl")
_logger.setLevel(logging.INFO)
_logger.propagate = False

if not _logger.handlers:
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(handler)

_lock = Lock()


def write_json_log(event: dict[str, Any]) -> None:
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))

    with _lock:
        _logger.info(line)
