from abc import ABC, abstractmethod

from query_engine.types import QueryExecutionResult


class QueryExecutor(ABC):
    """Abstract interface for executing validated read-only SQL."""

    @abstractmethod
    def execute(self, sql: str) -> QueryExecutionResult:
        """Execute a validated read-only SQL query."""
        raise NotImplementedError