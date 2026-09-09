from dataclasses import dataclass
from typing import Any

import psycopg

from connectors.base import Connector

@dataclass(frozen=True)
class PostgreSQLConnectionConfig:
    host: str
    port: int
    database: str
    user: str
    password: str


class PostgreSQLConnector(Connector):
    def __init__(self, config: PostgreSQLConnectionConfig) -> None:
        self._config = config

    def test_connection(self) -> bool:
        """Check whether the PostgreSQL data source can be reached."""
        try:
            with psycopg.connect(
                host=self._config.host,
                port=self._config.port,
                dbname=self._config.database,
                user=self._config.user,
                password=self._config.password,
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()

            return True
        except psycopg.Error:
            return False

    def discover_schemas(self) -> list[str]:
        raise NotImplementedError

    def discover_tables(self, schema: str) -> list[str]:
        raise NotImplementedError

    def discover_columns(
        self,
        schema: str,
        table: str,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    def discover_relationships(
        self,
        schema: str,
        table: str,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError
