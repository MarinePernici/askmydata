from django.test import TestCase

from apps.catalogs.models import (
    KnowledgeCatalog as KnowledgeCatalogModel,
    SchemaSnapshot,
)
from apps.catalogs.readers import CatalogReader
from apps.conversations.models import Conversation
from apps.conversations.services import ConversationService
from apps.data_sources.models import DataSource
from apps.projects.models import Project
from apps.projects.tests.factories import create_test_project
from apps.runs.models import ExecutionTrace, QuestionRun
from apps.runs.services import QuestionRunService
from catalog.snapshot_serializer import CatalogSnapshotSerializer
from catalog.types import (
    KnowledgeCatalog,
    SemanticMetadata,
    TableMetadata,
)
from connectors.types import ColumnMetadata
from query_engine.types import (
    AnswerGenerationResult,
    QueryExecutionResult,
    ResultValidationResult,
    SQLGenerationResult,
    SQLValidationResult,
)


class RecordingGenerator:
    def __init__(self):
        self.catalog = None

    def generate(self, question, catalog, history=()):
        self.catalog = catalog

        return SQLGenerationResult(
            sql="SELECT id FROM sales.orders;",
            explanation="Returns order identifiers.",
        )


class FakeValidator:
    def validate(self, sql):
        return SQLValidationResult(
            is_valid=True,
        )


class FakeExecutor:
    def execute(self, sql):
        return QueryExecutionResult(
            columns=("id",),
            rows=((1,), (2,)),
        )


class RecordingExecutorFactory:
    def __init__(self):
        self.config = None

    def __call__(self, config):
        self.config = config
        return FakeExecutor()


class FakeResultValidator:
    def validate(self, result):
        return ResultValidationResult(
            is_valid=True,
        )


class FakeAnswerGenerator:
    def generate(self, question, sql, result):
        return AnswerGenerationResult(
            answer="There are two orders.",
        )


class QuestionRunIntegrationTests(TestCase):
    def test_run_uses_persisted_catalog_and_project_data_source(self):
        project = create_test_project(
            name="Test project",
            status=Project.Status.READY,
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="sales_database",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        domain_catalog = KnowledgeCatalog(
            tables=(
                TableMetadata(
                    schema="sales",
                    name="orders",
                    columns=(
                        ColumnMetadata(
                            name="id",
                            data_type="integer",
                            nullable=False,
                            default=None,
                        ),
                    ),
                    relationships=(),
                    semantic_metadata=SemanticMetadata(
                        description="Customer orders",
                        business_synonyms=(
                            "sales orders",
                            "purchases",
                        ),
                    ),
                ),
            )
        )

        catalog_model = KnowledgeCatalogModel.objects.create(
            project=project,
            status=KnowledgeCatalogModel.Status.READY,
            version=1,
        )

        SchemaSnapshot.objects.create(
            catalog=catalog_model,
            version=1,
            schema_data=CatalogSnapshotSerializer().serialize(domain_catalog),
        )

        generator = RecordingGenerator()
        executor_factory = RecordingExecutorFactory()

        service = QuestionRunService(
            generator=generator,
            validator=FakeValidator(),
            executor_factory=executor_factory,
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=CatalogReader(),
            conversation_service=ConversationService(),
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        result = service.run(
            project=project,
            conversation=conversation,
            question="How many orders are there?",
        )

        self.assertEqual(
            generator.catalog,
            domain_catalog,
        )

        self.assertEqual(
            executor_factory.config.database,
            "sales_database",
        )
        self.assertEqual(
            executor_factory.config.user,
            "readonly",
        )

        self.assertEqual(
            result.answer,
            "There are two orders.",
        )

        question_run = QuestionRun.objects.get(
            project=project,
        )

        self.assertEqual(
            question_run.status,
            QuestionRun.Status.COMPLETED,
        )
        self.assertEqual(
            question_run.row_count,
            2,
        )

        self.assertEqual(
            ExecutionTrace.objects.filter(
                question_run=question_run,
            ).count(),
            5,
        )
