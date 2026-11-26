import json
import logging
import re
from datetime import UTC, datetime

from opentelemetry import trace


class JsonFormatter(logging.Formatter):
    """Format application log records as one JSON object per line."""

    INVITATION_TOKEN_PATTERN = re.compile(r"(/auth/register/)[^/\s?#]+")

    STRUCTURED_FIELDS = (
        "event",
        "project_id",
        "question_run_id",
        "connection_status",
        "catalog_version",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=UTC,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": self.INVITATION_TOKEN_PATTERN.sub(
                r"\g<1>[REDACTED]",
                record.getMessage(),
            ),
        }

        try:
            span = trace.get_current_span()
            span_context = span.get_span_context()

            if span_context.is_valid:
                payload["trace_id"] = format(span_context.trace_id, "032x")
                payload["span_id"] = format(span_context.span_id, "016x")
        except Exception:  # noqa: BLE001, S110
            pass

        for field in self.STRUCTURED_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info and record.exc_info[0] is not None:
            payload["exception_type"] = record.exc_info[0].__name__

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
