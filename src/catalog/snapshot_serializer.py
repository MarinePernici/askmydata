from catalog.types import KnowledgeCatalog


class CatalogSnapshotSerializer:
    def serialize(
        self,
        catalog: KnowledgeCatalog,
    ) -> dict:
        return {
            "tables": [
                {
                    "schema": table.schema,
                    "name": table.name,
                    "columns": [
                        {
                            "name": column.name,
                            "data_type": column.data_type,
                            "nullable": column.nullable,
                            "default": column.default,
                        }
                        for column in table.columns
                    ],
                    "relationships": [
                        {
                            "source_schema": relationship.source_schema,
                            "source_table": relationship.source_table,
                            "source_column": relationship.source_column,
                            "target_schema": relationship.target_schema,
                            "target_table": relationship.target_table,
                            "target_column": relationship.target_column,
                        }
                        for relationship in table.relationships
                    ],
                    "semantic_metadata": (
                        {
                            "description": table.semantic_metadata.description,
                            "business_synonyms": list(
                                table.semantic_metadata.business_synonyms
                            ),
                        }
                        if table.semantic_metadata is not None
                        else None
                    ),
                }
                for table in catalog.tables
            ]
        }
