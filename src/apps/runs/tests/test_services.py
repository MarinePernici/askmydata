from django.test import TestCase

from apps.projects.models import Project
from apps.runs.models import ExecutionTrace, QuestionRun
from apps.runs.services import QuestionRunService
from catalog.types import KnowledgeCatalog
from query_engine.types import (
    AnswerGenerationResult,
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
        return SQLValidationResult(is_valid=True)


class FakeExecutor:
    def execute(self, sql):
        return QueryExecutionResult(
            columns=("value",),
            rows=((1,),),
        )


class FakeResultValidator:
    def validate(self, result):
        return ResultValidationResult(is_valid=True)


class FakeAnswerGenerator:
    def generate(self, question, sql, result):
        return AnswerGenerationResult(
            answer="There is one value.",
        )


class FailingGenerator:
    def generate(self, question, catalog):
        raise RuntimeError("LLM unavailable")


class QuestionRunServiceTests(TestCase):
    def test_successful_run_is_persisted(self):
        project = Project.objects.create(name="Test project")

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor=FakeExecutor(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
        )

        result = service.run(
            project=project,
            question="Return one.",
            catalog=KnowledgeCatalog(tables=()),
        )

        run = QuestionRun.objects.get()

        self.assertEqual(run.status, QuestionRun.Status.COMPLETED)
        self.assertIsNotNone(run.started_at)
        self.assertIsNotNone(run.completed_at)
        self.assertEqual(run.row_count, 1)

        self.assertEqual(result.answer, "There is one value.")

        self.assertEqual(
            ExecutionTrace.objects.filter(
                question_run=run
            ).count(),
            5,
        )

    def test_failed_run_is_persisted(self):
        project = Project.objects.create(
            name="Test project",
        )

        service = QuestionRunService(
            generator=FailingGenerator(),
            validator=FakeValidator(),
            executor=FakeExecutor(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
        )

        with self.assertRaises(RuntimeError):
            service.run(
                project=project,
                question="Return one.",
                catalog=KnowledgeCatalog(tables=()),
            )

        run = QuestionRun.objects.get()

        self.assertEqual(
            run.status,
            QuestionRun.Status.FAILED,
        )
        self.assertIsNotNone(run.started_at)
        self.assertIsNotNone(run.completed_at)
        self.assertEqual(
            run.error_code,
            "RuntimeError",
        )
        self.assertEqual(
            run.error_message,
            "LLM unavailable",
        )

        traces = ExecutionTrace.objects.filter(
            question_run=run,
        )

        self.assertEqual(traces.count(), 1)

        trace = traces.get()

        self.assertEqual(
            trace.step,
            "sql_generation",
        )
        self.assertEqual(
            trace.status,
            ExecutionTrace.Status.FAILED,
        )
        self.assertEqual(
            trace.error_code,
            "RuntimeError",
        )
        self.assertEqual(
            trace.error_message,
            "LLM unavailable",
        )