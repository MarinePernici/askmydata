from django.db.models import Max, Q

from apps.conversations.models import Conversation, Message
from apps.runs.models import QuestionRun
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

        message = Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            sequence_number=next_sequence,
        )

        conversation.save(
            update_fields=["updated_at"],
        )

        return message

    def get_history(
        self,
        conversation: Conversation,
        max_messages: int = 20,
    ) -> tuple[ConversationMessage, ...]:
        messages = list(
            conversation.messages.exclude(
                Q(question_run__status=QuestionRun.Status.FAILED)
                | Q(generated_by_run__status=QuestionRun.Status.FAILED)
            ).order_by("-sequence_number")[:max_messages]
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

    def set_title_from_question(
        self,
        conversation: Conversation,
        question: str,
        max_length: int = 80,
    ) -> None:
        if conversation.title:
            return

        title = question.strip()

        if len(title) > max_length:
            title = f"{title[: max_length - 1].rstrip()}…"

        conversation.title = title
        conversation.save(
            update_fields=[
                "title",
                "updated_at",
            ]
        )

    def rename_conversation(
        self,
        conversation: Conversation,
        title: str,
    ) -> Conversation:
        conversation.title = title.strip()
        conversation.save(
            update_fields=[
                "title",
                "updated_at",
            ]
        )
        return conversation
