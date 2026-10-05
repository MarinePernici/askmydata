import json

from catalog.types import KnowledgeCatalog
from config.observability import traced_llm_call
from llm.base import LLMProvider
from llm.types import LLMMessage
from query_engine.catalog_serializer import CatalogSerializer
from query_engine.exceptions import SQLGenerationError
from query_engine.types import (
    CannotAnswerResult,
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
    ) -> SQLGenerationResult | ClarificationResult | CannotAnswerResult:
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
                    "- Use schema-qualified table names.\n"
                    "- If the question is ambiguous and different reasonable interpretations "
                    "would materially change the query, do not choose an interpretation "
                    "yourself.\n"
                    "- Ask one concise clarification question instead.\n"
                    "- Do not ask for clarification when the intended query can be determined "
                    "unambiguously from the question, catalog, and conversation history.\n"
                    "- Do not invent or assume business definitions, metrics, formulas, or "
                    "relationships that are not established by the catalog, the user's question, "
                    "or the conversation history.\n"
                    "- If a requested business metric cannot be derived from the catalog and no "
                    "definition is provided by the user or conversation history, ask for the "
                    "missing definition instead of substituting another metric.\n"
                    "- You may suggest alternative meanings for an ambiguous qualitative term "
                    "(for example, different ways to interpret a ranking criterion).\n"
                    "- Never suggest candidate formulas for a missing quantitative business "
                    "metric. If its calculation is not defined by the catalog or conversation "
                    "history, ask the user to provide the definition without giving formula "
                    "examples.\n"
                    "- If the question requires information that is not represented in or "
                    "derivable from the catalog, the user's question, or the conversation "
                    "history, do not use external knowledge, make assumptions, or force the "
                    "question into available tables or columns.\n"
                    "- In that case, return cannot_answer instead of generating SQL or asking "
                    "for clarification.\n"
                    "- Preserve explicit constraints from the user's question and conversation "
                    "history, including singular/plural intent, requested counts, filters, "
                    "date ranges, and ordering.\n"
                    "- When the user asks for multiple ranked results without specifying a "
                    "count, choose a reasonable result limit rather than returning only one "
                    "result.\n\n"
                    f"Catalog:\n{catalog_context}\n\n"
                    f"Conversation history:\n{history_context}\n\n"
                    "Return exactly one JSON object.\n\n"
                    "If the question can be answered unambiguously, return exactly "
                    "these fields:\n"
                    '- "sql": the PostgreSQL query\n'
                    '- "explanation": a short explanation of the query\n\n'
                    "If clarification is required, return exactly this field:\n"
                    '- "clarification": one concise question asking for the missing '
                    "information.\n\n"
                    "If the question cannot be answered from the available project data, "
                    "return exactly this field:\n"
                    '- "cannot_answer": true'
                ),
            ),
            LLMMessage(
                role="user",
                content=question,
            ),
        ]

        with traced_llm_call("sql_generation") as span:
            response = self._provider.generate(messages)
            if span is not None:
                span.set_attribute("llm.model", response.usage.model)

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
                usages=(response.usage,),
            )

        if payload.get("cannot_answer") is True:
            return CannotAnswerResult(
                usages=(response.usage,),
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
            usage=response.usage,
        )
