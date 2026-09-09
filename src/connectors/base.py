from abc import ABC, abstractmethod
from typing import Any


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
    ) -> list[dict[str, Any]]:
        """Return metadata for the columns of the given table."""
        raise NotImplementedError

    @abstractmethod
    def discover_relationships(
        self,
        schema: str,
        table: str,
    ) -> list[dict[str, Any]]:
        """Return metadata for relationships involving the given table."""
        raise NotImplementedError
