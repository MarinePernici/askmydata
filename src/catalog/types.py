from dataclasses import dataclass

from connectors.types import ColumnMetadata, RelationshipMetadata


@dataclass(frozen=True)
class TableMetadata:
    """Metadata describing a table in the Knowledge Catalog."""

    schema: str
    name: str
    columns: tuple[ColumnMetadata, ...]
    relationships: tuple[RelationshipMetadata, ...]

@dataclass(frozen=True)
class KnowledgeCatalog:
    """Structured representation of an external data source schema."""

    tables: tuple[TableMetadata, ...]


