from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalogs.exceptions import (
    CatalogNotReadyError,
    CatalogScopeNotConfiguredError,
    DataSourceNotConfiguredError,
)
from apps.catalogs.models import CatalogScope, KnowledgeCatalog
from apps.data_sources.models import DataSource
from apps.projects.models import Project
from catalog.types import (
    KnowledgeCatalog as DomainKnowledgeCatalog,
    SemanticMetadata,
    TableMetadata,
)
from connectors.types import ColumnMetadata


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

    @patch("apps.catalogs.views.CatalogScopeService")
    def test_archived_project_cannot_access_catalog_scope_post(
        self,
        catalog_scope_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-archived-catalog-scope",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Archived project",
            status=Project.Status.ARCHIVED,
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

        self.assertRedirects(
            response,
            reverse(
                "project-detail",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )

        catalog_scope_service_class.return_value.discover_available_tables.assert_not_called()
        catalog_scope_service_class.return_value.save_selection.assert_not_called()

    @patch("apps.catalogs.views.CatalogScopeService")
    def test_ready_project_cannot_access_catalog_scope(
        self,
        catalog_scope_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-ready-catalog-scope",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Ready project",
            status=Project.Status.READY,
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

        self.assertRedirects(
            response,
            reverse(
                "project-detail",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )

        catalog_scope_service_class.return_value.discover_available_tables.assert_not_called()
        catalog_scope_service_class.return_value.save_selection.assert_not_called()

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
    def test_archived_project_cannot_build_catalog(
        self,
        catalog_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-archived-catalog-build",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Archived project",
            status=Project.Status.ARCHIVED,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "catalog-build",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertRedirects(
            response,
            reverse(
                "project-detail",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )

        catalog_service_class.return_value.build_for_project.assert_not_called()

    @patch("apps.catalogs.views.CatalogService")
    def test_ready_project_cannot_build_catalog(
        self,
        catalog_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-ready-catalog-build",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Ready project",
            status=Project.Status.READY,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "catalog-build",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertRedirects(
            response,
            reverse(
                "project-detail",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )

        catalog_service_class.return_value.build_for_project.assert_not_called()

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

    def test_ready_project_cannot_access_catalog_confirmation(self):
        user = get_user_model().objects.create_user(
            username="marine-ready-catalog-confirmation",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Ready project",
            status=Project.Status.READY,
        )

        DataSource.objects.create(
            project=project,
        )

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {"schema": "sales", "table": "customers"},
            ],
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
                "project-detail",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
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


class CatalogDetailViewTests(TestCase):
    @patch("apps.catalogs.views.CatalogReader")
    def test_user_can_access_ready_catalog_for_own_project(
        self,
        catalog_reader_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-catalog-detail",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )
        catalog_model = KnowledgeCatalog.objects.create(
            project=project,
            status=KnowledgeCatalog.Status.READY,
            version=1,
        )
        catalog = DomainKnowledgeCatalog(
            tables=(),
        )

        catalog_reader_class.return_value.get_current.return_value = catalog

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-detail",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["project"], project)
        self.assertEqual(response.context["catalog_model"], catalog_model)
        self.assertEqual(response.context["catalog"], catalog)

        catalog_reader_class.return_value.get_current.assert_called_once_with(project)

    @patch("apps.catalogs.views.CatalogReader")
    def test_catalog_detail_is_available_when_catalog_is_not_ready(
        self,
        catalog_reader_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-catalog-not-ready",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )
        catalog_model = KnowledgeCatalog.objects.create(
            project=project,
            status=KnowledgeCatalog.Status.BUILDING,
        )

        catalog_reader_class.return_value.get_current.side_effect = (
            CatalogNotReadyError("Project knowledge catalog is not ready.")
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-detail",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["catalog_model"], catalog_model)
        self.assertIsNone(response.context["catalog"])

    @patch("apps.catalogs.views.CatalogReader")
    def test_catalog_detail_is_available_when_catalog_does_not_exist(
        self,
        catalog_reader_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-catalog-missing",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-detail",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["catalog_model"])
        self.assertIsNone(response.context["catalog"])

        catalog_reader_class.return_value.get_current.assert_not_called()

    @patch("apps.catalogs.views.CatalogReader")
    def test_user_cannot_access_catalog_for_another_users_project(
        self,
        catalog_reader_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-catalog-detail",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="other-catalog-user",
            password="test-password",
        )
        project = Project.objects.create(
            owner=other_user,
            name="Other project",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-detail",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)
        catalog_reader_class.return_value.get_current.assert_not_called()

    @patch("apps.catalogs.views.CatalogReader")
    def test_catalog_detail_displays_catalog_metrics(
        self,
        catalog_reader_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-catalog-metrics",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )
        KnowledgeCatalog.objects.create(
            project=project,
            status=KnowledgeCatalog.Status.READY,
            version=1,
        )

        catalog = DomainKnowledgeCatalog(
            tables=(
                TableMetadata(
                    schema="sales",
                    name="customers",
                    columns=(
                        ColumnMetadata(
                            name="id",
                            data_type="integer",
                            nullable=False,
                            default=None,
                        ),
                        ColumnMetadata(
                            name="email",
                            data_type="text",
                            nullable=False,
                            default=None,
                        ),
                    ),
                    relationships=(),
                    semantic_metadata=SemanticMetadata(
                        description="Customer accounts.",
                        business_synonyms=("customer", "client"),
                    ),
                ),
                TableMetadata(
                    schema="sales",
                    name="orders",
                    columns=(
                        ColumnMetadata(
                            name="id",
                            data_type="integer",
                            nullable=False,
                            default=None,
                        ),
                    ),
                    relationships=(),
                    semantic_metadata=SemanticMetadata(
                        description="Customer orders.",
                        business_synonyms=("order",),
                    ),
                ),
            ),
        )

        catalog_reader_class.return_value.get_current.return_value = catalog

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-detail",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.context["tables_count"], 2)
        self.assertEqual(response.context["columns_count"], 3)
        self.assertEqual(response.context["business_synonyms_count"], 3)
        self.assertEqual(
            response.context["selected_table"],
            catalog.tables[0],
        )

    @patch("apps.catalogs.views.CatalogReader")
    def test_catalog_detail_selects_requested_table(
        self,
        catalog_reader_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-catalog-selection",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )
        KnowledgeCatalog.objects.create(
            project=project,
            status=KnowledgeCatalog.Status.READY,
            version=1,
        )

        customers = TableMetadata(
            schema="sales",
            name="customers",
            columns=(),
            relationships=(),
            semantic_metadata=None,
        )
        orders = TableMetadata(
            schema="sales",
            name="orders",
            columns=(),
            relationships=(),
            semantic_metadata=None,
        )

        catalog = DomainKnowledgeCatalog(
            tables=(customers, orders),
        )

        catalog_reader_class.return_value.get_current.return_value = catalog

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-detail",
                kwargs={"project_id": project.id},
            ),
            {"table": "sales.orders"},
        )

        self.assertEqual(
            response.context["selected_table"],
            orders,
        )

    @patch("apps.catalogs.views.CatalogReader")
    def test_archived_project_disables_regenerate_catalog(
        self,
        catalog_reader_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-archived-catalog",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Archived project",
            status=Project.Status.ARCHIVED,
        )
        KnowledgeCatalog.objects.create(
            project=project,
            status=KnowledgeCatalog.Status.READY,
            version=1,
        )

        catalog_reader_class.return_value.get_current.return_value = (
            DomainKnowledgeCatalog(tables=())
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "catalog-detail",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Regenerate catalog")
        self.assertContains(response, "disabled")


@patch("apps.catalogs.views.CatalogService")
class CatalogRegenerateViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="catalog-regenerate-user",
            password="password",
        )
        self.client.force_login(self.user)

        self.project = Project.objects.create(
            owner=self.user,
            name="Catalog regenerate project",
        )

    def test_regenerate_catalog_calls_service_and_redirects_to_catalog(
        self,
        catalog_service_class,
    ):
        response = self.client.post(
            reverse(
                "catalog-regenerate",
                kwargs={"project_id": self.project.id},
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "catalog-detail",
                kwargs={"project_id": self.project.id},
            ),
        )

        catalog_service_class.return_value.build_for_project.assert_called_once_with(
            self.project
        )

    def test_regenerate_catalog_rejects_get(
        self,
        catalog_service_class,
    ):
        response = self.client.get(
            reverse(
                "catalog-regenerate",
                kwargs={"project_id": self.project.id},
            )
        )

        self.assertEqual(response.status_code, 404)
        catalog_service_class.return_value.build_for_project.assert_not_called()

    def test_regenerate_catalog_returns_404_for_another_users_project(
        self,
        catalog_service_class,
    ):
        other_user = get_user_model().objects.create_user(
            username="other-catalog-user",
            password="password",
        )
        other_project = Project.objects.create(
            owner=other_user,
            name="Other project",
        )

        response = self.client.post(
            reverse(
                "catalog-regenerate",
                kwargs={"project_id": other_project.id},
            )
        )

        self.assertEqual(response.status_code, 404)
        catalog_service_class.return_value.build_for_project.assert_not_called()

    def test_regenerate_catalog_redirects_to_catalog_when_configuration_is_missing(
        self,
        catalog_service_class,
    ):
        catalog_service_class.return_value.build_for_project.side_effect = (
            DataSourceNotConfiguredError("Data source is not configured.")
        )

        response = self.client.post(
            reverse(
                "catalog-regenerate",
                kwargs={"project_id": self.project.id},
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "catalog-detail",
                kwargs={"project_id": self.project.id},
            ),
        )

    def test_archived_project_cannot_regenerate_catalog(
        self,
        catalog_service_class,
    ):
        self.project.status = Project.Status.ARCHIVED
        self.project.save(update_fields=["status"])

        response = self.client.post(
            reverse(
                "catalog-regenerate",
                kwargs={"project_id": self.project.id},
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "catalog-detail",
                kwargs={"project_id": self.project.id},
            ),
        )

        catalog_service_class.return_value.build_for_project.assert_not_called()
