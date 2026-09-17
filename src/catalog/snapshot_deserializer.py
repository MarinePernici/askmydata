from catalog.types import (
    KnowledgeCatalog,
    SemanticMetadata,
    TableMetadata,
)
from connectors.types import (
    ColumnMetadata,
    RelationshipMetadata,
)


class CatalogSnapshotDeserializer:
    def deserialize(
        self,
        data: dict,
    ) -> KnowledgeCatalog:
        return KnowledgeCatalog(
            tables=tuple(
                TableMetadata(
                    schema=table["schema"],
                    name=table["name"],
                    columns=tuple(
                        ColumnMetadata(
                            name=column["name"],
                            data_type=column["data_type"],
                            nullable=column["nullable"],
                            default=column["default"],
                            is_primary_key=column.get("is_primary_key", False),
                        )
                        for column in table["columns"]
                    ),
                    relationships=tuple(
                        RelationshipMetadata(
                            source_schema=relationship["source_schema"],
                            source_table=relationship["source_table"],
                            source_column=relationship["source_column"],
                            target_schema=relationship["target_schema"],
                            target_table=relationship["target_table"],
                            target_column=relationship["target_column"],
                        )
                        for relationship in table["relationships"]
                    ),
                    semantic_metadata=(
                        SemanticMetadata(
                            description=table["semantic_metadata"]["description"],
                            business_synonyms=tuple(
                                table["semantic_metadata"]["business_synonyms"]
                            ),
                        )
                        if table["semantic_metadata"] is not None
                        else None
                    ),
                )
                for table in data["tables"]
            )
        )
