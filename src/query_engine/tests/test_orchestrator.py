import unittest

from catalog.types import KnowledgeCatalog
from query_engine.exceptions import ResultValidationError, SQLValidationError
from query_engine.orchestrator import QueryOrchestrator
from query_engine.types import (
    QueryExecutionResult,
    ResultValidationResult,
    SQLGenerationResult,
    SQLValidationResult,
    AnswerGenerationResult,
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


class FakeAnswerGenerator:
    def generate(self, question, sql, result):
        return AnswerGenerationResult(
            answer="There is one value.",
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


class RecordingAnswerGenerator:
    def __init__(self):
        self.called = False

    def generate(self, question, sql, result):
        self.called = True
        return AnswerGenerationResult(
            answer="This should not be generated.",
        )


class QueryOrchestratorTests(unittest.TestCase):
    def test_orchestrator_can_be_created(self):
        orchestrator = QueryOrchestrator(
            generator=None,
            validator=None,
            executor=None,
            result_validator=None,
            answer_generator=None,
        )

        self.assertIsNotNone(orchestrator)

    def test_run_generates_validates_and_executes_query(self):
        orchestrator = QueryOrchestrator(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor=FakeExecutor(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
        )

        result = orchestrator.run(
            question="Return one.",
            catalog=KnowledgeCatalog(tables=()),
        )

        self.assertEqual(
            result.sql,
            "SELECT 1 AS value;",
        )
        self.assertEqual(
            result.explanation,
            "Returns one value.",
        )
        self.assertEqual(
            result.execution.columns,
            ("value",),
        )
        self.assertEqual(
            result.execution.rows,
            ((1,),),
        )
        self.assertEqual(
            result.answer,
            "There is one value.",
        )

    def test_run_does_not_execute_invalid_sql(self):
        executor = RecordingExecutor()

        orchestrator = QueryOrchestrator(
            generator=FakeGenerator(),
            validator=RejectingValidator(),
            executor=executor,
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
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
            answer_generator=FakeAnswerGenerator(),
        )

        with self.assertRaises(ResultValidationError):
            orchestrator.run(
                question="Return one.",
                catalog=KnowledgeCatalog(tables=()),
            )

    def test_run_does_not_generate_answer_for_invalid_query_result(self):
        answer_generator = RecordingAnswerGenerator()

        orchestrator = QueryOrchestrator(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor=FakeExecutor(),
            result_validator=RejectingResultValidator(),
            answer_generator=answer_generator,
        )

        with self.assertRaises(ResultValidationError):
            orchestrator.run(
                question="Return one.",
                catalog=KnowledgeCatalog(tables=()),
            )

        self.assertFalse(answer_generator.called)

if __name__ == "__main__":
    unittest.main()