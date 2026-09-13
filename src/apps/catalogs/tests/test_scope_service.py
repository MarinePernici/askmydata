from unittest.mock import patch

from django.test import TestCase

from apps.catalogs.scope_service import (
    CatalogScopeService,
    InvalidCatalogScopeSelectionError,
)
from apps.data_sources.models import DataSource
from apps.projects.tests.factories import create_test_project


class FakeConnector:
    def discover_schemas(self):
        return ["public", "sales"]

    def discover_tables(self, schema):
        return {
            "public": ["customers", "orders"],
            "sales": ["invoices"],
        }[schema]


class CatalogScopeServiceTests(TestCase):
    def test_discovers_available_tables_grouped_by_schema(self):
        project = create_test_project()

        service = CatalogScopeService(
            connector_factory=lambda project: FakeConnector(),
        )

        result = service.discover_available_tables(project)

        self.assertEqual(
            result,
            {
                "public": ["customers", "orders"],
                "sales": ["invoices"],
            },
        )

    @patch("apps.catalogs.scope_service.PostgreSQLConnector")
    def test_builds_connector_from_project_data_source(self, connector_class):
        project = create_test_project()

        data_source = DataSource.objects.create(
            project=project,
            host="localhost",
            port=5432,
            database="external_db",
            username="readonly",
        )
        data_source.set_password("secret")
        data_source.save()

        connector = connector_class.return_value
        connector.discover_schemas.return_value = []

        service = CatalogScopeService()

        service.discover_available_tables(project)

        connector_class.assert_called_once_with(
            data_source.to_connection_config(),
        )

    def test_rejects_selection_outside_available_tables(self):
        project = create_test_project()

        service = CatalogScopeService(
            connector_factory=lambda project: FakeConnector(),
        )

        selections = [
            {"schema": "sales", "table": "customers"},
            {"schema": "secret", "table": "admin_users"},
        ]

        available_tables = {
            "sales": ["customers", "orders"],
        }

        with self.assertRaises(InvalidCatalogScopeSelectionError):
            service.save_selection(
                project=project,
                selections=selections,
                available_tables=available_tables,
            )

        self.assertFalse(
            hasattr(project, "catalog_scope"),
        )

    def test_saves_valid_selection(self):
        project = create_test_project()

        service = CatalogScopeService(
            connector_factory=lambda project: FakeConnector(),
        )

        selections = [
            {"schema": "sales", "table": "customers"},
            {"schema": "sales", "table": "orders"},
        ]

        available_tables = {
            "sales": ["customers", "orders"],
        }

        catalog_scope = service.save_selection(
            project=project,
            selections=selections,
            available_tables=available_tables,
        )

        self.assertEqual(
            catalog_scope.selected_tables,
            selections,
        )

        project.refresh_from_db()

        self.assertEqual(
            project.catalog_scope.selected_tables,
            selections,
        )
            