import unittest

from query_engine.sql_validator import SQLValidator


class SQLValidatorTests(unittest.TestCase):
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
