from django.db.models import Max

from apps.conversations.models import Conversation, Message
from query_engine.types import ConversationMessage


class ConversationService:
    def add_message(
        self,
        conversation: Conversation,
        role: str,
        content: str,
    ) -> Message:
        max_sequence = conversation.messages.aggregate(
            max_sequence=Max("sequence_number")
        )["max_sequence"]

        next_sequence = (max_sequence or 0) + 1

        return Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            sequence_number=next_sequence,
        )

    def get_history(
        self,
        conversation: Conversation,
        max_messages: int = 20,
    ) -> tuple[ConversationMessage, ...]:
        messages = list(
            conversation.messages
            .order_by("-sequence_number")[:max_messages]
        )

        messages.reverse()

        return tuple(
            ConversationMessage(
                role=message.role,
                content=message.content,
            )
            for message in messages
        )

    def create_conversation(
        self,
        project,
        title: str = "",
    ) -> Conversation:
        return Conversation.objects.create(
            project=project,
            title=title,
        )

    def list_conversations(
        self,
        project,
    ):
        return Conversation.objects.filter(
            project=project,
        ).order_by("-updated_at")

    def get_conversation(
        self,
        project,
        conversation_id,
    ) -> Conversation:
        return Conversation.objects.get(
            id=conversation_id,
            project=project,
        )