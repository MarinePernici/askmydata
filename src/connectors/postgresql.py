from dataclasses import dataclass
import psycopg

from connectors.base import Connector
from connectors.types import ColumnMetadata, RelationshipMetadata


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

    def _connect(self) -> psycopg.Connection:
        """Create a connection to the configured PostgreSQL data source."""
        return psycopg.connect(
            host=self._config.host,
            port=self._config.port,
            dbname=self._config.database,
            user=self._config.user,
            password=self._config.password,
        )

    def test_connection(self) -> bool:
        """Check whether the PostgreSQL data source can be reached."""
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()

            return True
        except psycopg.Error:
            return False

    def discover_schemas(self) -> list[str]:
        """Return the user-accessible schemas in the PostgreSQL data source."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
                    AND schema_name NOT LIKE 'pg_toast%%'
                    AND schema_name NOT LIKE 'pg_temp_%%'
                    ORDER BY schema_name
                    """
                )

                return [row[0] for row in cursor.fetchall()]

    def discover_tables(self, schema: str) -> list[str]:
        """Return the tables available in the given PostgreSQL schema."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = %s
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """,
                    (schema,),
                )

                return [row[0] for row in cursor.fetchall()]

    def discover_columns(
        self,
        schema: str,
        table: str,
    ) -> list[ColumnMetadata]:
        """Return metadata for the columns of the given PostgreSQL table."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        c.column_name,
                        c.data_type,
                        c.is_nullable,
                        c.column_default,
                        CASE WHEN pk.attname IS NOT NULL THEN TRUE ELSE FALSE END
                    FROM information_schema.columns AS c
                    LEFT JOIN (
                        SELECT
                            ns.nspname AS table_schema,
                            tbl.relname AS table_name,
                            att.attname
                        FROM pg_catalog.pg_constraint AS con
                        JOIN pg_catalog.pg_class AS tbl
                            ON tbl.oid = con.conrelid
                        JOIN pg_catalog.pg_namespace AS ns
                            ON ns.oid = tbl.relnamespace
                        JOIN pg_catalog.pg_attribute AS att
                            ON att.attrelid = tbl.oid
                            AND att.attnum = ANY(con.conkey)
                        WHERE con.contype = 'p'
                    ) AS pk
                        ON c.table_schema = pk.table_schema
                        AND c.table_name = pk.table_name
                        AND c.column_name = pk.attname
                    WHERE c.table_schema = %s
                    AND c.table_name = %s
                    ORDER BY c.ordinal_position
                    """,
                    (schema, table),
                )

                return [
                    ColumnMetadata(
                        name=row[0],
                        data_type=row[1],
                        nullable=row[2] == "YES",
                        default=row[3],
                        is_primary_key=row[4],
                    )
                    for row in cursor.fetchall()
                ]

    def discover_relationships(
        self,
        schema: str,
        table: str,
    ) -> list[RelationshipMetadata]:
        """Return foreign-key relationships involving the given PostgreSQL table."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        source_ns.nspname AS source_schema,
                        source_table.relname AS source_table,
                        source_column.attname AS source_column,
                        target_ns.nspname AS target_schema,
                        target_table.relname AS target_table,
                        target_column.attname AS target_column
                    FROM pg_constraint AS fk
                    JOIN pg_class AS source_table
                        ON source_table.oid = fk.conrelid
                    JOIN pg_namespace AS source_ns
                        ON source_ns.oid = source_table.relnamespace
                    JOIN pg_class AS target_table
                        ON target_table.oid = fk.confrelid
                    JOIN pg_namespace AS target_ns
                        ON target_ns.oid = target_table.relnamespace
                    JOIN LATERAL unnest(
                        fk.conkey,
                        fk.confkey
                    ) AS columns(source_attnum, target_attnum)
                        ON TRUE
                    JOIN pg_attribute AS source_column
                        ON source_column.attrelid = source_table.oid
                        AND source_column.attnum = columns.source_attnum
                    JOIN pg_attribute AS target_column
                        ON target_column.attrelid = target_table.oid
                        AND target_column.attnum = columns.target_attnum
                    WHERE fk.contype = 'f'
                    AND (
                        (source_ns.nspname = %s AND source_table.relname = %s)
                        OR
                        (target_ns.nspname = %s AND target_table.relname = %s)
                    )
                    ORDER BY
                        source_ns.nspname,
                        source_table.relname,
                        source_column.attname
                    """,
                    (schema, table, schema, table),
                )

                return [
                    RelationshipMetadata(
                        source_schema=row[0],
                        source_table=row[1],
                        source_column=row[2],
                        target_schema=row[3],
                        target_table=row[4],
                        target_column=row[5],
                    )
                    for row in cursor.fetchall()
                ]
