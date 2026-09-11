import unittest

from catalog.types import (
    CatalogScope,
    CatalogTableSelection,
    SemanticMetadata,
    TableMetadata,
)


class CatalogScopeTests(unittest.TestCase):
    def test_catalog_scope_contains_selected_tables(self):
        scope = CatalogScope(
            tables=(
                CatalogTableSelection(
                    schema="sales",
                    table="customers",
                ),
                CatalogTableSelection(
                    schema="sales",
                    table="orders",
                ),
            )
        )

        self.assertEqual(len(scope.tables), 2)
        self.assertEqual(
            scope.tables[0],
            CatalogTableSelection(
                schema="sales",
                table="customers",
            ),
        )

    def test_catalog_scope_can_be_empty(self):
        scope = CatalogScope(tables=())

        self.assertEqual(scope.tables, ())


class TableMetadataTests(unittest.TestCase):
    def test_table_metadata_can_exist_without_semantic_metadata(self):
        table = TableMetadata(
            schema="sales",
            name="orders",
            columns=(),
            relationships=(),
        )

        self.assertIsNone(table.semantic_metadata)

    def test_table_metadata_can_contain_semantic_metadata(self):
        semantic_metadata = SemanticMetadata(
            description="Customer orders recorded in the sales system.",
            business_synonyms=(
                "sales orders",
                "purchases",
            ),
        )

        table = TableMetadata(
            schema="sales",
            name="orders",
            columns=(),
            relationships=(),
            semantic_metadata=semantic_metadata,
        )

        self.assertEqual(
            table.semantic_metadata,
            semantic_metadata,
        )
        self.assertEqual(
            table.semantic_metadata.description,
            "Customer orders recorded in the sales system.",
        )
        self.assertEqual(
            table.semantic_metadata.business_synonyms,
            (
                "sales orders",
                "purchases",
            ),
        )