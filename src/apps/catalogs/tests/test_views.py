from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalogs.exceptions import (
    CatalogScopeNotConfiguredError,
    DataSourceNotConfiguredError,
)
from apps.catalogs.models import CatalogScope, KnowledgeCatalog
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

    @patch(
        "apps.catalogs.scope_service.CatalogScopeService.discover_available_tables",
        return_value={
            "sales": ["customers", "orders"],
        },
    )
    def test_catalog_scope_displays_build_catalog_action(
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

        response = self.client.get(
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Build catalog")
        self.assertContains(
            response,
            reverse(
                "catalog-build",
                kwargs={"project_id": project.id},
            ),
        )

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
            CatalogScopeNotConfiguredError(
                "Project has no catalog scope."
            )
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
            DataSourceNotConfiguredError(
                "Project has no data source."
            )
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

    @patch(
        "apps.catalogs.scope_service.CatalogScopeService.discover_available_tables",
        return_value={
            "sales": ["customers", "orders"],
        },
    )
    def test_catalog_scope_displays_ready_catalog_status(
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

        KnowledgeCatalog.objects.create(
            project=project,
            status=KnowledgeCatalog.Status.READY,
            version=2,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Catalog status: Ready")
        self.assertContains(response, "Version: 2")

    @patch(
        "apps.catalogs.scope_service.CatalogScopeService.discover_available_tables",
        return_value={
            "sales": ["customers", "orders"],
        },
    )
    def test_catalog_scope_displays_catalog_status(
        self,
        discover_available_tables,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        self.client.force_login(user)

        cases = [
            (KnowledgeCatalog.Status.PENDING, "Pending"),
            (KnowledgeCatalog.Status.BUILDING, "Building"),
            (KnowledgeCatalog.Status.STALE, "Stale"),
            (KnowledgeCatalog.Status.FAILED, "Failed"),
        ]

        for status, label in cases:
            with self.subTest(status=status):
                project = Project.objects.create(
                    owner=user,
                    name=f"Project {status}",
                )

                DataSource.objects.create(
                    project=project,
                )

                KnowledgeCatalog.objects.create(
                    project=project,
                    status=status,
                )

                response = self.client.get(
                    reverse(
                        "catalog-scope",
                        kwargs={"project_id": project.id},
                    ),
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    f"Catalog status: {label}",
                )

    @patch(
        "apps.catalogs.scope_service.CatalogScopeService.discover_available_tables",
        return_value={
            "sales": ["customers", "orders"],
        },
    )
    def test_catalog_scope_displays_not_built_when_catalog_does_not_exist(
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

        response = self.client.get(
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Catalog status: Not built",
        )

    @patch(
        "apps.catalogs.scope_service.CatalogScopeService.discover_available_tables",
        return_value={
            "sales": ["customers", "orders"],
        },
    )
    def test_catalog_scope_displays_rebuild_action_when_catalog_is_ready(
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

        KnowledgeCatalog.objects.create(
            project=project,
            status=KnowledgeCatalog.Status.READY,
            version=1,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rebuild catalog")
        self.assertNotContains(response, ">Build catalog<")

    @patch(
        "apps.catalogs.scope_service.CatalogScopeService.discover_available_tables",
        return_value={
            "sales": ["customers", "orders"],
        },
    )
    def test_catalog_scope_disables_build_action_when_catalog_is_building(
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

        KnowledgeCatalog.objects.create(
            project=project,
            status=KnowledgeCatalog.Status.BUILDING,
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
            "Catalog build in progress.",
        )
        self.assertNotContains(response, ">Build catalog<")
        self.assertNotContains(response, ">Rebuild catalog<")

    @patch(
        "apps.catalogs.scope_service.CatalogScopeService.discover_available_tables",
        return_value={
            "sales": ["customers", "orders"],
        },
    )
    def test_catalog_scope_displays_build_action_when_catalog_is_pending(
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

        KnowledgeCatalog.objects.create(
            project=project,
            status=KnowledgeCatalog.Status.PENDING,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ">Build catalog<")
        self.assertNotContains(response, ">Rebuild catalog<")

    @patch(
        "apps.catalogs.scope_service.CatalogScopeService.discover_available_tables",
        return_value={
            "sales": ["customers", "orders"],
        },
    )
    def test_catalog_scope_displays_expected_action_for_failed_and_stale_catalog(
        self,
        discover_available_tables,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        self.client.force_login(user)

        cases = [
            (
                KnowledgeCatalog.Status.FAILED,
                "Build catalog",
                "Rebuild catalog",
            ),
            (
                KnowledgeCatalog.Status.STALE,
                "Rebuild catalog",
                ">Build catalog<",
            ),
        ]

        for status, expected, unexpected in cases:
            with self.subTest(status=status):
                project = Project.objects.create(
                    owner=user,
                    name=f"Project {status}",
                )

                DataSource.objects.create(
                    project=project,
                )

                KnowledgeCatalog.objects.create(
                    project=project,
                    status=status,
                )

                response = self.client.get(
                    reverse(
                        "catalog-scope",
                        kwargs={"project_id": project.id},
                    ),
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected)
                self.assertNotContains(response, unexpected)



