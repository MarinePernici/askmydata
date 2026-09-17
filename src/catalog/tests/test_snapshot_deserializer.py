from django.test import SimpleTestCase

from catalog.snapshot_deserializer import CatalogSnapshotDeserializer
from catalog.snapshot_serializer import CatalogSnapshotSerializer
from catalog.types import (
    KnowledgeCatalog,
    SemanticMetadata,
    TableMetadata,
)
from connectors.types import (
    ColumnMetadata,
    RelationshipMetadata,
)


class CatalogSnapshotDeserializerTests(SimpleTestCase):
    def test_serialized_catalog_can_be_deserialized(self):
        catalog = KnowledgeCatalog(
            tables=(
                TableMetadata(
                    schema="sales",
                    name="orders",
                    columns=(
                        ColumnMetadata(
                            name="id",
                            data_type="integer",
                            nullable=False,
                            default=None,
                            is_primary_key=True,
                        ),
                    ),
                    relationships=(
                        RelationshipMetadata(
                            source_schema="sales",
                            source_table="orders",
                            source_column="customer_id",
                            target_schema="sales",
                            target_table="customers",
                            target_column="id",
                        ),
                    ),
                    semantic_metadata=SemanticMetadata(
                        description="Customer orders",
                        business_synonyms=(
                            "sales orders",
                            "purchases",
                        ),
                    ),
                ),
            )
        )

        serialized = CatalogSnapshotSerializer().serialize(catalog)

        deserialized = CatalogSnapshotDeserializer().deserialize(serialized)

        self.assertEqual(
            deserialized,
            catalog,
        )

    def test_deserialize_legacy_snapshot_without_primary_key_metadata(self):
        data = {
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
        }

        catalog = CatalogSnapshotDeserializer().deserialize(data)

        self.assertFalse(
            catalog.tables[0].columns[0].is_primary_key,
        )
