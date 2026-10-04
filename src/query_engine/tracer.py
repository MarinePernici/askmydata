from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class QueryTracer(ABC):
    @abstractmethod
    def record(
        self,
        step: str,
        status: str,
        duration_ms: int,
        started_at: datetime,
        completed_at: datetime,
        error_code: str = "",
        error_message: str = "",
        technical_metadata: dict[str, Any] | None = None,
    ) -> None:
        raise NotImplementedError


class NullQueryTracer(QueryTracer):
    """Tracer that intentionally discards all trace events."""

    def record(
        self,
        step: str,
        status: str,
        duration_ms: int,
        started_at: datetime,
        completed_at: datetime,
        error_code: str = "",
        error_message: str = "",
        technical_metadata: dict[str, Any] | None = None,
    ) -> None:
        pass
