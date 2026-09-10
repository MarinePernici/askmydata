import os
import unittest
import psycopg
import environ

from connectors.postgresql import PostgreSQLConnectionConfig
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

        with self.assertRaises(psycopg.errors.QueryCanceled):
            executor.execute(
                "SELECT pg_sleep(1);"
            )



if __name__ == "__main__":
    unittest.main()