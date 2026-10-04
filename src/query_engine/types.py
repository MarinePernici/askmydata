from dataclasses import dataclass

from llm.types import LLMUsage


@dataclass(frozen=True)
class SQLGenerationResult:
    """Structured result of SQL generation."""

    sql: str
    explanation: str
    usage: LLMUsage


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


@dataclass(frozen=True)
class ResultValidationResult:
    """Result of query execution result validation."""

    is_valid: bool
    error: str | None = None


@dataclass(frozen=True)
class AnswerGenerationResult:
    """Natural-language answer generated from a query result."""

    answer: str
    usage: LLMUsage


@dataclass(frozen=True)
class QueryRunResult:
    """Result of a complete query processing run."""

    sql: str
    explanation: str
    execution: QueryExecutionResult
    answer: str
    usages: tuple[LLMUsage, ...] = ()


@dataclass(frozen=True)
class ConversationMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ClarificationResult:
    question: str
    usages: tuple[LLMUsage, ...] = ()


@dataclass(frozen=True)
class CannotAnswerResult:
    """The question cannot be answered from the available project data."""

    usages: tuple[LLMUsage, ...] = ()
