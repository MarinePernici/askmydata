from connectors.base import Connector

from catalog.types import KnowledgeCatalog, TableMetadata


class CatalogBuilder:
    """Build a Knowledge Catalog from an external data source."""

    def __init__(self, connector: Connector) -> None:
        self._connector = connector

    def build(self) -> KnowledgeCatalog:
        """Build a catalog containing all accessible schemas and tables."""
        tables: list[TableMetadata] = []

        for schema in self._connector.discover_schemas():
            for table in self._connector.discover_tables(schema):
                columns = self._connector.discover_columns(schema, table)
                relationships = self._connector.discover_relationships(
                    schema,
                    table,
                )

                tables.append(
                    TableMetadata(
                        schema=schema,
                        name=table,
                        columns=tuple(columns),
                        relationships=tuple(relationships),
                    )
                )

        return KnowledgeCatalog(tables=tuple(tables))