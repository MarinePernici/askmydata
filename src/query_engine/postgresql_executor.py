import psycopg

from connectors.postgresql import PostgreSQLConnectionConfig
from query_engine.exceptions import (
    DataSourceConnectionError,
    DataSourcePermissionError,
    QueryTimeoutError,
)
from query_engine.query_executor import QueryExecutor
from query_engine.types import QueryExecutionResult


class PostgreSQLQueryExecutor(QueryExecutor):
    """Execute read-only SQL queries against PostgreSQL."""

    def __init__(
        self,
        config: PostgreSQLConnectionConfig,
        max_rows: int = 1000,
        timeout_ms: int = 30_000,
    ) -> None:
        if max_rows <= 0:
            raise ValueError("max_rows must be greater than zero.")

        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero.")

        self._config = config
        self._max_rows = max_rows
        self._timeout_ms = timeout_ms

    def execute(self, sql: str) -> QueryExecutionResult:
        try:
            with (
                psycopg.connect(
                    host=self._config.host,
                    port=self._config.port,
                    dbname=self._config.database,
                    user=self._config.user,
                    password=self._config.password,
                ) as connection,
                connection.cursor() as cursor,
            ):
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute(
                    "SELECT set_config('statement_timeout', %s, true)",
                    (str(self._timeout_ms),),
                )
                cursor.execute(sql)

                columns = tuple(description.name for description in cursor.description)
                rows = tuple(cursor.fetchmany(self._max_rows))

        except psycopg.errors.InsufficientPrivilege as exc:
            raise DataSourcePermissionError(
                "The database user does not have the required permissions."
            ) from exc
        except psycopg.errors.QueryCanceled as exc:
            raise QueryTimeoutError(
                "The query exceeded the configured execution timeout."
            ) from exc
        except psycopg.OperationalError as exc:
            raise DataSourceConnectionError(
                "Unable to connect to the configured data source."
            ) from exc

        return QueryExecutionResult(
            columns=columns,
            rows=rows,
        )
