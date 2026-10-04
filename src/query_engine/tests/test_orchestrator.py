import unittest

from catalog.types import KnowledgeCatalog
from llm.types import LLMUsage
from query_engine.exceptions import ResultValidationError, SQLValidationError
from query_engine.orchestrator import QueryOrchestrator
from query_engine.types import (
    AnswerGenerationResult,
    CannotAnswerResult,
    ClarificationResult,
    ConversationMessage,
    QueryExecutionResult,
    ResultValidationResult,
    SQLGenerationResult,
    SQLValidationResult,
)

SQL_USAGE = LLMUsage(
    model="fake-model",
    prompt_tokens=100,
    completion_tokens=20,
)

ANSWER_USAGE = LLMUsage(
    model="fake-model",
    prompt_tokens=50,
    completion_tokens=10,
)


class FakeGenerator:
    def generate(self, question, catalog, history=()):
        return SQLGenerationResult(
            sql="SELECT 1 AS value;",
            explanation="Returns one value.",
            usage=SQL_USAGE,
        )


class FakeValidator:
    def validate(self, sql, catalog=None):
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
            usage=ANSWER_USAGE,
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


class RecordingValidator:
    def __init__(self):
        self.catalog = None

    def validate(self, sql, catalog=None):
        self.catalog = catalog
        return SQLValidationResult(
            is_valid=True,
            error=None,
        )


class RejectingValidator:
    def validate(self, sql, catalog=None):
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
            usage=ANSWER_USAGE,
        )


class RecordingTracer:
    def __init__(self):
        self.events = []

    def record(
        self,
        step,
        status,
        duration_ms,
        started_at,
        completed_at,
        error_code="",
        error_message="",
        technical_metadata=None,
    ):
        self.events.append(
            {
                "step": step,
                "status": status,
                "duration_ms": duration_ms,
                "started_at": started_at,
                "completed_at": completed_at,
                "error_code": error_code,
                "error_message": error_message,
                "technical_metadata": technical_metadata or {},
            }
        )


class FailingGenerator:
    def generate(self, question, catalog, history=()):
        raise RuntimeError("LLM unavailable")


class RecordingGenerator:
    def __init__(self):
        self.history = None

    def generate(
        self,
        question,
        catalog,
        history=(),
    ):
        self.history = history

        return SQLGenerationResult(
            sql="SELECT 1;",
            explanation="Test query.",
            usage=SQL_USAGE,
        )


class ClarificationGenerator:
    def generate(
        self,
        question,
        catalog,
        history=(),
    ):
        return ClarificationResult(
            question="Which date range should I use?",
            usages=(SQL_USAGE,),
        )


class CannotAnswerGenerator:
    def generate(
        self,
        question,
        catalog,
        history=(),
    ):
        return CannotAnswerResult(
            usages=(SQL_USAGE,),
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
        self.assertEqual(
            result.usages,
            (SQL_USAGE, ANSWER_USAGE),
        )

    def test_run_does_not_execute_invalid_sql(self):
        executor = RecordingExecutor()
        tracer = RecordingTracer()

        orchestrator = QueryOrchestrator(
            generator=FakeGenerator(),
            validator=RejectingValidator(),
            executor=executor,
            tracer=tracer,
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
        )

        with self.assertRaises(SQLValidationError):
            orchestrator.run(
                question="Delete all orders.",
                catalog=KnowledgeCatalog(tables=()),
            )

        self.assertFalse(executor.called)

        self.assertEqual(len(tracer.events), 2)

        sql_validation_event = tracer.events[1]

        self.assertEqual(sql_validation_event["step"], "sql_validation")
        self.assertEqual(sql_validation_event["status"], "completed")
        self.assertEqual(
            sql_validation_event["technical_metadata"],
            {
                "sql": "SELECT 1 AS value;",
                "is_valid": False,
                "validation_error": "Only SELECT queries are allowed.",
            },
        )

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

    def test_orchestrator_traces_all_successful_steps(self):
        tracer = RecordingTracer()

        orchestrator = QueryOrchestrator(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor=FakeExecutor(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            tracer=tracer,
        )

        orchestrator.run(
            question="How many orders are there?",
            catalog=KnowledgeCatalog(tables=()),
        )

        self.assertEqual(len(tracer.events), 5)

        self.assertEqual(
            [event["step"] for event in tracer.events],
            [
                "sql_generation",
                "sql_validation",
                "query_execution",
                "result_validation",
                "answer_generation",
            ],
        )

        sql_validation_event = tracer.events[1]

        self.assertEqual(
            sql_validation_event["technical_metadata"],
            {
                "sql": "SELECT 1 AS value;",
                "is_valid": True,
                "validation_error": None,
            },
        )

        self.assertTrue(all(event["status"] == "completed" for event in tracer.events))

        self.assertTrue(all(event["duration_ms"] >= 0 for event in tracer.events))

        self.assertTrue(all(event["started_at"] is not None for event in tracer.events))
        self.assertTrue(
            all(event["completed_at"] is not None for event in tracer.events)
        )
        self.assertTrue(
            all(event["completed_at"] >= event["started_at"] for event in tracer.events)
        )

    def test_orchestrator_traces_failed_sql_generation(self):
        tracer = RecordingTracer()

        orchestrator = QueryOrchestrator(
            generator=FailingGenerator(),
            validator=FakeValidator(),
            executor=FakeExecutor(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            tracer=tracer,
        )

        with self.assertRaises(RuntimeError):
            orchestrator.run(
                question="How many orders are there?",
                catalog=KnowledgeCatalog(tables=()),
            )

        self.assertEqual(len(tracer.events), 1)

        event = tracer.events[0]

        self.assertEqual(event["step"], "sql_generation")
        self.assertEqual(event["status"], "failed")
        self.assertEqual(event["error_code"], "RuntimeError")
        self.assertEqual(event["error_message"], "LLM unavailable")
        self.assertGreaterEqual(event["duration_ms"], 0)
        self.assertIsNotNone(event["started_at"])
        self.assertIsNotNone(event["completed_at"])
        self.assertGreaterEqual(
            event["completed_at"],
            event["started_at"],
        )

    def test_history_is_forwarded_to_sql_generator(self):
        history = (
            ConversationMessage(
                role="user",
                content="Previous question",
            ),
            ConversationMessage(
                role="assistant",
                content="Previous answer",
            ),
        )

        generator = RecordingGenerator()

        orchestrator = QueryOrchestrator(
            generator=generator,
            validator=FakeValidator(),
            executor=FakeExecutor(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
        )

        orchestrator.run(
            question="Current question",
            catalog=KnowledgeCatalog(tables=()),
            history=history,
        )

        self.assertEqual(
            generator.history,
            history,
        )

    def test_run_returns_clarification_without_executing_query(self):
        executor = RecordingExecutor()

        orchestrator = QueryOrchestrator(
            generator=ClarificationGenerator(),
            validator=FakeValidator(),
            executor=executor,
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
        )

        result = orchestrator.run(
            question="How many recent orders are there?",
            catalog=KnowledgeCatalog(tables=()),
        )

        self.assertEqual(
            result,
            ClarificationResult(
                question="Which date range should I use?",
                usages=(SQL_USAGE,),
            ),
        )

        self.assertFalse(executor.called)

    def test_clarification_traces_only_sql_generation(self):
        tracer = RecordingTracer()

        orchestrator = QueryOrchestrator(
            generator=ClarificationGenerator(),
            validator=FakeValidator(),
            executor=FakeExecutor(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            tracer=tracer,
        )

        orchestrator.run(
            question="How many recent orders are there?",
            catalog=KnowledgeCatalog(tables=()),
        )

        self.assertEqual(len(tracer.events), 1)

        self.assertEqual(
            tracer.events[0]["step"],
            "sql_generation",
        )
        self.assertEqual(
            tracer.events[0]["status"],
            "completed",
        )

    def test_run_returns_cannot_answer_without_executing_query(self):
        executor = RecordingExecutor()

        orchestrator = QueryOrchestrator(
            generator=CannotAnswerGenerator(),
            validator=FakeValidator(),
            executor=executor,
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
        )

        result = orchestrator.run(
            question="What is the capital of Italy?",
            catalog=KnowledgeCatalog(tables=()),
        )

        self.assertEqual(
            result,
            CannotAnswerResult(
                usages=(SQL_USAGE,),
            ),
        )

        self.assertFalse(executor.called)

    def test_cannot_answer_traces_only_sql_generation(self):
        tracer = RecordingTracer()

        orchestrator = QueryOrchestrator(
            generator=CannotAnswerGenerator(),
            validator=FakeValidator(),
            executor=FakeExecutor(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            tracer=tracer,
        )

        orchestrator.run(
            question="What is the capital of Italy?",
            catalog=KnowledgeCatalog(tables=()),
        )

        self.assertEqual(len(tracer.events), 1)
        self.assertEqual(
            tracer.events[0]["step"],
            "sql_generation",
        )
        self.assertEqual(
            tracer.events[0]["status"],
            "completed",
        )

    def test_catalog_is_forwarded_to_sql_validator(self):
        validator = RecordingValidator()
        catalog = KnowledgeCatalog(tables=())

        orchestrator = QueryOrchestrator(
            generator=FakeGenerator(),
            validator=validator,
            executor=FakeExecutor(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
        )

        orchestrator.run(
            question="Return one.",
            catalog=catalog,
        )

        self.assertIs(validator.catalog, catalog)


if __name__ == "__main__":
    unittest.main()
