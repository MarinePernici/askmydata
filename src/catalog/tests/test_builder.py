import environ
import os
import unittest

from catalog.builder import CatalogBuilder
from catalog.types import KnowledgeCatalog, TableMetadata
from connectors.base import Connector
from connectors.postgresql import (
    PostgreSQLConnectionConfig,
    PostgreSQLConnector,
)
from connectors.types import ColumnMetadata, RelationshipMetadata


ROOT_DIR = environ.Path(__file__) - 4
environ.Env.read_env(ROOT_DIR(".env"))


class FakeConnector(Connector):
    def test_connection(self) -> bool:
        return True

    def discover_schemas(self) -> list[str]:
        return ["sales"]

    def discover_tables(self, schema: str) -> list[str]:
        return ["customers", "orders"]

    def discover_columns(
        self,
        schema: str,
        table: str,
    ) -> list[ColumnMetadata]:
        return [
            ColumnMetadata(
                name="id",
                data_type="bigint",
                nullable=False,
                default=None,
            )
        ]

    def discover_relationships(
        self,
        schema: str,
        table: str,
    ) -> list[RelationshipMetadata]:
        if schema == "sales" and table in {"customers", "orders"}:
            return [
                RelationshipMetadata(
                    source_schema="sales",
                    source_table="orders",
                    source_column="customer_id",
                    target_schema="sales",
                    target_table="customers",
                    target_column="id",
                )
            ]

        return []


class KnowledgeCatalogTests(unittest.TestCase):
    def test_catalog_can_represent_table_metadata(self):
        column = ColumnMetadata(
            name="id",
            data_type="bigint",
            nullable=False,
            default=None,
        )

        table = TableMetadata(
            schema="sales",
            name="customers",
            columns=(column,),
            relationships=(),
        )

        catalog = KnowledgeCatalog(tables=(table,))

        self.assertEqual(catalog.tables[0].schema, "sales")
        self.assertEqual(catalog.tables[0].name, "customers")
        self.assertEqual(catalog.tables[0].columns, (column,))

    def test_builder_builds_catalog_from_connector(self):
        connector = FakeConnector()
        builder = CatalogBuilder(connector)

        catalog = builder.build()

        self.assertEqual(
            [(table.schema, table.name) for table in catalog.tables],
            [
                ("sales", "customers"),
                ("sales", "orders"),
            ],
        )

        self.assertEqual(
            catalog.tables[0].columns[0].name,
            "id",
        )

    def test_builder_includes_table_relationships(self):
        connector = FakeConnector()
        builder = CatalogBuilder(connector)

        catalog = builder.build()

        orders = next(
            table
            for table in catalog.tables
            if table.schema == "sales" and table.name == "orders"
        )

        self.assertEqual(
            orders.relationships,
            (
                RelationshipMetadata(
                    source_schema="sales",
                    source_table="orders",
                    source_column="customer_id",
                    target_schema="sales",
                    target_table="customers",
                    target_column="id",
                ),
            ),
        )

    def test_builder_builds_catalog_from_postgresql_connector(self):
        config = PostgreSQLConnectionConfig(
            host=os.environ["TEST_SOURCE_DB_HOST"],
            port=int(os.environ["TEST_SOURCE_DB_PORT"]),
            database=os.environ["TEST_SOURCE_DB_NAME"],
            user=os.environ["TEST_SOURCE_DB_USER"],
            password=os.environ["TEST_SOURCE_DB_PASSWORD"],
        )

        connector = PostgreSQLConnector(config)
        builder = CatalogBuilder(connector)

        catalog = builder.build()

        tables = {
            (table.schema, table.name): table
            for table in catalog.tables
        }

        self.assertIn(("sales", "customers"), tables)
        self.assertIn(("sales", "orders"), tables)

        orders = tables[("sales", "orders")]

        self.assertEqual(
            [column.name for column in orders.columns],
            ["id", "customer_id", "amount", "created_at"],
        )

        self.assertIn(
            RelationshipMetadata(
                source_schema="sales",
                source_table="orders",
                source_column="customer_id",
                target_schema="sales",
                target_table="customers",
                target_column="id",
            ),
            orders.relationships,
        )