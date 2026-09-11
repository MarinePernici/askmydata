from dataclasses import dataclass

from connectors.types import ColumnMetadata, RelationshipMetadata


@dataclass(frozen=True)
class SemanticMetadata:
    description: str
    business_synonyms: tuple[str, ...]

@dataclass(frozen=True)
class TableMetadata:
    """Metadata describing a table in the Knowledge Catalog."""

    schema: str
    name: str
    columns: tuple[ColumnMetadata, ...]
    relationships: tuple[RelationshipMetadata, ...]
    semantic_metadata: SemanticMetadata | None = None

@dataclass(frozen=True)
class KnowledgeCatalog:
    """Structured representation of an external data source schema."""

    tables: tuple[TableMetadata, ...]


@dataclass(frozen=True)
class CatalogTableSelection:
    schema: str
    table: str


@dataclass(frozen=True)
class CatalogScope:
    tables: tuple[CatalogTableSelection, ...]





