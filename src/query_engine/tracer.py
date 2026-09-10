from abc import ABC, abstractmethod


class QueryTracer(ABC):
    @abstractmethod
    def record(
        self,
        step: str,
        status: str,
        duration_ms: int,
        error_code: str = "",
        error_message: str = "",
    ) -> None:
        raise NotImplementedError


class NullQueryTracer(QueryTracer):
    """Tracer that intentionally discards all trace events."""

    def record(
        self,
        step: str,
        status: str,
        duration_ms: int,
        error_code: str = "",
        error_message: str = "",
    ) -> None:
        pass