from query_engine.exceptions import (
    DataSourceConnectionError,
    DataSourcePermissionError,
    QueryTimeoutError,
)


def get_safe_error_message(exc: Exception) -> str:
    """Return a safe, user-facing message for a technical failure."""
    if isinstance(exc, DataSourceConnectionError):
        return (
            "Unable to connect to the project's data source. "
            "Check the connection and try again."
        )

    if isinstance(exc, DataSourcePermissionError):
        return (
            "The database user no longer has the required permissions. "
            "Check the data source permissions."
        )

    if isinstance(exc, QueryTimeoutError):
        return "The query took too long to execute. Try a more specific question."

    return "Unable to process your question. Please try again."
