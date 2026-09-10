from catalog.types import KnowledgeCatalog
from query_engine.exceptions import SQLValidationError, ResultValidationError
from query_engine.query_executor import QueryExecutor
from query_engine.sql_generator import SQLGenerator
from query_engine.sql_validator import SQLValidator
from query_engine.types import QueryExecutionResult
from query_engine.result_validator import ResultValidator


class QueryOrchestrator:
    """Orchestrate SQL generation, validation, and execution."""

    def __init__(
        self,
        generator: SQLGenerator,
        validator: SQLValidator,
        executor: QueryExecutor,
        result_validator: ResultValidator,
    ) -> None:
        self._generator = generator
        self._validator = validator
        self._executor = executor
        self._result_validator = result_validator

    def run(
        self,
        question: str,
        catalog: KnowledgeCatalog,
    ) -> QueryExecutionResult:
        generation_result = self._generator.generate(
            question=question,
            catalog=catalog,
        )

        validation_result = self._validator.validate(
            generation_result.sql
        )

        if not validation_result.is_valid:
            raise SQLValidationError(
                validation_result.error or "SQL validation failed."
            )

        execution_result = self._executor.execute(
            generation_result.sql
        )

        result_validation = self._result_validator.validate(
            execution_result
        )

        if not result_validation.is_valid:
            raise ResultValidationError(
                result_validation.error or "Query result validation failed."
            )

        return execution_result