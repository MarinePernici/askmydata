from catalog.types import (
    CatalogScope,
    KnowledgeCatalog,
    TableMetadata,
)


class CatalogBuilder:
    def __init__(self, connector):
        self._connector = connector

    def build(
        self,
        scope: CatalogScope | None = None,
    ) -> KnowledgeCatalog:
        tables = []

        if scope is None:
            schemas = self._connector.discover_schemas()

            selections = [
                (schema, table)
                for schema in schemas
                for table in self._connector.discover_tables(schema)
            ]
        else:
            selections = [
                (selection.schema, selection.table)
                for selection in scope.tables
            ]

        for schema, table in selections:
            columns = tuple(
                self._connector.discover_columns(
                    schema,
                    table,
                )
            )

            relationships = tuple(
                self._connector.discover_relationships(
                    schema,
                    table,
                )
            )

            tables.append(
                TableMetadata(
                    schema=schema,
                    name=table,
                    columns=columns,
                    relationships=relationships,
                )
            )

        return KnowledgeCatalog(
            tables=tuple(tables),
        )