import unittest

from catalog.types import KnowledgeCatalog, SemanticMetadata, TableMetadata
from connectors.types import ColumnMetadata
from query_engine.catalog_serializer import CatalogSerializer


class CatalogSerializerTests(unittest.TestCase):
    def test_serialize_includes_tables_and_columns(self):
        catalog = KnowledgeCatalog(
            tables=(
                TableMetadata(
                    schema="sales",
                    name="customers",
                    columns=(
                        ColumnMetadata(
                            name="id",
                            data_type="bigint",
                            nullable=False,
                            default=None,
                        ),
                        ColumnMetadata(
                            name="email",
                            data_type="character varying",
                            nullable=True,
                            default=None,
                        ),
                    ),
                    relationships=(),
                ),
            )
        )

        serializer = CatalogSerializer()

        result = serializer.serialize(catalog)

        self.assertIn("TABLE sales.customers", result)
        self.assertIn("COLUMN id bigint NOT NULL", result)
        self.assertIn(
            "COLUMN email character varying NULL",
            result,
        )

    def test_serialize_includes_semantic_metadata(self):
        catalog = KnowledgeCatalog(
            tables=(
                TableMetadata(
                    schema="sales",
                    name="orders",
                    columns=(),
                    relationships=(),
                    semantic_metadata=SemanticMetadata(
                        description="Customer orders",
                        business_synonyms=("sales orders", "purchases"),
                    ),
                ),
            )
        )

        serializer = CatalogSerializer()

        result = serializer.serialize(catalog)

        self.assertIn(
            "DESCRIPTION Customer orders",
            result,
        )
        self.assertIn(
            "SYNONYMS sales orders, purchases",
            result,
        )