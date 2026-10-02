import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Format application log records as one JSON object per line."""

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
            "message": record.getMessage(),
        }

        for field in self.STRUCTURED_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
