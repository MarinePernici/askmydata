from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnMetadata:
    """Technology-independent metadata describing a table column."""

    name: str
    data_type: str
    nullable: bool
    default: str | None
    is_primary_key: bool = False


@dataclass(frozen=True)
class RelationshipMetadata:
    """Technology-independent metadata describing a foreign-key relationship."""

    source_schema: str
    source_table: str
    source_column: str
    target_schema: str
    target_table: str
    target_column: str
