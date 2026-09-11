import json

from catalog.exceptions import SemanticEnrichmentError
from catalog.types import KnowledgeCatalog, SemanticMetadata, TableMetadata
from llm.base import LLMProvider
from llm.types import LLMMessage


class SemanticEnricher:
    def __init__(
        self,
        provider: LLMProvider,
    ) -> None:
        self._provider = provider

    def enrich_table(
        self,
        table: TableMetadata,
    ) -> TableMetadata:
        response = self._provider.generate(
            messages=self._build_messages(table)
        )

        semantic_metadata = self._parse_semantic_metadata(
            response.content
        )

        return TableMetadata(
            schema=table.schema,
            name=table.name,
            columns=table.columns,
            relationships=table.relationships,
            semantic_metadata=semantic_metadata,
        )

    def enrich_catalog(
        self,
        catalog: KnowledgeCatalog,
    ) -> KnowledgeCatalog:
        return KnowledgeCatalog(
            tables=tuple(
                self.enrich_table(table)
                for table in catalog.tables
            )
        )

    def _parse_semantic_metadata(
        self,
        content: str,
    ) -> SemanticMetadata:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise SemanticEnrichmentError(
                "LLM returned invalid semantic metadata JSON."
            ) from exc

        try:
            description = payload["description"]
            business_synonyms = payload["business_synonyms"]
        except (KeyError, TypeError) as exc:
            raise SemanticEnrichmentError(
                "LLM semantic metadata is missing required fields."
            ) from exc

        if not isinstance(description, str):
            raise SemanticEnrichmentError(
                "Semantic metadata description must be a string."
            )

        if not isinstance(business_synonyms, list):
            raise SemanticEnrichmentError(
                "Semantic metadata business_synonyms must be a list."
            )

        if not all(
            isinstance(synonym, str)
            for synonym in business_synonyms
        ):
            raise SemanticEnrichmentError(
                "Semantic metadata business_synonyms must contain only strings."
            )

        return SemanticMetadata(
            description=description,
            business_synonyms=tuple(business_synonyms),
        )

    def _build_messages(
        self,
        table: TableMetadata,
    ) -> list[LLMMessage]:
        columns_text = "\n".join(
            f"- {column.name}: {column.data_type}"
            for column in table.columns
        )

        relationships_text = "\n".join(
            (
                f"- {relationship.source_column} -> "
                f"{relationship.target_schema}."
                f"{relationship.target_table}."
                f"{relationship.target_column}"
            )
            for relationship in table.relationships
        )

        return [
            LLMMessage(
                role="system",
                content=(
                    "You generate semantic metadata for database tables. "
                    "Return valid JSON only."
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"Schema: {table.schema}\n"
                    f"Table: {table.name}\n\n"
                    f"Columns:\n{columns_text}\n\n"
                    f"Relationships:\n{relationships_text}\n\n"
                    "Return JSON with exactly these fields:\n"
                    '- "description": string\n'
                    '- "business_synonyms": array of strings'
                ),
            ),
        ]