from django.test import TestCase

from apps.conversations.models import Conversation, Message
from apps.conversations.services import ConversationService
from apps.projects.tests.factories import create_test_project
from query_engine.types import ConversationMessage


class ConversationServiceTests(TestCase):
    def setUp(self):
        self.project = create_test_project(
            name="Test project",
        )

        self.conversation = Conversation.objects.create(
            project=self.project,
            title="Test conversation",
        )

        self.service = ConversationService()

    def test_add_message_uses_sequence_one_for_first_message(self):
        message = self.service.add_message(
            conversation=self.conversation,
            role=Message.Role.USER,
            content="First message",
        )

        self.assertEqual(
            message.sequence_number,
            1,
        )

    def test_add_message_uses_next_sequence_number(self):
        self.service.add_message(
            conversation=self.conversation,
            role=Message.Role.USER,
            content="First message",
        )

        message = self.service.add_message(
            conversation=self.conversation,
            role=Message.Role.ASSISTANT,
            content="Second message",
        )

        self.assertEqual(
            message.sequence_number,
            2,
        )

    def test_add_message_uses_highest_sequence_after_deletion(self):
        Message.objects.create(
            conversation=self.conversation,
            role=Message.Role.USER,
            content="First message",
            sequence_number=1,
        )

        second_message = Message.objects.create(
            conversation=self.conversation,
            role=Message.Role.ASSISTANT,
            content="Second message",
            sequence_number=2,
        )

        Message.objects.create(
            conversation=self.conversation,
            role=Message.Role.USER,
            content="Third message",
            sequence_number=3,
        )

        second_message.delete()

        message = self.service.add_message(
            conversation=self.conversation,
            role=Message.Role.ASSISTANT,
            content="New message",
        )

        self.assertEqual(
            message.sequence_number,
            4,
        )

    def test_get_history_returns_messages_in_sequence_order(self):
        Message.objects.create(
            conversation=self.conversation,
            role=Message.Role.ASSISTANT,
            content="Second message",
            sequence_number=2,
        )

        Message.objects.create(
            conversation=self.conversation,
            role=Message.Role.USER,
            content="First message",
            sequence_number=1,
        )

        history = self.service.get_history(
            conversation=self.conversation,
        )

        self.assertEqual(
            history,
            (
                ConversationMessage(
                    role="user",
                    content="First message",
                ),
                ConversationMessage(
                    role="assistant",
                    content="Second message",
                ),
            ),
        )

    def test_get_history_limits_to_most_recent_messages(self):
        for sequence_number in range(1, 26):
            Message.objects.create(
                conversation=self.conversation,
                role=Message.Role.USER,
                content=f"Message {sequence_number}",
                sequence_number=sequence_number,
            )

        history = self.service.get_history(
            conversation=self.conversation,
            max_messages=20,
        )

        self.assertEqual(len(history), 20)

        self.assertEqual(
            history[0].content,
            "Message 6",
        )
        self.assertEqual(
            history[-1].content,
            "Message 25",
        )

    def test_get_history_uses_default_limit(self):
        for sequence_number in range(1, 26):
            Message.objects.create(
                conversation=self.conversation,
                role=Message.Role.USER,
                content=f"Message {sequence_number}",
                sequence_number=sequence_number,
            )

        history = self.service.get_history(
            conversation=self.conversation,
        )

        self.assertEqual(len(history), 20)
        self.assertEqual(history[0].content, "Message 6")
        self.assertEqual(history[-1].content, "Message 25")

    def test_create_conversation_for_project(self):
        conversation = self.service.create_conversation(
            project=self.project,
            title="Sales analysis",
        )

        self.assertEqual(
            conversation.project,
            self.project,
        )
        self.assertEqual(
            conversation.title,
            "Sales analysis",
        )
        self.assertEqual(
            conversation.status,
            Conversation.Status.ACTIVE,
        )

    def test_list_conversations_returns_project_conversations_most_recent_first(self):
        older = Conversation.objects.create(
            project=self.project,
            title="Older",
        )
        newer = Conversation.objects.create(
            project=self.project,
            title="Newer",
        )

        other_project = create_test_project(
            name="Other project",
        )
        Conversation.objects.create(
            project=other_project,
            title="Other",
        )

        conversations = self.service.list_conversations(
            project=self.project,
        )

        self.assertEqual(
            list(conversations),
            [
                newer,
                older,
                self.conversation,
            ],
        )

    def test_get_conversation_returns_conversation_for_project(self):
        conversation = self.service.get_conversation(
            project=self.project,
            conversation_id=self.conversation.id,
        )

        self.assertEqual(
            conversation,
            self.conversation,
        )

    def test_get_conversation_rejects_conversation_from_another_project(self):
        other_project = create_test_project(
            name="Other project",
        )

        with self.assertRaises(Conversation.DoesNotExist):
            self.service.get_conversation(
                project=other_project,
                conversation_id=self.conversation.id,
            )
