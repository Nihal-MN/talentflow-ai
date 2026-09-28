"""Structured logging.

Console output is human-friendly ``key=value`` lines; set ``LOG_FORMAT=json``
for line-delimited JSON (containers, log aggregators). We never log resume or
JD bodies — log ids, counts and durations instead. See SECURITY.md.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

#: Attributes present on every LogRecord; everything else is treated as
#: structured "extra" data supplied by the caller.
_STANDARD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys()) | {
    "message",
    "asctime",
    "taskName",
}


def _extras(record: logging.LogRecord) -> dict[str, Any]:
    return {key: value for key, value in record.__dict__.items() if key not in _STANDARD_ATTRS}


class KeyValueFormatter(logging.Formatter):
    """``2026-09-28T10:00:00Z INFO     talentflow.request: request method=GET ...``"""

    default_time_format = "%Y-%m-%dT%H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        base = (
            f"{self.formatTime(record, self.default_time_format)} "
            f"{record.levelname:<8} {record.name}: {record.getMessage()}"
        )
        extras = _extras(record)
        if extras:
            base += " " + " ".join(f"{key}={value}" for key, value in extras.items())
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


class JsonFormatter(logging.Formatter):
    """One JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": self.formatTime(record, KeyValueFormatter.default_time_format),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(_extras(record))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", *, json_output: bool | None = None) -> None:
    """Install a single stdout handler with the chosen format.

    ``json_output`` defaults to ``LOG_FORMAT=json`` from the environment.
    """
    if json_output is None:
        json_output = os.getenv("LOG_FORMAT", "").strip().lower() == "json"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if json_output else KeyValueFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    # The API logs requests itself (middleware) in our structured format;
    # silence uvicorn's duplicate access log.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
