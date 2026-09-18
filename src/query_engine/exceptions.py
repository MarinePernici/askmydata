class SQLGenerationError(Exception):
    """Raised when a generated SQL response cannot be interpreted."""


class SQLValidationError(Exception):
    """Raised when generated SQL fails validation."""


class ResultValidationError(Exception):
    """Raised when a query execution result fails validation."""


class QueryExecutionError(Exception):
    """Raised when a SQL query cannot be executed."""


class DataSourcePermissionError(QueryExecutionError):
    """Raised when the data source permissions prevent query execution."""


class QueryTimeoutError(QueryExecutionError):
    """Raised when a SQL query exceeds its execution timeout."""
