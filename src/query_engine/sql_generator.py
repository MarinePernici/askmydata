import json

from catalog.types import KnowledgeCatalog
from llm.base import LLMProvider
from llm.types import LLMMessage
from query_engine.catalog_serializer import CatalogSerializer
from query_engine.exceptions import SQLGenerationError
from query_engine.types import SQLGenerationResult


class SQLGenerator:
    """Generate SQL from a natural-language question and a Knowledge Catalog."""

    def __init__(
        self,
        provider: LLMProvider,
        serializer: CatalogSerializer | None = None,
    ) -> None:
        self._provider = provider
        self._serializer = serializer or CatalogSerializer()

    def generate(
        self,
        question: str,
        catalog: KnowledgeCatalog,
    ) -> SQLGenerationResult:
        catalog_context = self._serializer.serialize(catalog)

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

            sql = payload["sql"]
            explanation = payload["explanation"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise SQLGenerationError(
                "The LLM returned an invalid SQL generation response."
            ) from exc

        return SQLGenerationResult(
            sql=sql,
            explanation=explanation,
        )