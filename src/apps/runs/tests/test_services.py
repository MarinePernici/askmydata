from unittest.mock import patch

from django.test import TestCase

from apps.conversations.models import Conversation, Message
from apps.conversations.services import ConversationService
from apps.data_sources.models import DataSource
from apps.projects.models import Project
from apps.projects.tests.factories import create_test_project
from apps.runs.exceptions import ProjectNotReadyError
from apps.runs.models import ExecutionTrace, QuestionRun
from apps.runs.services import QuestionRunService
from catalog.types import KnowledgeCatalog
from llm.types import LLMUsage
from query_engine.exceptions import (
    DataSourceConnectionError,
    DataSourcePermissionError,
    QueryTimeoutError,
    SQLValidationError,
)
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
        return SQLValidationResult(is_valid=True)


class FailingValidator:
    def validate(self, sql, catalog=None):
        return SQLValidationResult(
            is_valid=False,
            error="SQL query references a table outside the catalog scope.",
        )


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
            usage=ANSWER_USAGE,
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
            sql="SELECT 1 AS value;",
            explanation="Returns one value.",
            usage=SQL_USAGE,
        )


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


class QuestionRunServiceTests(TestCase):
    def create_conversation(self, project):
        return Conversation.objects.create(
            project=project,
            title="Test conversation",
        )

    def create_project_with_data_source(self):
        project = create_test_project(
            name="Test project",
            status=Project.Status.READY,
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
        conversation = self.create_conversation(project)

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
            conversation_service=ConversationService(),
        )

        result = service.run(
            project=project,
            conversation=conversation,
            question="Return one.",
        )

        run = QuestionRun.objects.get()

        self.assertEqual(run.status, QuestionRun.Status.COMPLETED)
        self.assertIsNotNone(run.started_at)
        self.assertIsNotNone(run.completed_at)
        self.assertEqual(run.row_count, 1)

        self.assertIsNotNone(run.latency_ms)
        self.assertGreaterEqual(run.latency_ms, 0)

        self.assertEqual(run.model_name, "fake-model")
        self.assertEqual(run.prompt_tokens, 150)
        self.assertEqual(run.completion_tokens, 30)
        self.assertIsNone(run.estimated_cost)

        self.assertEqual(result.answer, "There is one value.")

        self.assertEqual(
            ExecutionTrace.objects.filter(question_run=run).count(),
            5,
        )

    def test_failed_run_is_persisted(self):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        service = QuestionRunService(
            generator=FailingGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        with self.assertRaises(RuntimeError):
            service.run(
                project=project,
                conversation=conversation,
                question="Return one.",
            )

        run = QuestionRun.objects.get()

        self.assertEqual(
            run.status,
            QuestionRun.Status.FAILED,
        )
        self.assertIsNotNone(run.started_at)
        self.assertIsNotNone(run.completed_at)
        self.assertIsNotNone(run.latency_ms)
        self.assertGreaterEqual(run.latency_ms, 0)
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
        conversation = self.create_conversation(project)

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
            conversation_service=ConversationService(),
        )

        service.run(
            project=project,
            conversation=conversation,
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

        conversation = self.create_conversation(project)

        catalog = KnowledgeCatalog(tables=())
        catalog_reader = FakeCatalogReader(catalog)

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=catalog_reader,
            conversation_service=ConversationService(),
        )

        service.run(
            project=project,
            conversation=conversation,
            question="Return one.",
        )

        self.assertEqual(
            catalog_reader.project,
            project,
        )

    def test_successful_run_creates_conversation_messages(self):
        project = self.create_project_with_data_source()

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        service.run(
            project=project,
            conversation=conversation,
            question="Return one.",
        )

        messages = list(conversation.messages.all())

        self.assertEqual(
            len(messages),
            2,
        )

        self.assertEqual(
            messages[0].role,
            Message.Role.USER,
        )
        self.assertEqual(
            messages[0].content,
            "Return one.",
        )
        self.assertEqual(
            messages[0].sequence_number,
            1,
        )

        self.assertEqual(
            messages[1].role,
            Message.Role.ASSISTANT,
        )
        self.assertEqual(
            messages[1].content,
            "There is one value.",
        )
        self.assertEqual(
            messages[1].sequence_number,
            2,
        )

        question_run = QuestionRun.objects.get()

        self.assertEqual(
            question_run.conversation,
            conversation,
        )
        self.assertEqual(
            question_run.user_message,
            messages[0],
        )
        self.assertEqual(
            question_run.assistant_message,
            messages[1],
        )

    def test_first_question_sets_conversation_title(self):
        project = self.create_project_with_data_source()

        conversation = Conversation.objects.create(
            project=project,
        )

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        service.run(
            project=project,
            conversation=conversation,
            question="How many customers do we have?",
        )

        conversation.refresh_from_db()

        self.assertEqual(
            conversation.title,
            "How many customers do we have?",
        )

    def test_failed_run_creates_safe_assistant_message(self):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        service = QuestionRunService(
            generator=FailingGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        with self.assertRaises(RuntimeError):
            service.run(
                project=project,
                conversation=conversation,
                question="Return one.",
            )

        messages = list(conversation.messages.all())

        self.assertEqual(len(messages), 2)

        self.assertEqual(messages[0].role, Message.Role.USER)
        self.assertEqual(messages[0].content, "Return one.")

        self.assertEqual(messages[1].role, Message.Role.ASSISTANT)
        self.assertEqual(
            messages[1].content,
            "Unable to process your question. Please try again.",
        )
        self.assertNotIn("LLM unavailable", messages[1].content)

        question_run = QuestionRun.objects.get()

        self.assertEqual(
            question_run.status,
            QuestionRun.Status.FAILED,
        )
        self.assertEqual(
            question_run.user_message,
            messages[0],
        )
        self.assertEqual(
            question_run.assistant_message,
            messages[1],
        )

        self.assertEqual(
            question_run.error_message,
            "LLM unavailable",
        )

    def test_execution_errors_create_safe_assistant_messages(self):
        cases = (
            (
                DataSourceConnectionError,
                (
                    "Unable to connect to the project's data source. "
                    "Check the connection and try again."
                ),
            ),
            (
                DataSourcePermissionError,
                (
                    "The database user no longer has the required permissions. "
                    "Check the data source permissions."
                ),
            ),
            (
                QueryTimeoutError,
                "The query took too long to execute. Try a more specific question.",
            ),
        )

        for exception_class, expected_message in cases:
            with self.subTest(exception=exception_class.__name__):
                project = self.create_project_with_data_source()
                conversation = self.create_conversation(project)

                service = QuestionRunService(
                    generator=FakeGenerator(),
                    validator=FakeValidator(),
                    executor_factory=FakeExecutorFactory(),
                    result_validator=FakeResultValidator(),
                    answer_generator=FakeAnswerGenerator(),
                    catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
                    conversation_service=ConversationService(),
                )

                technical_detail = "Sensitive database connection details"

                with (
                    patch.object(
                        FakeExecutor,
                        "execute",
                        side_effect=exception_class(technical_detail),
                    ),
                    self.assertRaises(exception_class),
                ):
                    service.run(
                        project=project,
                        conversation=conversation,
                        question="Return one.",
                    )

                run = QuestionRun.objects.get(
                    conversation=conversation,
                )

                self.assertEqual(run.status, QuestionRun.Status.FAILED)
                self.assertEqual(run.error_code, exception_class.__name__)
                self.assertEqual(run.error_message, technical_detail)

                self.assertIsNotNone(run.assistant_message)
                self.assertEqual(
                    run.assistant_message.content,
                    expected_message,
                )
                self.assertNotIn(
                    technical_detail,
                    run.assistant_message.content,
                )
                self.assertEqual(conversation.messages.count(), 2)

    def test_sql_validation_failure_creates_safe_assistant_message(self):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FailingValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        with self.assertRaises(SQLValidationError):
            service.run(
                project=project,
                conversation=conversation,
                question="What is the total amount of all payments?",
            )

        messages = list(conversation.messages.order_by("sequence_number"))

        self.assertEqual(len(messages), 2)

        self.assertEqual(messages[0].role, Message.Role.USER)
        self.assertEqual(
            messages[0].content,
            "What is the total amount of all payments?",
        )

        self.assertEqual(messages[1].role, Message.Role.ASSISTANT)
        self.assertEqual(
            messages[1].content,
            "I can't answer this question with the data available in this project.",
        )
        self.assertNotIn(
            "outside the catalog scope",
            messages[1].content,
        )

        question_run = QuestionRun.objects.get()

        self.assertEqual(
            question_run.status,
            QuestionRun.Status.FAILED,
        )
        self.assertEqual(
            question_run.error_code,
            "SQLValidationError",
        )
        self.assertEqual(
            question_run.error_message,
            "SQL query references a table outside the catalog scope.",
        )
        self.assertEqual(
            question_run.assistant_message,
            messages[1],
        )
        self.assertIsNotNone(question_run.latency_ms)
        self.assertGreaterEqual(question_run.latency_ms, 0)

    def test_run_appends_messages_after_highest_sequence_number(self):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content="Previous question",
            sequence_number=1,
        )

        message_to_delete = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content="Previous answer",
            sequence_number=2,
        )

        Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content="Another question",
            sequence_number=3,
        )

        message_to_delete.delete()

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        service.run(
            project=project,
            conversation=conversation,
            question="Return one.",
        )

        self.assertEqual(
            list(
                conversation.messages.values_list(
                    "sequence_number",
                    flat=True,
                )
            ),
            [1, 3, 4, 5],
        )

    def test_run_passes_previous_conversation_history_to_generator(self):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content="How many orders are there?",
            sequence_number=1,
        )
        Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content="There are 42 orders.",
            sequence_number=2,
        )

        generator = RecordingGenerator()
        catalog = KnowledgeCatalog(tables=())

        service = QuestionRunService(
            generator=generator,
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(catalog),
            conversation_service=ConversationService(),
        )

        service.run(
            project=project,
            conversation=conversation,
            question="And how many this month?",
        )

        self.assertEqual(
            generator.history,
            (
                ConversationMessage(
                    role="user",
                    content="How many orders are there?",
                ),
                ConversationMessage(
                    role="assistant",
                    content="There are 42 orders.",
                ),
            ),
        )

    def test_run_rejects_conversation_from_another_project(self):
        project = self.create_project_with_data_source()
        other_project = self.create_project_with_data_source()

        conversation = self.create_conversation(other_project)

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        with self.assertRaises(ValueError):
            service.run(
                project=project,
                conversation=conversation,
                question="Return one.",
            )

        self.assertEqual(
            conversation.messages.count(),
            0,
        )

        self.assertFalse(
            QuestionRun.objects.filter(
                conversation=conversation,
            ).exists()
        )

    def test_run_persists_clarification_request(self):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        service = QuestionRunService(
            generator=ClarificationGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        result = service.run(
            project=project,
            conversation=conversation,
            question="How many recent orders are there?",
        )

        run = QuestionRun.objects.get()

        self.assertEqual(
            result,
            ClarificationResult(
                question="Which date range should I use?",
                usages=(SQL_USAGE,),
            ),
        )

        self.assertEqual(
            run.status,
            QuestionRun.Status.NEEDS_CLARIFICATION,
        )

        self.assertIsNotNone(run.assistant_message)
        self.assertEqual(
            run.assistant_message.content,
            "Which date range should I use?",
        )

        self.assertEqual(
            run.assistant_message.role,
            Message.Role.ASSISTANT,
        )
        self.assertIsNotNone(run.latency_ms)
        self.assertGreaterEqual(run.latency_ms, 0)

        self.assertEqual(run.model_name, "fake-model")
        self.assertEqual(run.prompt_tokens, 100)
        self.assertEqual(run.completion_tokens, 20)
        self.assertIsNone(run.estimated_cost)

    def test_answer_to_clarification_uses_previous_exchange_as_history(self):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content="How many recent orders are there?",
            sequence_number=1,
        )
        Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content="Which date range should I use?",
            sequence_number=2,
        )

        generator = RecordingGenerator()
        catalog = KnowledgeCatalog(tables=())

        service = QuestionRunService(
            generator=generator,
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(catalog),
            conversation_service=ConversationService(),
        )

        service.run(
            project=project,
            conversation=conversation,
            question="The last 30 days.",
        )

        self.assertEqual(
            generator.history,
            (
                ConversationMessage(
                    role="user",
                    content="How many recent orders are there?",
                ),
                ConversationMessage(
                    role="assistant",
                    content="Which date range should I use?",
                ),
            ),
        )

    def test_unanswerable_question_is_rejected_with_safe_message(self):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        service = QuestionRunService(
            generator=CannotAnswerGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        result = service.run(
            project=project,
            conversation=conversation,
            question="What is the capital of Italy?",
        )

        run = QuestionRun.objects.get()

        self.assertEqual(
            result,
            CannotAnswerResult(
                usages=(SQL_USAGE,),
            ),
        )
        self.assertEqual(
            run.status,
            QuestionRun.Status.REJECTED,
        )
        self.assertIsNotNone(run.latency_ms)
        self.assertGreaterEqual(run.latency_ms, 0)

        self.assertEqual(run.model_name, "fake-model")
        self.assertEqual(run.prompt_tokens, 100)
        self.assertEqual(run.completion_tokens, 20)
        self.assertIsNone(run.estimated_cost)
        self.assertIsNotNone(run.assistant_message)
        self.assertEqual(
            run.assistant_message.content,
            (
                "I can't answer this question using the data available "
                "in this project. Please ask a question related to the "
                "project's data."
            ),
        )
        self.assertEqual(
            run.assistant_message.role,
            Message.Role.ASSISTANT,
        )
        self.assertEqual(run.error_code, "")
        self.assertEqual(run.error_message, "")
        self.assertIsNone(run.row_count)

    def test_run_rejects_project_that_is_not_ready(self):
        project = self.create_project_with_data_source()
        project.status = Project.Status.CONFIGURING
        project.save(update_fields=["status"])

        conversation = self.create_conversation(project)

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        with self.assertRaises(ProjectNotReadyError):
            service.run(
                project=project,
                conversation=conversation,
                question="How many orders are there?",
            )

        self.assertEqual(
            project.question_runs.count(),
            0,
        )
        self.assertEqual(
            conversation.messages.count(),
            0,
        )

    @patch("apps.runs.services.logger")
    def test_unexpected_run_failure_is_logged(self, logger):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        service = QuestionRunService(
            generator=FailingGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        with self.assertRaises(RuntimeError):
            service.run(
                project=project,
                conversation=conversation,
                question="Return one.",
            )

        question_run = QuestionRun.objects.get()

        logger.exception.assert_called_once_with(
            "Unexpected failure while processing question run.",
            extra={
                "event": "question_run.failed",
                "project_id": project.id,
                "question_run_id": question_run.id,
            },
        )

    @patch("apps.runs.services.traced_question_run")
    def test_run_is_traced_with_correlation_identifiers(self, traced_question_run):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        service.run(
            project=project,
            conversation=conversation,
            question="Return one.",
        )

        question_run = QuestionRun.objects.get()

        traced_question_run.assert_called_once_with(
            project_id=project.id,
            question_run_id=question_run.id,
        )

    @patch("apps.runs.services.traced_question_run")
    def test_failed_run_is_traced_with_correlation_identifiers(
        self,
        traced_question_run,
    ):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        service = QuestionRunService(
            generator=FailingGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        with self.assertRaises(RuntimeError):
            service.run(
                project=project,
                conversation=conversation,
                question="Return one.",
            )

        question_run = QuestionRun.objects.get()

        traced_question_run.assert_called_once_with(
            project_id=project.id,
            question_run_id=question_run.id,
        )

    @patch("apps.runs.services.record_question_run_metrics")
    def test_completed_run_records_question_run_metrics(
        self,
        record_question_run_metrics,
    ):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        service.run(
            project=project,
            conversation=conversation,
            question="Return one.",
        )

        question_run = QuestionRun.objects.get()

        record_question_run_metrics.assert_called_once_with(
            status=QuestionRun.Status.COMPLETED,
            duration_ms=question_run.latency_ms,
        )

    @patch("apps.runs.services.record_llm_token_metrics")
    def test_completed_run_records_llm_token_metrics(
        self,
        record_llm_token_metrics,
    ):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        service = QuestionRunService(
            generator=FakeGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        service.run(
            project=project,
            conversation=conversation,
            question="Return one.",
        )

        self.assertEqual(record_llm_token_metrics.call_count, 2)

    @patch("apps.runs.services.record_question_run_metrics")
    def test_failed_run_records_question_run_metrics(
        self,
        record_question_run_metrics,
    ):
        project = self.create_project_with_data_source()
        conversation = self.create_conversation(project)

        service = QuestionRunService(
            generator=FailingGenerator(),
            validator=FakeValidator(),
            executor_factory=FakeExecutorFactory(),
            result_validator=FakeResultValidator(),
            answer_generator=FakeAnswerGenerator(),
            catalog_reader=FakeCatalogReader(KnowledgeCatalog(tables=())),
            conversation_service=ConversationService(),
        )

        with self.assertRaises(RuntimeError):
            service.run(
                project=project,
                conversation=conversation,
                question="Return one.",
            )

        question_run = QuestionRun.objects.get()

        record_question_run_metrics.assert_called_once_with(
            status=QuestionRun.Status.FAILED,
            duration_ms=question_run.latency_ms,
        )
