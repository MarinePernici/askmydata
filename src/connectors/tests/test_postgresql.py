import os
import unittest

import environ

from connectors.postgresql import (
    PostgreSQLConnectionConfig,
    PostgreSQLConnector,
)
from connectors.types import ColumnMetadata, RelationshipMetadata


ROOT_DIR = environ.Path(__file__) - 4
environ.Env.read_env(ROOT_DIR(".env"))


class PostgreSQLConnectorTests(unittest.TestCase):
    def setUp(self):
        self.config = PostgreSQLConnectionConfig(
            host=os.environ["TEST_SOURCE_DB_HOST"],
            port=int(os.environ["TEST_SOURCE_DB_PORT"]),
            database=os.environ["TEST_SOURCE_DB_NAME"],
            user=os.environ["TEST_SOURCE_DB_USER"],
            password=os.environ["TEST_SOURCE_DB_PASSWORD"],
        )

    def test_connection_succeeds_with_valid_credentials(self):
        connector = PostgreSQLConnector(self.config)

        self.assertTrue(connector.test_connection())

    def test_connection_fails_with_invalid_password(self):
        invalid_config = PostgreSQLConnectionConfig(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password="invalid-password",
        )
        connector = PostgreSQLConnector(invalid_config)

        self.assertFalse(connector.test_connection())

    def test_discover_schemas_returns_accessible_user_schemas(self):
        connector = PostgreSQLConnector(self.config)

        schemas = connector.discover_schemas()

        self.assertIn("public", schemas)
        self.assertIn("sales", schemas)
        self.assertNotIn("pg_catalog", schemas)
        self.assertNotIn("information_schema", schemas)

    def test_discover_tables_returns_tables_from_requested_schema(self):
        connector = PostgreSQLConnector(self.config)

        tables = connector.discover_tables("sales")

        self.assertEqual(tables, ["customers", "orders"])

    def test_discover_columns_returns_column_metadata(self):
        connector = PostgreSQLConnector(self.config)

        columns = connector.discover_columns("sales", "customers")

        self.assertEqual(
            columns,
            [
                ColumnMetadata(
                    name="id",
                    data_type="bigint",
                    nullable=False,
                    default="nextval('sales.customers_id_seq'::regclass)",
                ),
                ColumnMetadata(
                    name="name",
                    data_type="character varying",
                    nullable=False,
                    default=None,
                ),
                ColumnMetadata(
                    name="email",
                    data_type="character varying",
                    nullable=True,
                    default=None,
                ),
            ],
        )

    def test_discover_columns_handles_multiple_postgresql_types(self):
        connector = PostgreSQLConnector(self.config)

        columns = connector.discover_columns("sales", "orders")

        self.assertEqual(
            [column.name for column in columns],
            ["id", "customer_id", "amount", "created_at"],
        )

        self.assertEqual(columns[1].data_type, "bigint")
        self.assertEqual(columns[1].nullable, False)

        self.assertEqual(columns[2].data_type, "numeric")
        self.assertEqual(columns[2].nullable, False)

        self.assertEqual(
            columns[3].data_type,
            "timestamp with time zone",
        )
        self.assertEqual(columns[3].nullable, False)

    def test_discover_relationships_returns_outgoing_foreign_keys(self):
        connector = PostgreSQLConnector(self.config)

        relationships = connector.discover_relationships("sales", "orders")

        self.assertEqual(
            relationships,
            [
                RelationshipMetadata(
                    source_schema="sales",
                    source_table="orders",
                    source_column="customer_id",
                    target_schema="sales",
                    target_table="customers",
                    target_column="id",
                )
            ],
        )

    def test_discover_relationships_returns_incoming_foreign_keys(self):
        connector = PostgreSQLConnector(self.config)

        relationships = connector.discover_relationships("sales", "customers")

        self.assertEqual(
            relationships,
            [
                RelationshipMetadata(
                    source_schema="sales",
                    source_table="orders",
                    source_column="customer_id",
                    target_schema="sales",
                    target_table="customers",
                    target_column="id",
                )
            ],
        )


