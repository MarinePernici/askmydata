from django.db import IntegrityError
from django.test import TestCase

from apps.conversations.models import Conversation, Message
from apps.projects.tests.factories import create_test_project


class ConversationModelTests(TestCase):
    def test_conversation_can_be_created_for_project(self):
        project = create_test_project(
            name="Test project",
        )

        conversation = Conversation.objects.create(
            project=project,
            title="Sales analysis",
        )

        self.assertEqual(
            conversation.project,
            project,
        )
        self.assertEqual(
            conversation.title,
            "Sales analysis",
        )
        self.assertEqual(
            conversation.status,
            Conversation.Status.ACTIVE,
        )

    def test_project_can_have_multiple_conversations(self):
        project = create_test_project(
            name="Test project",
        )

        Conversation.objects.create(
            project=project,
            title="First conversation",
        )
        Conversation.objects.create(
            project=project,
            title="Second conversation",
        )

        self.assertEqual(
            project.conversations.count(),
            2,
        )


class MessageModelTests(TestCase):
    def test_messages_are_ordered_by_sequence_number(self):
        project = create_test_project(
            name="Test project",
        )

        conversation = Conversation.objects.create(
            project=project,
        )

        Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content="Second message",
            sequence_number=2,
        )

        Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content="First message",
            sequence_number=1,
        )

        messages = list(
            conversation.messages.all()
        )

        self.assertEqual(
            [message.sequence_number for message in messages],
            [1, 2],
        )

    def test_sequence_number_must_be_unique_within_conversation(self):
        project = create_test_project(
            name="Test project",
        )

        conversation = Conversation.objects.create(
            project=project,
        )

        Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content="First message",
            sequence_number=1,
        )

        with self.assertRaises(IntegrityError):
            Message.objects.create(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content="Duplicate sequence",
                sequence_number=1,
            )