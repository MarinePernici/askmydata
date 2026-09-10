from dataclasses import dataclass


@dataclass(frozen=True)
class SQLGenerationResult:
    """Structured result of SQL generation."""

    sql: str
    explanation: str


@dataclass(frozen=True)
class SQLValidationResult:
    """Result of SQL query validation."""

    is_valid: bool
    error: str | None = None


@dataclass(frozen=True)
class QueryExecutionResult:
    """Result returned after executing a read-only SQL query."""

    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]