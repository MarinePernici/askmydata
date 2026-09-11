import unittest

from catalog.exceptions import SemanticEnrichmentError
from catalog.semantic_enricher import SemanticEnricher
from catalog.types import KnowledgeCatalog, TableMetadata, ColumnMetadata
from connectors.types import RelationshipMetadata
from llm.types import LLMResponse


class FakeLLMProvider:
    def generate(self, messages):
        return LLMResponse(
            content=(
                '{"description": "Customer orders recorded in the sales system.", '
                '"business_synonyms": ["sales orders", "purchases"]}'
            ),
            model="fake-model",
        )


class InvalidJSONProvider:
    def generate(self, messages):
        return LLMResponse(
            content="This is not valid JSON",
            model="fake-model",
        )


class MissingFieldProvider:
    def generate(self, messages):
        return LLMResponse(
            content='{"description": "Customer orders"}',
            model="fake-model",
        )


class InvalidFieldTypeProvider:
    def generate(self, messages):
        return LLMResponse(
            content=(
                '{"description": "Customer orders", '
                '"business_synonyms": "orders"}'
            ),
            model="fake-model",
        )


class PartiallyFailingProvider:
    def __init__(self):
        self.call_count = 0

    def generate(self, messages):
        self.call_count += 1

        if self.call_count == 1:
            return LLMResponse(
                content=(
                    '{"description": "Customer data", '
                    '"business_synonyms": ["customers"]}'
                ),
                model="fake-model",
            )

        return LLMResponse(
            content="invalid json",
            model="fake-model",
        )


class CapturingProvider:
    def __init__(self):
        self.messages = None

    def generate(self, messages):
        self.messages = messages

        return LLMResponse(
            content=(
                '{"description": "Customer orders", '
                '"business_synonyms": ["orders"]}'
            ),
            model="fake-model",
        )


class SemanticEnricherTests(unittest.TestCase):
    def test_enrich_table_adds_semantic_metadata(self):
        table = TableMetadata(
            schema="sales",
            name="orders",
            columns=(),
            relationships=(),
        )

        enricher = SemanticEnricher(
            provider=FakeLLMProvider(),
        )

        enriched_table = enricher.enrich_table(table)

        self.assertEqual(
            enriched_table.semantic_metadata.description,
            "Customer orders recorded in the sales system.",
        )
        self.assertEqual(
            enriched_table.semantic_metadata.business_synonyms,
            (
                "sales orders",
                "purchases",
            ),
        )

        self.assertIsNone(
            table.semantic_metadata,
        )

    def test_enrich_table_raises_error_when_llm_returns_invalid_json(self):
        table = TableMetadata(
            schema="sales",
            name="orders",
            columns=(),
            relationships=(),
        )

        enricher = SemanticEnricher(
            provider=InvalidJSONProvider(),
        )

        with self.assertRaises(SemanticEnrichmentError):
            enricher.enrich_table(table)

    def test_enrich_table_raises_error_when_required_field_is_missing(self):
        table = TableMetadata(
            schema="sales",
            name="orders",
            columns=(),
            relationships=(),
        )

        enricher = SemanticEnricher(
            provider=MissingFieldProvider(),
        )

        with self.assertRaises(SemanticEnrichmentError):
            enricher.enrich_table(table)

    def test_enrich_table_raises_error_when_field_types_are_invalid(self):
        table = TableMetadata(
            schema="sales",
            name="orders",
            columns=(),
            relationships=(),
        )

        enricher = SemanticEnricher(
            provider=InvalidFieldTypeProvider(),
        )

        with self.assertRaises(SemanticEnrichmentError):
            enricher.enrich_table(table)

    def test_enrich_catalog_enriches_all_tables(self):
        catalog = KnowledgeCatalog(
            tables=(
                TableMetadata(
                    schema="sales",
                    name="customers",
                    columns=(),
                    relationships=(),
                ),
                TableMetadata(
                    schema="sales",
                    name="orders",
                    columns=(),
                    relationships=(),
                ),
            )
        )

        enricher = SemanticEnricher(
            provider=FakeLLMProvider(),
        )

        enriched_catalog = enricher.enrich_catalog(catalog)

        self.assertEqual(
            len(enriched_catalog.tables),
            2,
        )

        self.assertIsNotNone(
            enriched_catalog.tables[0].semantic_metadata,
        )
        self.assertIsNotNone(
            enriched_catalog.tables[1].semantic_metadata,
        )

        self.assertIsNone(
            catalog.tables[0].semantic_metadata,
        )
        self.assertIsNone(
            catalog.tables[1].semantic_metadata,
        )

    def test_enrich_catalog_fails_if_one_table_cannot_be_enriched(self):
        catalog = KnowledgeCatalog(
            tables=(
                TableMetadata(
                    schema="sales",
                    name="customers",
                    columns=(),
                    relationships=(),
                ),
                TableMetadata(
                    schema="sales",
                    name="orders",
                    columns=(),
                    relationships=(),
                ),
            )
        )

        enricher = SemanticEnricher(
            provider=PartiallyFailingProvider(),
        )

        with self.assertRaises(SemanticEnrichmentError):
            enricher.enrich_catalog(catalog)

        self.assertIsNone(
            catalog.tables[0].semantic_metadata,
        )
        self.assertIsNone(
            catalog.tables[1].semantic_metadata,
        )

    def test_enrich_table_prompt_includes_columns(self):
        provider = CapturingProvider()

        table = TableMetadata(
            schema="sales",
            name="orders",
            columns=(
                ColumnMetadata(
                    name="id",
                    data_type="bigint",
                    nullable=False,
                    default=None,
                ),
                ColumnMetadata(
                    name="customer_id",
                    data_type="bigint",
                    nullable=False,
                    default=None,
                ),
            ),
            relationships=(),
        )

        enricher = SemanticEnricher(provider=provider)

        enricher.enrich_table(table)

        user_message = provider.messages[1].content

        self.assertIn("id", user_message)
        self.assertIn("bigint", user_message)
        self.assertIn("customer_id", user_message)

    def test_enrich_table_prompt_includes_relationships(self):
        provider = CapturingProvider()

        relationship = RelationshipMetadata(
            source_schema="sales",
            source_table="orders",
            source_column="customer_id",
            target_schema="sales",
            target_table="customers",
            target_column="id",
        )

        table = TableMetadata(
            schema="sales",
            name="orders",
            columns=(),
            relationships=(relationship,),
        )

        enricher = SemanticEnricher(provider=provider)

        enricher.enrich_table(table)

        user_message = provider.messages[1].content

        self.assertIn("customer_id", user_message)
        self.assertIn("sales.customers.id", user_message)