from query_engine.types import (
    QueryExecutionResult,
    ResultValidationResult,
)


class ResultValidator:
    """Validate query execution results before answer generation."""

    def validate(
        self,
        result: QueryExecutionResult,
    ) -> ResultValidationResult:
        column_count = len(result.columns)

        for row in result.rows:
            if len(row) != column_count:
                return ResultValidationResult(
                    is_valid=False,
                    error=(
                        "Query result row length does not match "
                        "the number of columns."
                    ),
                )

        return ResultValidationResult(
            is_valid=True,
            error=None,
        )