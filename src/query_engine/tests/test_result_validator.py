import unittest

from query_engine.result_validator import ResultValidator
from query_engine.types import QueryExecutionResult


class ResultValidatorTests(unittest.TestCase):
    def test_validator_can_be_created(self):
        validator = ResultValidator()

        self.assertIsNotNone(validator)

    def test_accepts_consistent_result(self):
        validator = ResultValidator()

        result = validator.validate(
            QueryExecutionResult(
                columns=("id", "amount"),
                rows=(
                    (1, 10.50),
                    (2, 25.00),
                ),
            )
        )

        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error)

    def test_accepts_empty_result(self):
        validator = ResultValidator()

        result = validator.validate(
            QueryExecutionResult(
                columns=("id", "amount"),
                rows=(),
            )
        )

        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error)

    def test_rejects_row_with_wrong_number_of_values(self):
        validator = ResultValidator()

        result = validator.validate(
            QueryExecutionResult(
                columns=("id", "amount"),
                rows=(
                    (1, 10.50),
                    (2,),
                ),
            )
        )

        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.error,
            ("Query result row length does not match the number of columns."),
        )


if __name__ == "__main__":
    unittest.main()
