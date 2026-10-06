from django.utils.translation import gettext as _

from query_engine.exceptions import (
    DataSourceConnectionError,
    DataSourcePermissionError,
    QueryTimeoutError,
)


def get_safe_interface_error_message(exc: Exception) -> str:
    """Return a safe, translated error message for the user interface."""
    if isinstance(exc, DataSourceConnectionError):
        return _(
            "Unable to connect to the project's data source. "
            "Check the connection and try again."
        )

    if isinstance(exc, DataSourcePermissionError):
        return _(
            "The database user no longer has the required permissions. "
            "Check the data source permissions."
        )

    if isinstance(exc, QueryTimeoutError):
        return _("The query took too long to execute. Try a more specific question.")

    return _("Unable to process your question. Please try again.")


def get_safe_conversation_error_message(exc: Exception) -> str:
    """Return a safe error message intended for conversation content."""
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
