from django.test import TestCase

from apps.conversations.models import Conversation, Message
from apps.projects.tests.factories import create_test_project
from apps.runs.models import QuestionRun, ExecutionTrace


class QuestionRunModelTests(TestCase):
    def test_question_run_has_pending_status_by_default(self):
        project = create_test_project(
            name="Test project",
        )

        run = QuestionRun.objects.create(
            project=project,
        )

        self.assertEqual(
            run.status,
            QuestionRun.Status.PENDING,
        )

    def test_question_run_belongs_to_project(self):
        project = create_test_project(
            name="Test project",
        )

        run = QuestionRun.objects.create(
            project=project,
        )

        self.assertEqual(run.project, project)
        self.assertIn(run, project.question_runs.all())

    def test_execution_trace_belongs_to_question_run(self):
        project = create_test_project(
            name="Test project",
        )

        run = QuestionRun.objects.create(
            project=project,
        )

        trace = ExecutionTrace.objects.create(
            question_run=run,
            step="sql_generation",
        )

        self.assertEqual(trace.question_run, run)
        self.assertIn(trace, run.execution_traces.all())

    def test_execution_trace_has_pending_status_by_default(self):
        project = create_test_project(
            name="Test project",
        )

        run = QuestionRun.objects.create(
            project=project,
        )

        trace = ExecutionTrace.objects.create(
            question_run=run,
            step="sql_generation",
        )

        self.assertEqual(
            trace.status,
            ExecutionTrace.Status.PENDING,
        )


class QuestionRunConversationTests(TestCase):
    def test_question_run_can_be_linked_to_conversation_and_messages(self):
        project = create_test_project(
            name="Test project",
        )

        conversation = Conversation.objects.create(
            project=project,
        )

        user_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content="How many orders are there?",
            sequence_number=1,
        )

        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content="There are two orders.",
            sequence_number=2,
        )

        question_run = QuestionRun.objects.create(
            project=project,
            conversation=conversation,
            user_message=user_message,
            assistant_message=assistant_message,
        )

        self.assertEqual(
            question_run.conversation,
            conversation,
        )
        self.assertEqual(
            question_run.user_message,
            user_message,
        )
        self.assertEqual(
            question_run.assistant_message,
            assistant_message,
        )

    def test_deleting_conversation_deletes_question_run(self):
        project = create_test_project(
            name="Test project",
        )

        conversation = Conversation.objects.create(
            project=project,
        )

        question_run = QuestionRun.objects.create(
            project=project,
            conversation=conversation,
        )

        conversation.delete()

        self.assertFalse(
            QuestionRun.objects.filter(
                id=question_run.id,
            ).exists()
        )

    def test_deleting_messages_preserves_question_run(self):
        project = create_test_project(
            name="Test project",
        )

        conversation = Conversation.objects.create(
            project=project,
        )

        user_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content="How many orders are there?",
            sequence_number=1,
        )

        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content="There are two orders.",
            sequence_number=2,
        )

        question_run = QuestionRun.objects.create(
            project=project,
            conversation=conversation,
            user_message=user_message,
            assistant_message=assistant_message,
        )

        user_message.delete()
        assistant_message.delete()

        question_run.refresh_from_db()

        self.assertIsNone(
            question_run.user_message,
        )
        self.assertIsNone(
            question_run.assistant_message,
        )
