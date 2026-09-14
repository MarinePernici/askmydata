from abc import ABC, abstractmethod
from connectors.types import ColumnMetadata, RelationshipMetadata


class Connector(ABC):
    """Abstract interface for inspecting an external data source."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Return whether a connection to the data source can be established."""
        raise NotImplementedError

    @abstractmethod
    def discover_schemas(self) -> list[str]:
        """Return the schemas available in the data source."""
        raise NotImplementedError

    @abstractmethod
    def discover_tables(self, schema: str) -> list[str]:
        """Return the tables available in the given schema."""
        raise NotImplementedError

    @abstractmethod
    def discover_columns(
        self,
        schema: str,
        table: str,
    ) -> list[ColumnMetadata]:
        """Return metadata for the columns of the given table."""
        raise NotImplementedError

    @abstractmethod
    def discover_relationships(
        self,
        schema: str,
        table: str,
    ) -> list[RelationshipMetadata]:
        """Return foreign-key relationships involving the given table."""
        raise NotImplementedError
