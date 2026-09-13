from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalogs.models import CatalogScope
from apps.data_sources.models import DataSource
from apps.projects.models import Project


class CatalogScopeViewTests(TestCase):
    def test_user_cannot_access_catalog_scope_for_another_users_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="other-user",
            password="test-password",
        )

        project = Project.objects.create(
            owner=other_user,
            name="Other project",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)

    @patch("apps.catalogs.views.CatalogScopeService")
    def test_user_can_access_catalog_scope_for_own_project(
        self,
        catalog_scope_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        catalog_scope_service_class.return_value.discover_available_tables.return_value = {}

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, project.name)

    @patch("apps.catalogs.views.CatalogScopeService")
    def test_catalog_scope_displays_discovered_tables(
        self,
        catalog_scope_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        DataSource.objects.create(
            project=project,
        )

        catalog_scope_service_class.return_value.discover_available_tables.return_value = {
            "sales": ["customers", "orders"],
        }

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "sales.customers")
        self.assertContains(response, "sales.orders")

    def test_catalog_scope_without_data_source_displays_configuration_message(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Configure a data source before selecting tables.",
        )

    @patch(
        "apps.catalogs.scope_service.CatalogScopeService.discover_available_tables",
        return_value={
            "sales": ["customers", "orders"],
        },
    )
    def test_user_can_save_catalog_scope_selection(
        self,
        discover_available_tables,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        DataSource.objects.create(
            project=project,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
            data={
                "tables": [
                    "sales.customers",
                    "sales.orders",
                ],
            },
        )

        self.assertEqual(response.status_code, 302)

        project.refresh_from_db()

        self.assertEqual(
            project.catalog_scope.selected_tables,
            [
                {"schema": "sales", "table": "customers"},
                {"schema": "sales", "table": "orders"},
            ],
        )

    @patch(
        "apps.catalogs.scope_service.CatalogScopeService.discover_available_tables",
        return_value={
            "sales": ["customers", "orders"],
        },
    )
    def test_user_cannot_save_table_outside_discovered_tables(
        self,
        discover_available_tables,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        DataSource.objects.create(
            project=project,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
            data={
                "tables": [
                    "sales.customers",
                    "secret.admin_users",
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Invalid table selection.",
        )

        self.assertFalse(
            hasattr(project, "catalog_scope"),
        )

    @patch(
        "apps.catalogs.scope_service.CatalogScopeService.discover_available_tables",
        return_value={
            "sales": ["customers", "orders"],
        },
    )
    def test_catalog_scope_marks_saved_tables_as_selected(
        self,
        discover_available_tables,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        DataSource.objects.create(
            project=project,
        )

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {"schema": "sales", "table": "orders"},
            ],
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<input type="checkbox" name="tables" value="sales.orders" checked>',
            html=True,
        )