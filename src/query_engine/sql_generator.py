import json

from catalog.types import KnowledgeCatalog
from llm.base import LLMProvider
from llm.types import LLMMessage
from query_engine.catalog_serializer import CatalogSerializer
from query_engine.exceptions import SQLGenerationError
from query_engine.types import (
    ClarificationResult,
    ConversationMessage,
    SQLGenerationResult,
)


class SQLGenerator:
    """Generate SQL from a natural-language question and a Knowledge Catalog."""

    def __init__(
        self,
        provider: LLMProvider,
        serializer: CatalogSerializer | None = None,
    ) -> None:
        self._provider = provider
        self._serializer = serializer or CatalogSerializer()

    def _serialize_history(
        self,
        history: tuple[ConversationMessage, ...],
    ) -> str:
        if not history:
            return "No previous conversation."

        return "\n".join(f"{message.role}: {message.content}" for message in history)

    def generate(
        self,
        question: str,
        catalog: KnowledgeCatalog,
        history: tuple[ConversationMessage, ...] = (),
    ) -> SQLGenerationResult | ClarificationResult:
        catalog_context = self._serializer.serialize(catalog)
        history_context = self._serialize_history(history)

        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You generate PostgreSQL SELECT queries from natural-language "
                    "questions.\n\n"
                    "Rules:\n"
                    "- Use only the tables and columns present in the catalog.\n"
                    "- Generate read-only SQL only.\n"
                    "- Do not generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, "
                    "TRUNCATE, or other data-modifying statements.\n"
                    "- Return exactly one SQL query.\n"
                    "- Use schema-qualified table names.\n\n"
                    f"Catalog:\n{catalog_context}\n\n"
                    f"Conversation history:\n{history_context}\n\n"
                    "Return a JSON object with exactly these fields:\n"
                    '- "sql": the PostgreSQL query\n'
                    '- "explanation": a short explanation of the query'
                ),
            ),
            LLMMessage(
                role="user",
                content=question,
            ),
        ]

        response = self._provider.generate(messages)

        try:
            payload = json.loads(response.content)
        except (json.JSONDecodeError, TypeError) as exc:
            raise SQLGenerationError(
                "The LLM returned an invalid SQL generation response."
            ) from exc

        if "clarification" in payload:
            clarification = payload["clarification"]

            if not isinstance(clarification, str) or not clarification.strip():
                raise SQLGenerationError(
                    "The LLM returned an invalid SQL generation response."
                )

            return ClarificationResult(
                question=clarification.strip(),
            )

        try:
            sql = payload["sql"]
            explanation = payload["explanation"]
        except (KeyError, TypeError) as exc:
            raise SQLGenerationError(
                "The LLM returned an invalid SQL generation response."
            ) from exc

        return SQLGenerationResult(
            sql=sql,
            explanation=explanation,
        )
