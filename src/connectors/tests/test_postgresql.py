import os
import unittest

import environ

from connectors.postgresql import (
    PostgreSQLConnectionConfig,
    PostgreSQLConnector,
)


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
