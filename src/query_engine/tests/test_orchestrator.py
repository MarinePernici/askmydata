import unittest

from catalog.types import KnowledgeCatalog
from query_engine.exceptions import ResultValidationError, SQLValidationError
from query_engine.orchestrator import QueryOrchestrator
from query_engine.types import (
    QueryExecutionResult,
    ResultValidationResult,
    SQLGenerationResult,
    SQLValidationResult,
)

class FakeGenerator:
    def generate(self, question, catalog):
        return SQLGenerationResult(
            sql="SELECT 1 AS value;",
            explanation="Returns one value.",
        )


class FakeValidator:
    def validate(self, sql):
        return SQLValidationResult(
            is_valid=True,
            error=None,
        )


class FakeExecutor:
    def execute(self, sql):
        return QueryExecutionResult(
            columns=("value",),
            rows=((1,),),
        )


class FakeResultValidator:
    def validate(self, result):
        return ResultValidationResult(
            is_valid=True,
            error=None,
        )


class RecordingExecutor:
    def __init__(self):
        self.called = False

    def execute(self, sql):
        self.called = True
        return QueryExecutionResult(
            columns=(),
            rows=(),
        )


class RejectingValidator:
    def validate(self, sql):
        return SQLValidationResult(
            is_valid=False,
            error="Only SELECT queries are allowed.",
        )


class RejectingResultValidator:
    def validate(self, result):
        return ResultValidationResult(
            is_valid=False,
            error="Invalid query result.",
        )


class QueryOrchestratorTests(unittest.TestCase):
    def test_orchestrator_can_be_created(self):
        orchestrator = QueryOrchestrator(
            generator=None,
            validator=None,
            executor=None,
            result_validator=None,
        )

        self.assertIsNotNone(orchestrator)

    def test_run_generates_validates_and_executes_query(self):
        orchestrator = QueryOrchestrator(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor=FakeExecutor(),
            result_validator=FakeResultValidator(),
        )

        result = orchestrator.run(
            question="Return one.",
            catalog=KnowledgeCatalog(tables=()),
        )

        self.assertEqual(result.columns, ("value",))
        self.assertEqual(result.rows, ((1,),))

    def test_run_does_not_execute_invalid_sql(self):
        executor = RecordingExecutor()

        orchestrator = QueryOrchestrator(
            generator=FakeGenerator(),
            validator=RejectingValidator(),
            executor=executor,
            result_validator=FakeResultValidator(),
        )

        with self.assertRaises(SQLValidationError):
            orchestrator.run(
                question="Delete all orders.",
                catalog=KnowledgeCatalog(tables=()),
            )

        self.assertFalse(executor.called)

    def test_run_raises_error_for_invalid_query_result(self):
        orchestrator = QueryOrchestrator(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor=FakeExecutor(),
            result_validator=RejectingResultValidator(),
        )

        with self.assertRaises(ResultValidationError):
            orchestrator.run(
                question="Return one.",
                catalog=KnowledgeCatalog(tables=()),
            )

if __name__ == "__main__":
    unittest.main()