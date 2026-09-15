from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalogs.exceptions import (
    CatalogScopeNotConfiguredError,
    DataSourceNotConfiguredError,
)
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
        self.assertContains(response, "Create project")
        self.assertContains(response, "Data selection")

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
        self.assertEqual(
            response.url,
            reverse(
                "catalog-confirmation",
                kwargs={"project_id": project.id},
            ),
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
            'value="sales.orders"',
        )
        self.assertContains(
            response,
            "checked",
        )

    @patch("apps.catalogs.views.CatalogService")
    def test_user_can_build_catalog_for_own_project(
        self,
        catalog_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "catalog-build",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "conversation-list",
                kwargs={"project_id": project.id},
            ),
        )

        catalog_service_class.return_value.build_for_project.assert_called_once_with(
            project
        )

    @patch("apps.catalogs.views.CatalogService")
    def test_user_cannot_build_catalog_for_another_users_project(
        self,
        catalog_service_class,
    ):
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

        response = self.client.post(
            reverse(
                "catalog-build",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)
        catalog_service_class.return_value.build_for_project.assert_not_called()

    @patch("apps.catalogs.views.CatalogService")
    def test_catalog_build_rejects_get(
        self,
        catalog_service_class,
    ):
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
                "catalog-build",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)
        catalog_service_class.return_value.build_for_project.assert_not_called()

    @patch("apps.catalogs.views.CatalogService")
    def test_catalog_build_displays_error_when_scope_is_not_configured(
        self,
        catalog_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        catalog_service_class.return_value.build_for_project.side_effect = (
            CatalogScopeNotConfiguredError("Project has no catalog scope.")
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "catalog-build",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 302)

        response = self.client.get(response["Location"])

        self.assertContains(
            response,
            "Project has no catalog scope.",
        )

    @patch("apps.catalogs.views.CatalogService")
    def test_catalog_build_displays_error_when_data_source_is_not_configured(
        self,
        catalog_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        catalog_service_class.return_value.build_for_project.side_effect = (
            DataSourceNotConfiguredError("Project has no data source.")
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "catalog-build",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 302)

        response = self.client.get(response["Location"])

        self.assertContains(
            response,
            "Project has no data source.",
        )

    @patch("apps.catalogs.views.CatalogService")
    def test_catalog_build_displays_generic_error_on_unexpected_failure(
        self,
        catalog_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        catalog_service_class.return_value.build_for_project.side_effect = RuntimeError(
            "database connection details"
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "catalog-build",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 302)

        response = self.client.get(response["Location"])

        self.assertContains(
            response,
            "Unable to build the catalog.",
        )
        self.assertNotContains(
            response,
            "database connection details",
        )


class CatalogConfirmationViewTests(TestCase):
    def test_user_can_access_catalog_confirmation_for_own_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        data_source = DataSource.objects.create(
            project=project,
        )

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {"schema": "sales", "table": "customers"},
                {"schema": "sales", "table": "orders"},
            ],
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-confirmation",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["project"], project)
        self.assertEqual(response.context["data_source"], data_source)
        self.assertEqual(
            response.context["selected_tables"],
            [
                {"schema": "sales", "table": "customers"},
                {"schema": "sales", "table": "orders"},
            ],
        )

    def test_catalog_confirmation_redirects_when_data_source_is_missing(self):
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
                "catalog-confirmation",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertRedirects(
            response,
            reverse(
                "data-source-configure",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )

    def test_catalog_confirmation_redirects_when_scope_is_missing(self):
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

        response = self.client.get(
            reverse(
                "catalog-confirmation",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertRedirects(
            response,
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )

    def test_user_cannot_access_catalog_confirmation_for_another_users_project(self):
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
                "catalog-confirmation",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)
