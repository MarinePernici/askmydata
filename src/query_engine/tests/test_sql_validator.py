import unittest

from catalog.types import KnowledgeCatalog, TableMetadata
from query_engine.sql_validator import SQLValidator


class SQLValidatorTests(unittest.TestCase):
    def make_catalog(self):
        return KnowledgeCatalog(
            tables=(
                TableMetadata(
                    schema="sales",
                    name="orders",
                    columns=(),
                    relationships=(),
                ),
                TableMetadata(
                    schema="sales",
                    name="customers",
                    columns=(),
                    relationships=(),
                ),
            )
        )

    def test_validator_can_be_created(self):
        validator = SQLValidator()

        self.assertIsNotNone(validator)

    def test_accepts_select_query(self):
        validator = SQLValidator()

        result = validator.validate("SELECT id, amount FROM sales.orders;")

        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error)

    def test_rejects_invalid_sql(self):
        validator = SQLValidator()

        result = validator.validate("SELECT FROM WHERE;")

        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.error,
            "SQL query has invalid PostgreSQL syntax.",
        )

    def test_rejects_multiple_statements(self):
        validator = SQLValidator()

        result = validator.validate("SELECT 1; SELECT 2;")

        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.error,
            "Exactly one SQL statement is allowed.",
        )

    def test_rejects_delete_statement(self):
        validator = SQLValidator()

        result = validator.validate("DELETE FROM sales.orders;")

        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.error,
            "Only SELECT queries are allowed.",
        )

    def test_rejects_empty_query(self):
        validator = SQLValidator()

        result = validator.validate("   ")

        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.error,
            "SQL query is empty.",
        )

    def test_rejects_delete_inside_cte(self):
        validator = SQLValidator()

        result = validator.validate(
            """
            WITH deleted_orders AS (
                DELETE FROM sales.orders
                RETURNING id
            )
            SELECT * FROM deleted_orders;
            """
        )

        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.error,
            "Data-modifying operations are not allowed.",
        )

    def test_accepts_select_inside_cte(self):
        validator = SQLValidator()

        result = validator.validate(
            """
            WITH recent_orders AS (
                SELECT id, amount
                FROM sales.orders
            )
            SELECT * FROM recent_orders;
            """
        )

        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error)

    def test_accepts_table_in_catalog(self):
        validator = SQLValidator()

        result = validator.validate(
            "SELECT id FROM sales.orders;",
            catalog=self.make_catalog(),
        )

        self.assertTrue(result.is_valid)

    def test_rejects_table_outside_catalog(self):
        validator = SQLValidator()

        result = validator.validate(
            "SELECT * FROM private.secret;",
            catalog=self.make_catalog(),
        )

        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.error,
            "SQL query references a table outside the catalog scope.",
        )

    def test_rejects_out_of_scope_table_in_join(self):
        validator = SQLValidator()

        result = validator.validate(
            """
            SELECT orders.id
            FROM sales.orders
            JOIN private.secret
                ON private.secret.id = orders.id;
            """,
            catalog=self.make_catalog(),
        )

        self.assertFalse(result.is_valid)

    def test_accepts_cte_using_catalog_table(self):
        validator = SQLValidator()

        result = validator.validate(
            """
            WITH recent_orders AS (
                SELECT id
                FROM sales.orders
            )
            SELECT *
            FROM recent_orders;
            """,
            catalog=self.make_catalog(),
        )

        self.assertTrue(result.is_valid)
