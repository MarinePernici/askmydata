import os
import unittest
from unittest.mock import patch

import environ
import psycopg

from connectors.postgresql import PostgreSQLConnectionConfig
from query_engine.exceptions import (
    DataSourceConnectionError,
    DataSourcePermissionError,
    QueryTimeoutError,
)
from query_engine.postgresql_executor import PostgreSQLQueryExecutor

ROOT_DIR = environ.Path(__file__) - 4
environ.Env.read_env(ROOT_DIR(".env"))


class PostgreSQLQueryExecutorTests(unittest.TestCase):
    def setUp(self):
        self.config = PostgreSQLConnectionConfig(
            host=os.environ["TEST_SOURCE_DB_HOST"],
            port=int(os.environ["TEST_SOURCE_DB_PORT"]),
            database=os.environ["TEST_SOURCE_DB_NAME"],
            user=os.environ["TEST_SOURCE_DB_USER"],
            password=os.environ["TEST_SOURCE_DB_PASSWORD"],
        )

    def test_executes_select_query(self):
        executor = PostgreSQLQueryExecutor(self.config)

        result = executor.execute(
            """
            SELECT id, amount
            FROM sales.orders
            ORDER BY id
            """
        )

        self.assertEqual(
            result.columns,
            ("id", "amount"),
        )

    def test_executes_scalar_query(self):
        executor = PostgreSQLQueryExecutor(self.config)

        result = executor.execute("SELECT 1 AS value;")

        self.assertEqual(result.columns, ("value",))
        self.assertEqual(result.rows, ((1,),))

    def test_limits_number_of_returned_rows(self):
        executor = PostgreSQLQueryExecutor(
            self.config,
            max_rows=2,
        )

        result = executor.execute(
            """
            SELECT value
            FROM generate_series(1, 10) AS value
            ORDER BY value;
            """
        )

        self.assertEqual(
            result.rows,
            ((1,), (2,)),
        )

    def test_rejects_non_positive_max_rows(self):
        with self.assertRaises(ValueError):
            PostgreSQLQueryExecutor(
                self.config,
                max_rows=0,
            )

    def test_rejects_non_positive_timeout(self):
        with self.assertRaises(ValueError):
            PostgreSQLQueryExecutor(
                self.config,
                timeout_ms=0,
            )

    def test_cancels_query_when_timeout_is_exceeded(self):
        executor = PostgreSQLQueryExecutor(
            self.config,
            timeout_ms=100,
        )

        with self.assertRaises(QueryTimeoutError):
            executor.execute("SELECT pg_sleep(1);")

    def test_executes_queries_in_read_only_transaction(self):
        executor = PostgreSQLQueryExecutor(self.config)

        result = executor.execute(
            "SELECT current_setting('transaction_read_only') AS read_only;"
        )

        self.assertEqual(result.rows, (("on",),))

    def test_read_only_transaction_blocks_write_with_writable_user(self):
        writable_config = PostgreSQLConnectionConfig(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=os.environ["TEST_WRITABLE_DB_USER"],
            password=os.environ["TEST_WRITABLE_DB_PASSWORD"],
        )

        executor = PostgreSQLQueryExecutor(writable_config)

        with self.assertRaises(psycopg.errors.ReadOnlySqlTransaction):
            executor.execute(
                """
                INSERT INTO sales.customers (name, email)
                VALUES ('Unauthorized', 'unauthorized@example.com')
                """
            )

    def test_translates_permission_error(self):
        executor = PostgreSQLQueryExecutor(self.config)

        with (
            patch(
                "query_engine.postgresql_executor.psycopg.connect",
                side_effect=psycopg.errors.InsufficientPrivilege(
                    "permission denied for table customers"
                ),
            ),
            self.assertRaises(DataSourcePermissionError),
        ):
            executor.execute("SELECT * FROM sales.customers")

    def test_translates_query_timeout_error(self):
        executor = PostgreSQLQueryExecutor(self.config)

        with (
            patch(
                "query_engine.postgresql_executor.psycopg.connect",
                side_effect=psycopg.errors.QueryCanceled(
                    "canceling statement due to statement timeout"
                ),
            ),
            self.assertRaises(QueryTimeoutError),
        ):
            executor.execute("SELECT * FROM sales.customers")

    def test_translates_connection_error(self):
        executor = PostgreSQLQueryExecutor(self.config)

        with (
            patch(
                "query_engine.postgresql_executor.psycopg.connect",
                side_effect=psycopg.OperationalError(
                    "connection to server failed: sensitive details"
                ),
            ),
            self.assertRaises(DataSourceConnectionError) as context,
        ):
            executor.execute("SELECT * FROM sales.customers")

        self.assertEqual(
            str(context.exception),
            "Unable to connect to the configured data source.",
        )

    def test_translates_real_permission_error(self):
        noselect_config = PostgreSQLConnectionConfig(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=os.environ["TEST_NOSELECT_DB_USER"],
            password=os.environ["TEST_NOSELECT_DB_PASSWORD"],
        )

        executor = PostgreSQLQueryExecutor(noselect_config)

        with self.assertRaises(DataSourcePermissionError):
            executor.execute("SELECT * FROM sales.customers")


if __name__ == "__main__":
    unittest.main()
