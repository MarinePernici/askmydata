from catalog.types import KnowledgeCatalog


class CatalogSerializer:
    """Serialize a Knowledge Catalog for use as LLM context."""

    def serialize(self, catalog: KnowledgeCatalog) -> str:
        lines: list[str] = []

        for table in catalog.tables:
            lines.append(f"TABLE {table.schema}.{table.name}")

            for column in table.columns:
                nullable = "NULL" if column.nullable else "NOT NULL"
                lines.append(
                    f"  COLUMN {column.name} {column.data_type} {nullable}"
                )

            for relationship in table.relationships:
                lines.append(
                    "  FOREIGN KEY "
                    f"{relationship.source_schema}."
                    f"{relationship.source_table}."
                    f"{relationship.source_column} -> "
                    f"{relationship.target_schema}."
                    f"{relationship.target_table}."
                    f"{relationship.target_column}"
                )

        return "\n".join(lines)