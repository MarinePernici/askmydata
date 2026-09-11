import unittest

from catalog.snapshot_serializer import CatalogSnapshotSerializer
from catalog.types import KnowledgeCatalog, TableMetadata, SemanticMetadata
from connectors.types import ColumnMetadata, RelationshipMetadata


class CatalogSnapshotSerializerTests(unittest.TestCase):
    def test_serialize_catalog_with_table_and_column(self):
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
                    ),
                    relationships=()
                ),
            )
        )

        serializer = CatalogSnapshotSerializer()

        result = serializer.serialize(catalog)

        self.assertEqual(
            result,
            {
                "tables": [
                    {
                        "schema": "sales",
                        "name": "customers",
                        "columns": [
                            {
                                "name": "id",
                                "data_type": "bigint",
                                "nullable": False,
                                "default": None,
                            }
                        ],
                        "relationships": [],
                        "semantic_metadata": None,
                    }
                ]
            },
        )

    def test_serialize_catalog_with_relationship(self):
        relationship = RelationshipMetadata(
            source_schema="sales",
            source_table="orders",
            source_column="customer_id",
            target_schema="sales",
            target_table="customers",
            target_column="id",
        )

        catalog = KnowledgeCatalog(
            tables=(
                TableMetadata(
                    schema="sales",
                    name="orders",
                    columns=(),
                    relationships=(relationship,),
                ),
            )
        )

        serializer = CatalogSnapshotSerializer()

        result = serializer.serialize(catalog)

        self.assertEqual(
            result["tables"][0]["relationships"],
            [
                {
                    "source_schema": "sales",
                    "source_table": "orders",
                    "source_column": "customer_id",
                    "target_schema": "sales",
                    "target_table": "customers",
                    "target_column": "id",
                }
            ],
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

        result = CatalogSnapshotSerializer().serialize(catalog)

        self.assertEqual(
            result["tables"][0]["semantic_metadata"],
            {
                "description": "Customer orders",
                "business_synonyms": [
                    "sales orders",
                    "purchases",
                ],
            },
        )