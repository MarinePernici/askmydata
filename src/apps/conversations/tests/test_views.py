from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from apps.authentication.models import UserPreferences
from apps.conversations.models import Conversation, Message
from apps.conversations.services import ConversationService
from apps.data_sources.models import DataSource
from apps.projects.models import Project
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


class HTTPFakeGenerator:
    def generate(self, question, catalog, history=()):
        return SQLGenerationResult(
            sql="SELECT 42 AS customer_count;",
            explanation="Returns the customer count.",
            usage=SQL_USAGE,
        )


class HTTPFakeValidator:
    def validate(self, sql, catalog=None):
        return SQLValidationResult(is_valid=True)


class HTTPFakeExecutor:
    def execute(self, sql):
        return QueryExecutionResult(
            columns=("customer_count",),
            rows=((42,),),
        )


class HTTPFakeExecutorFactory:
    def __call__(self, config):
        return HTTPFakeExecutor()


class HTTPFakeResultValidator:
    def validate(self, result):
        return ResultValidationResult(is_valid=True)


class HTTPFakeAnswerGenerator:
    def generate(self, question, sql, result):
        return AnswerGenerationResult(
            answer="There are 42 customers.",
            usage=ANSWER_USAGE,
        )


class HTTPFakeCatalogReader:
    def get_current(self, project):
        return KnowledgeCatalog(tables=())


class HTTPFakeClarificationGenerator:
    def generate(self, question, catalog, history=()):
        return ClarificationResult(
            question="Which date range should I use?",
            usages=(SQL_USAGE,),
        )


class HTTPFakeCannotAnswerGenerator:
    def generate(self, question, catalog, history=()):
        return CannotAnswerResult(
            message=(
                "I can't answer this question using the data available "
                "in this project. Please ask a question related to the project's data."
            ),
            usages=(SQL_USAGE,),
        )


class ConversationViewTests(TestCase):
    def test_user_cannot_access_conversations_for_another_users_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="other-user",
            password="test-password",
        )

        project = Project.objects.create(
            owner=other_user,
            name="Other project",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-list",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)

    def test_user_can_view_own_project_conversations(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="other-user",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
        )
        other_project = Project.objects.create(
            owner=other_user,
            name="Other project",
        )

        conversation = Conversation.objects.create(
            project=project,
            title="My conversation",
        )
        Conversation.objects.create(
            project=other_project,
            title="Other conversation",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-list",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My conversation")
        self.assertNotContains(response, "Other conversation")
        self.assertContains(
            response,
            reverse("project-list"),
        )

        self.assertContains(
            response,
            reverse(
                "project-detail",
                kwargs={"project_id": project.id},
            ),
        )
        self.assertContains(
            response,
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )

    def test_user_can_create_conversation_for_own_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-create",
                kwargs={"project_id": project.id},
            ),
            data={
                "title": "Sales analysis",
            },
        )

        self.assertEqual(response.status_code, 302)

        conversation = Conversation.objects.get(
            project=project,
        )

        self.assertEqual(
            conversation.title,
            "Sales analysis",
        )
        self.assertEqual(
            response.url,
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )

    def test_user_cannot_create_conversation_for_another_users_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="other-user",
            password="test-password",
        )

        project = Project.objects.create(
            owner=other_user,
            name="Other project",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-create",
                kwargs={"project_id": project.id},
            ),
            data={
                "title": "Unauthorized conversation",
            },
        )

        self.assertEqual(response.status_code, 404)

        self.assertFalse(
            Conversation.objects.filter(
                project=project,
            ).exists()
        )

    def test_archived_project_cannot_create_conversation(self):
        user = get_user_model().objects.create_user(
            username="marine-archived-create",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Archived project",
            status=Project.Status.ARCHIVED,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-create",
                kwargs={"project_id": project.id},
            ),
            data={"title": "New conversation"},
        )

        self.assertRedirects(
            response,
            reverse(
                "conversation-list",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertFalse(Conversation.objects.filter(project=project).exists())

    def test_conversation_list_displays_create_action(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-list",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New conversation")
        self.assertContains(
            response,
            reverse(
                "conversation-create",
                kwargs={"project_id": project.id},
            ),
        )

    def test_archived_project_disables_create_conversation_action(self):
        user = get_user_model().objects.create_user(
            username="marine-archived-conversation-list",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Archived project",
            status=Project.Status.ARCHIVED,
        )
        Conversation.objects.create(
            project=project,
            title="Existing conversation",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-list",
                kwargs={"project_id": project.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New conversation")
        self.assertContains(response, "disabled")
        self.assertContains(response, "Select a conversation")
        self.assertContains(
            response,
            "Choose a conversation from the list to view its messages.",
        )
        self.assertNotContains(response, "Start a conversation")
        self.assertNotContains(response, "No conversations")

    def test_user_can_view_own_conversation(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sales analysis")
        self.assertContains(
            response,
            reverse("project-list"),
        )

        self.assertContains(
            response,
            reverse(
                "project-detail",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertContains(
            response,
            reverse(
                "conversation-list",
                kwargs={"project_id": project.id},
            ),
        )

    def test_user_cannot_view_conversation_from_another_users_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="other-user",
            password="test-password",
        )

        project = Project.objects.create(
            owner=other_user,
            name="Other project",
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Private conversation",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )

        self.assertEqual(response.status_code, 404)

    def test_conversation_detail_displays_messages_in_order(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content="How many customers?",
            sequence_number=1,
        )

        Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content="There are 42 customers.",
            sequence_number=2,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How many customers?")
        self.assertContains(response, "There are 42 customers.")

        content = response.content.decode()

        self.assertLess(
            content.index("How many customers?"),
            content.index("There are 42 customers."),
        )

        self.assertEqual(
            content.count("data-conversation-last-message"),
            1,
        )

        last_message_marker = content.index("data-conversation-last-message")

        self.assertGreater(
            last_message_marker,
            content.index("How many customers?"),
        )
        self.assertLess(
            last_message_marker,
            content.index("There are 42 customers."),
        )

    def test_conversation_detail_hides_developer_details_when_disabled(self):
        user = get_user_model().objects.create_user(
            username="developer-mode-disabled",
            password="test-password",
        )
        UserPreferences.objects.create(
            user=user,
            developer_mode=False,
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )
        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )
        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content="There are 42 customers.",
            sequence_number=1,
        )
        run = QuestionRun.objects.create(
            project=project,
            conversation=conversation,
            assistant_message=assistant_message,
            status=QuestionRun.Status.COMPLETED,
            latency_ms=1284,
            model_name="fake-model",
            prompt_tokens=150,
            completion_tokens=30,
            row_count=1,
        )
        ExecutionTrace.objects.create(
            question_run=run,
            step="sql_validation",
            status=ExecutionTrace.Status.COMPLETED,
            duration_ms=8,
            technical_metadata={
                "sql": "SELECT COUNT(*) FROM customers;",
                "validation_error": "sensitive-validation-detail",
            },
            error_message="sensitive-error-message",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            )
        )

        self.assertEqual(response.status_code, 200)

        message = response.context["conversation_messages"][0]

        self.assertFalse(hasattr(message, "developer_details"))
        self.assertNotContains(response, "Technical details")
        self.assertNotContains(response, "SELECT COUNT(*) FROM customers;")
        self.assertNotContains(response, "sensitive-validation-detail")
        self.assertNotContains(response, "sensitive-error-message")

    def test_conversation_detail_builds_safe_developer_details_when_enabled(self):
        user = get_user_model().objects.create_user(
            username="developer-mode-enabled",
            password="test-password",
        )
        UserPreferences.objects.create(
            user=user,
            developer_mode=True,
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )
        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )
        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content="There are 42 customers.",
            sequence_number=1,
        )
        run = QuestionRun.objects.create(
            project=project,
            conversation=conversation,
            assistant_message=assistant_message,
            status=QuestionRun.Status.COMPLETED,
            latency_ms=1284,
            model_name="fake-model",
            prompt_tokens=150,
            completion_tokens=30,
            row_count=1,
        )
        ExecutionTrace.objects.create(
            question_run=run,
            step="sql_validation",
            status=ExecutionTrace.Status.COMPLETED,
            duration_ms=8,
            technical_metadata={
                "sql": "SELECT COUNT(*) FROM customers;",
                "validation_error": "sensitive-validation-detail",
                "secret": "sensitive-secret",
            },
            error_message="sensitive-error-message",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            )
        )

        self.assertEqual(response.status_code, 200)

        message = response.context["conversation_messages"][0]
        details = message.developer_details

        self.assertEqual(
            details,
            {
                "status": "Completed",
                "status_badge": "success",
                "latency_ms": 1284,
                "model_name": "fake-model",
                "prompt_tokens": 150,
                "completion_tokens": 30,
                "row_count": 1,
                "generated_sql": "SELECT COUNT(*) FROM customers;",
                "steps": [
                    {
                        "name": "SQL validation",
                        "status": "Completed",
                        "status_badge": "success",
                        "duration_ms": 8,
                    }
                ],
            },
        )
        self.assertNotIn("technical_metadata", details)
        self.assertNotIn("error_message", details)
        self.assertNotIn("error_code", details)
        self.assertContains(response, "Technical details")
        self.assertContains(response, "Completed")
        self.assertContains(response, "1284 ms")
        self.assertContains(response, "fake-model")
        self.assertContains(response, "150")
        self.assertContains(response, "30")
        self.assertContains(response, "SELECT COUNT(*) FROM customers;")
        self.assertContains(response, "SQL validation")
        self.assertContains(response, "8 ms")

        self.assertNotContains(response, "sensitive-validation-detail")
        self.assertNotContains(response, "sensitive-secret")
        self.assertNotContains(response, "sensitive-error-message")

        content = response.content.decode()
        details_start = content.index('<details class="developer-details">')
        details_end = content.index("</details>", details_start)
        details = content[details_start:details_end]

        self.assertNotIn(" open", details)

    def test_conversation_detail_translates_developer_details_in_french(self):
        user = get_user_model().objects.create_user(
            username="developer-mode-french",
            password="test-password",
        )
        UserPreferences.objects.create(
            user=user,
            language=UserPreferences.Language.FRENCH,
            developer_mode=True,
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
        )
        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )
        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content="There are 42 customers.",
            sequence_number=1,
        )
        run = QuestionRun.objects.create(
            project=project,
            conversation=conversation,
            assistant_message=assistant_message,
            status=QuestionRun.Status.COMPLETED,
        )
        ExecutionTrace.objects.create(
            question_run=run,
            step="sql_validation",
            status=ExecutionTrace.Status.COMPLETED,
            duration_ms=8,
        )

        self.client.force_login(user)

        with translation.override("fr"):
            response = self.client.get(
                reverse(
                    "conversation-detail",
                    kwargs={
                        "project_id": project.id,
                        "conversation_id": conversation.id,
                    },
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Détails techniques")
        self.assertContains(response, "Terminé")
        self.assertContains(response, "Validation SQL")
        self.assertNotContains(response, ">Completed<")
        self.assertNotContains(response, ">SQL validation<")

    def test_user_can_rename_own_conversation(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )
        conversation = Conversation.objects.create(
            project=project,
            title="Old title",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-rename",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            {
                "title": "New title",
            },
        )

        conversation.refresh_from_db()

        self.assertEqual(
            conversation.title,
            "New title",
        )
        self.assertRedirects(
            response,
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )

    def test_user_cannot_rename_conversation_from_another_users_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="other-user",
            password="test-password",
        )
        other_project = Project.objects.create(
            owner=other_user,
            name="Other project",
        )
        conversation = Conversation.objects.create(
            project=other_project,
            title="Private conversation",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-rename",
                kwargs={
                    "project_id": other_project.id,
                    "conversation_id": conversation.id,
                },
            ),
            {
                "title": "Changed title",
            },
        )

        conversation.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            conversation.title,
            "Private conversation",
        )

    def test_rename_conversation_rejects_get_request(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )
        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-rename",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_archived_project_cannot_rename_conversation(self):
        user = get_user_model().objects.create_user(
            username="marine-archived-rename",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Archived project",
            status=Project.Status.ARCHIVED,
        )
        conversation = Conversation.objects.create(
            project=project,
            title="Original title",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-rename",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={"title": "Changed title"},
        )

        conversation.refresh_from_db()

        self.assertRedirects(
            response,
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )
        self.assertEqual(conversation.title, "Original title")

    @patch("apps.conversations.views.create_question_run_service")
    def test_user_can_ask_question_in_own_conversation(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
            status=Project.Status.READY,
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        question_run_service = create_question_run_service.return_value

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={
                "question": "How many customers?",
            },
        )

        self.assertEqual(response.status_code, 302)

        question_run_service.run.assert_called_once_with(
            project=project,
            conversation=conversation,
            question="How many customers?",
        )

    @patch("apps.conversations.views.create_question_run_service")
    def test_user_cannot_ask_question_in_another_users_conversation(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        other_user = get_user_model().objects.create_user(
            username="other-user",
            password="test-password",
        )

        project = Project.objects.create(
            owner=other_user,
            name="Other project",
            status=Project.Status.READY,
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Private conversation",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={
                "question": "How many customers?",
            },
        )

        self.assertEqual(response.status_code, 404)
        create_question_run_service.assert_not_called()

    def test_conversation_detail_displays_ask_question_form(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
            status=Project.Status.READY,
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="question"')
        self.assertContains(
            response,
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )
        self.assertContains(
            response,
            'aria-label="Ask question"',
        )
        self.assertContains(
            response,
            "data-conversation-question-form",
        )
        self.assertContains(
            response,
            "data-conversation-question-input",
        )
        self.assertContains(
            response,
            "data-conversation-question-submit",
        )
        self.assertContains(
            response,
            "data-conversation-messages",
        )

        content = response.content.decode()

        submit_button_start = content.index("data-conversation-question-submit")
        submit_button_end = content.index(
            "</button>",
            submit_button_start,
        )

        submit_button = content[submit_button_start:submit_button_end]

        self.assertIn("disabled", submit_button)

    def test_archived_project_displays_conversation_as_read_only(self):
        user = get_user_model().objects.create_user(
            username="marine-archived-conversation-detail",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Archived project",
            status=Project.Status.ARCHIVED,
        )
        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "This project is archived and read-only.",
        )
        self.assertNotContains(
            response,
            'placeholder="Ask a question about your data..."',
        )
        self.assertContains(response, "No messages")
        self.assertContains(
            response,
            "This conversation has no messages.",
        )
        self.assertNotContains(response, "Ask your first question")

    @patch("apps.conversations.views.create_question_run_service")
    def test_empty_question_does_not_run_question_service(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
            status=Project.Status.READY,
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={
                "question": "   ",
            },
        )

        self.assertEqual(response.status_code, 302)
        create_question_run_service.assert_not_called()

    def test_ask_question_rejects_get_request(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
            status=Project.Status.READY,
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )

        self.assertEqual(response.status_code, 404)

    @patch("apps.conversations.views.create_question_run_service")
    def test_question_run_error_redirects_back_to_conversation(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
            status=Project.Status.READY,
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        service = create_question_run_service.return_value
        service.run.side_effect = RuntimeError("Sensitive internal details")

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={"question": "How many customers?"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )

    @patch("apps.conversations.views.create_question_run_service")
    def test_question_run_error_displays_generic_message(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
            status=Project.Status.READY,
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        service = create_question_run_service.return_value
        service.run.side_effect = RuntimeError("Sensitive internal details")

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={"question": "How many customers?"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Unable to process your question.",
        )
        self.assertNotContains(
            response,
            "Sensitive internal details",
        )
        self.assertContains(
            response,
            "data-question-error-dialog",
        )

    @patch("apps.conversations.views.create_question_run_service")
    def test_question_run_permission_error_displays_safe_message(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
            status=Project.Status.READY,
        )
        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        service = create_question_run_service.return_value
        service.run.side_effect = DataSourcePermissionError(
            "permission denied for table customers"
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={"question": "How many customers?"},
            follow=True,
        )
        self.assertContains(
            response,
            "The database user no longer has the required permissions. "
            "Check the data source permissions.",
        )
        self.assertNotContains(
            response,
            "permission denied for table customers",
        )
        self.assertContains(
            response,
            "data-question-error-dialog",
        )

        self.assertContains(
            response,
            'aria-labelledby="question-error-title-1"',
        )

    @patch("apps.conversations.views.create_question_run_service")
    def test_question_run_timeout_error_displays_safe_message(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
            status=Project.Status.READY,
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        service = create_question_run_service.return_value
        service.run.side_effect = QueryTimeoutError(
            "canceling statement due to statement timeout"
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={"question": "How many customers?"},
            follow=True,
        )

        self.assertContains(
            response,
            "The query took too long to execute. Try a more specific question.",
        )
        self.assertNotContains(
            response,
            "canceling statement due to statement timeout",
        )
        self.assertContains(
            response,
            "data-question-error-dialog",
        )

    @patch("apps.conversations.views.create_question_run_service")
    def test_question_run_sql_validation_error_redirects_without_flash_message(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="marine-sql-validation-error",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
            status=Project.Status.READY,
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        service = create_question_run_service.return_value
        service.run.side_effect = SQLValidationError(
            "SQL query references a table outside the catalog scope."
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={"question": "What is the total amount of all payments?"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            "SQL query references a table outside the catalog scope.",
        )
        self.assertNotContains(
            response,
            "I can't answer this question with the data available in this project.",
        )
        self.assertNotContains(
            response,
            "data-question-error-dialog",
        )

    @patch("apps.conversations.views.create_question_run_service")
    def test_question_run_connection_error_displays_safe_modal(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="marine-connection-error",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
            status=Project.Status.READY,
        )
        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        service = create_question_run_service.return_value
        service.run.side_effect = DataSourceConnectionError(
            "Sensitive connection details"
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={"question": "How many customers?"},
            follow=True,
        )

        self.assertContains(
            response,
            "Unable to connect to the project's data source. "
            "Check the connection and try again.",
            html=True,
        )
        self.assertContains(
            response,
            "data-question-error-dialog",
        )
        self.assertNotContains(
            response,
            "Sensitive connection details",
        )

    @patch("apps.conversations.views.create_question_run_service")
    def test_question_cannot_be_asked_when_project_is_not_ready(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
            status=Project.Status.CONFIGURING,
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={"question": "How many customers?"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Project is not ready.",
        )
        create_question_run_service.assert_not_called()

    @patch("apps.conversations.views.create_question_run_service")
    def test_question_cannot_be_asked_when_project_is_archived(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="marine-archived-question",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Archived project",
            status=Project.Status.ARCHIVED,
        )
        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={"question": "How many customers?"},
        )

        self.assertRedirects(
            response,
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )

        create_question_run_service.assert_not_called()

    def test_conversation_detail_hides_ask_form_when_project_is_not_ready(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
            status=Project.Status.CONFIGURING,
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            "data-conversation-question-form",
        )
        self.assertNotContains(
            response,
            "data-conversation-question-input",
        )
        self.assertNotContains(
            response,
            "data-conversation-question-submit",
        )

    def test_user_cannot_view_conversation_through_another_own_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="Project A",
        )

        other_project = Project.objects.create(
            owner=user,
            name="Project B",
        )

        conversation = Conversation.objects.create(
            project=other_project,
            title="Project B conversation",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "conversation-detail",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
        )

        self.assertEqual(response.status_code, 404)

    @patch("apps.conversations.views.create_question_run_service")
    def test_asking_question_persists_and_displays_conversation_messages(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
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

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        create_question_run_service.return_value = QuestionRunService(
            generator=HTTPFakeGenerator(),
            validator=HTTPFakeValidator(),
            executor_factory=HTTPFakeExecutorFactory(),
            result_validator=HTTPFakeResultValidator(),
            answer_generator=HTTPFakeAnswerGenerator(),
            catalog_reader=HTTPFakeCatalogReader(),
            conversation_service=ConversationService(),
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={
                "question": "How many customers?",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        messages = list(conversation.messages.order_by("sequence_number"))

        self.assertEqual(len(messages), 2)

        self.assertEqual(
            messages[0].content,
            "How many customers?",
        )
        self.assertEqual(
            messages[1].content,
            "There are 42 customers.",
        )

        self.assertContains(
            response,
            "How many customers?",
        )
        self.assertContains(
            response,
            "There are 42 customers.",
        )

        run = QuestionRun.objects.get(
            conversation=conversation,
        )
        self.assertEqual(
            run.status,
            QuestionRun.Status.COMPLETED,
        )

    @patch("apps.conversations.views.create_question_run_service")
    def test_clarification_displays_without_error_modal(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="clarification-user",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
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

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        create_question_run_service.return_value = QuestionRunService(
            generator=HTTPFakeClarificationGenerator(),
            validator=HTTPFakeValidator(),
            executor_factory=HTTPFakeExecutorFactory(),
            result_validator=HTTPFakeResultValidator(),
            answer_generator=HTTPFakeAnswerGenerator(),
            catalog_reader=HTTPFakeCatalogReader(),
            conversation_service=ConversationService(),
        )

        self.client.force_login(user)
        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={"question": "How many recent orders?"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Which date range should I use?")
        self.assertNotContains(response, "data-question-error-dialog")

        run = QuestionRun.objects.get(conversation=conversation)
        self.assertEqual(
            run.status,
            QuestionRun.Status.NEEDS_CLARIFICATION,
        )

    @patch("apps.conversations.views.create_question_run_service")
    def test_cannot_answer_displays_without_error_modal(
        self,
        create_question_run_service,
    ):
        user = get_user_model().objects.create_user(
            username="cannot-answer-user",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
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

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        create_question_run_service.return_value = QuestionRunService(
            generator=HTTPFakeCannotAnswerGenerator(),
            validator=HTTPFakeValidator(),
            executor_factory=HTTPFakeExecutorFactory(),
            result_validator=HTTPFakeResultValidator(),
            answer_generator=HTTPFakeAnswerGenerator(),
            catalog_reader=HTTPFakeCatalogReader(),
            conversation_service=ConversationService(),
        )

        self.client.force_login(user)
        response = self.client.post(
            reverse(
                "conversation-ask",
                kwargs={
                    "project_id": project.id,
                    "conversation_id": conversation.id,
                },
            ),
            data={"question": "What is the weather tomorrow?"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "data-question-error-dialog")

        run = QuestionRun.objects.get(conversation=conversation)
        self.assertEqual(
            run.status,
            QuestionRun.Status.REJECTED,
        )
        self.assertContains(
            response,
            "I can't answer this question using the data available "
            "in this project. Please ask a question related to the "
            "project's data.",
            html=True,
        )
