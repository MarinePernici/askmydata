from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter
from typing import TypeVar

from catalog.types import KnowledgeCatalog
from config.observability import traced_operation
from query_engine.exceptions import ResultValidationError, SQLValidationError
from query_engine.tracer import NullQueryTracer, QueryTracer
from query_engine.types import (
    CannotAnswerResult,
    ClarificationResult,
    ConversationMessage,
    QueryRunResult,
)

T = TypeVar("T")


class QueryOrchestrator:
    """Orchestrate SQL generation, validation, and execution."""

    def __init__(
        self,
        generator,
        validator,
        executor,
        result_validator,
        answer_generator,
        tracer: QueryTracer | None = None,
    ) -> None:
        self._generator = generator
        self._validator = validator
        self._executor = executor
        self._result_validator = result_validator
        self._answer_generator = answer_generator
        self._tracer = tracer or NullQueryTracer()

    def run(
        self,
        question: str,
        catalog: KnowledgeCatalog,
        history: tuple[ConversationMessage, ...] = (),
    ) -> QueryRunResult | ClarificationResult | CannotAnswerResult:
        generation_result = self._run_traced_step(
            step="sql_generation",
            operation=lambda: self._generator.generate(
                question=question,
                catalog=catalog,
                history=history,
            ),
        )

        if isinstance(generation_result, ClarificationResult):
            return generation_result

        if isinstance(generation_result, CannotAnswerResult):
            return generation_result

        validation_result = self._run_traced_step(
            step="sql_validation",
            operation=lambda: self._validator.validate(
                generation_result.sql,
                catalog=catalog,
            ),
            metadata_factory=lambda result: {
                "sql": generation_result.sql,
                "is_valid": result.is_valid,
                "validation_error": result.error,
            },
        )

        if not validation_result.is_valid:
            raise SQLValidationError(
                validation_result.error or "SQL validation failed."
            )

        execution_result = self._run_traced_step(
            step="query_execution",
            operation=lambda: self._executor.execute(generation_result.sql),
        )

        result_validation = self._run_traced_step(
            step="result_validation",
            operation=lambda: self._result_validator.validate(execution_result),
        )

        if not result_validation.is_valid:
            raise ResultValidationError(
                result_validation.error or "Query result validation failed."
            )

        answer_result = self._run_traced_step(
            step="answer_generation",
            operation=lambda: self._answer_generator.generate(
                question=question,
                sql=generation_result.sql,
                result=execution_result,
            ),
        )

        return QueryRunResult(
            sql=generation_result.sql,
            explanation=generation_result.explanation,
            execution=execution_result,
            answer=answer_result.answer,
            usages=(
                generation_result.usage,
                answer_result.usage,
            ),
        )

    def _run_traced_step(
        self,
        step: str,
        operation: Callable[[], T],
        metadata_factory: Callable[[T], dict[str, object]] | None = None,
    ) -> T:
        started_at = datetime.now(UTC)
        started_counter = perf_counter()

        try:
            with traced_operation(
                step,
                attributes={"pipeline_step": step},
            ):
                result = operation()
        except Exception as exc:
            completed_at = datetime.now(UTC)
            duration_ms = int((perf_counter() - started_counter) * 1000)

            self._tracer.record(
                step=step,
                status="failed",
                duration_ms=duration_ms,
                started_at=started_at,
                completed_at=completed_at,
                error_code=exc.__class__.__name__,
                error_message=str(exc),
            )

            raise

        completed_at = datetime.now(UTC)
        duration_ms = int((perf_counter() - started_counter) * 1000)

        self._tracer.record(
            step=step,
            status="completed",
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
            technical_metadata=metadata_factory(result) if metadata_factory else None,
        )

        return result
