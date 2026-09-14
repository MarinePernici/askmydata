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
