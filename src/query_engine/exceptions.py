class SQLGenerationError(Exception):
    """Raised when a generated SQL response cannot be interpreted."""


class SQLValidationError(Exception):
    """Raised when generated SQL fails validation."""


class ResultValidationError(Exception):
    """Raised when a query execution result fails validation."""