from django.test import TestCase

from apps.data_sources.models import DataSource
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


class FakeExecutorFactory:
    def __init__(self):
        self.config = None

    def __call__(self, config):
        self.config = config
        return FakeExecutor()


class FakeCatalogReader:
    def __init__(self, catalog):
        self.catalog = catalog
        self.project = None

    def get_current(self, project):
        self.project = project
        return self.catalog


class QuestionRunServiceTests(TestCase):
    def create_project_with_data_source(self):
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="test_database",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        return project

    def test_successful_run_is_persisted(self):
        project = self.create_project_with_data_source()

        executor_factory = FakeExecutorFactory()

        catalog = KnowledgeCatalog(tables=())
        catalog_reader = FakeCatalogReader(catalog)

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor_factory=executor_factory,
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=catalog_reader,
        )

        result = service.run(
            project=project,
            question="Return one.",
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
        project = self.create_project_with_data_source()

        service = QuestionRunService(
            generator=FailingGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(
                KnowledgeCatalog(tables=())
            ),
        )

        with self.assertRaises(RuntimeError):
            service.run(
                project=project,
                question="Return one.",
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

    def test_executor_factory_receives_project_data_source_config(self):
        project = self.create_project_with_data_source()

        executor_factory = FakeExecutorFactory()

        catalog = KnowledgeCatalog(tables=())
        catalog_reader = FakeCatalogReader(catalog)

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor_factory=executor_factory,
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=catalog_reader,
        )

        service.run(
            project=project,
            question="Return one.",
        )

        self.assertIsNotNone(executor_factory.config)
        self.assertEqual(
            executor_factory.config.host,
            "localhost",
        )
        self.assertEqual(
            executor_factory.config.port,
            5432,
        )
        self.assertEqual(
            executor_factory.config.database,
            "test_database",
        )
        self.assertEqual(
            executor_factory.config.user,
            "readonly",
        )
        self.assertEqual(
            executor_factory.config.password,
            "secret-password",
        )

    def test_catalog_is_loaded_from_project(self):
        project = self.create_project_with_data_source()

        catalog = KnowledgeCatalog(tables=())
        catalog_reader = FakeCatalogReader(catalog)

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=catalog_reader,
        )

        service.run(
            project=project,
            question="Return one.",
        )

        self.assertEqual(
            catalog_reader.project,
            project,
        )