from collections.abc import Callable
from time import perf_counter
from typing import TypeVar

from catalog.types import KnowledgeCatalog
from query_engine.exceptions import ResultValidationError, SQLValidationError
from query_engine.tracer import NullQueryTracer, QueryTracer
from query_engine.types import (
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
    ) -> QueryRunResult | ClarificationResult:
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

        validation_result = self._run_traced_step(
            step="sql_validation",
            operation=lambda: self._validator.validate(
                generation_result.sql
            ),
        )

        if not validation_result.is_valid:
            raise SQLValidationError(
                validation_result.error or "SQL validation failed."
            )

        execution_result = self._run_traced_step(
            step="query_execution",
            operation=lambda: self._executor.execute(
                generation_result.sql
            ),
        )

        result_validation = self._run_traced_step(
            step="result_validation",
            operation=lambda: self._result_validator.validate(
                execution_result
            ),
        )

        if not result_validation.is_valid:
            raise ResultValidationError(
                result_validation.error
                or "Query result validation failed."
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
        )

    def _run_traced_step(
        self,
        step: str,
        operation: Callable[[], T],
    ) -> T:
        started_at = perf_counter()

        try:
            result = operation()
        except Exception as exc:
            duration_ms = int(
                (perf_counter() - started_at) * 1000
            )

            self._tracer.record(
                step=step,
                status="failed",
                duration_ms=duration_ms,
                error_code=exc.__class__.__name__,
                error_message=str(exc),
            )

            raise

        duration_ms = int(
            (perf_counter() - started_at) * 1000
        )

        self._tracer.record(
            step=step,
            status="completed",
            duration_ms=duration_ms,
        )

        return result