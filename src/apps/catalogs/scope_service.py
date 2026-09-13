from apps.data_sources.models import DataSource
from connectors.postgresql import PostgreSQLConnector

from .models import CatalogScope


def build_connector_for_project(project):
    data_source = DataSource.objects.get(project=project)

    return PostgreSQLConnector(
        data_source.to_connection_config(),
    )


class InvalidCatalogScopeSelectionError(ValueError):
    pass


class CatalogScopeService:
    def __init__(self, connector_factory=build_connector_for_project):
        self.connector_factory = connector_factory

    def discover_available_tables(self, project):
        connector = self.connector_factory(project)

        return {
            schema: connector.discover_tables(schema)
            for schema in connector.discover_schemas()
        }

    def save_selection(
        self,
        project,
        selections,
        available_tables,
    ):
        allowed = {
            (schema, table)
            for schema, tables in available_tables.items()
            for table in tables
        }

        selected = {
            (selection["schema"], selection["table"])
            for selection in selections
        }

        if not selected.issubset(allowed):
            raise InvalidCatalogScopeSelectionError(
                "Invalid table selection."
            )

        catalog_scope, _ = CatalogScope.objects.update_or_create(
            project=project,
            defaults={
                "selected_tables": selections,
            },
        )

        return catalog_scope


