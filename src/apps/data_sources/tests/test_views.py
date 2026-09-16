from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalogs.exceptions import CatalogNotReadyError
from apps.catalogs.models import CatalogScope
from apps.data_sources.exceptions import DataSourceConnectionError
from apps.data_sources.models import DataSource
from apps.projects.models import Project
from catalog.types import KnowledgeCatalog, RelationshipMetadata, TableMetadata


class DataSourceConfigurationViewTests(TestCase):
    def test_user_cannot_configure_data_source_for_another_users_project(self):
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
                "data-source-configure",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)

    def test_user_can_access_data_source_configuration_for_own_project(self):
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
                "data-source-configure",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create project")
        self.assertContains(response, "Data source")
        self.assertContains(
            response,
            reverse(
                "project-update",
                kwargs={"project_id": project.id},
            ),
        )

    def test_invalid_data_source_form_is_not_persisted(self):
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
                "data-source-configure",
                kwargs={"project_id": project.id},
            ),
            {
                "host": "",
                "port": "5432",
                "database": "analytics",
                "username": "readonly",
                "password": "secret",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(DataSource.objects.filter(project=project).exists())

    @patch(
        "apps.data_sources.views.DataSourceService",
        create=True,
    )
    def test_valid_data_source_form_is_configured_and_tested(
        self,
        data_source_service_class,
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
                "data-source-configure",
                kwargs={"project_id": project.id},
            ),
            {
                "host": "localhost",
                "port": "5432",
                "database": "analytics",
                "username": "readonly",
                "password": "secret",
            },
        )

        self.assertEqual(
            response.url,
            reverse(
                "catalog-scope",
                kwargs={"project_id": project.id},
            ),
        )

        data_source_service_class.return_value.configure_and_test.assert_called_once_with(
            project=project,
            host="localhost",
            port=5432,
            database="analytics",
            username="readonly",
            password="secret",
        )

    @patch(
        "apps.data_sources.views.DataSourceService",
    )
    def test_connection_failure_displays_form_error(
        self,
        data_source_service_class,
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

        data_source_service_class.return_value.configure_and_test.side_effect = (
            DataSourceConnectionError("Unable to connect to the data source.")
        )

        response = self.client.post(
            reverse(
                "data-source-configure",
                kwargs={"project_id": project.id},
            ),
            {
                "host": "localhost",
                "port": "5432",
                "database": "analytics",
                "username": "readonly",
                "password": "wrong-password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Unable to connect to the data source.",
        )
        self.assertFalse(DataSource.objects.filter(project=project).exists())

    def test_existing_data_source_prefills_form_without_password(self):
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
            host="db.example.com",
            port=5433,
            database="analytics",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "data-source-configure",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)

        form = response.context["form"]

        self.assertEqual(form["host"].value(), "db.example.com")
        self.assertEqual(form["port"].value(), 5433)
        self.assertEqual(form["database"].value(), "analytics")
        self.assertEqual(form["username"].value(), "readonly")

        self.assertNotContains(response, "secret-password")

    def test_existing_data_source_requires_password_for_reconfiguration(self):
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
            host="db.example.com",
            port=5432,
            database="analytics",
            username="readonly",
        )
        data_source.set_password("old-secret")
        data_source.save()

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "data-source-configure",
                kwargs={"project_id": project.id},
            ),
            {
                "host": "new-db.example.com",
                "port": "5432",
                "database": "analytics",
                "username": "readonly",
                "password": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

        data_source.refresh_from_db()

        self.assertEqual(data_source.host, "db.example.com")
        self.assertEqual(data_source.get_password(), "old-secret")

    @patch(
        "apps.data_sources.views.DataSourceService",
    )
    def test_existing_data_source_can_be_reconfigured(
        self,
        data_source_service_class,
    ):
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
            host="old-db.example.com",
            port=5432,
            database="old_analytics",
            username="old_user",
        )
        data_source.set_password("old-secret")
        data_source.save()

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "data-source-configure",
                kwargs={"project_id": project.id},
            ),
            {
                "host": "new-db.example.com",
                "port": "5433",
                "database": "new_analytics",
                "username": "new_user",
                "password": "new-secret",
            },
        )

        self.assertEqual(response.status_code, 302)

        data_source_service_class.return_value.configure_and_test.assert_called_once_with(
            project=project,
            host="new-db.example.com",
            port=5433,
            database="new_analytics",
            username="new_user",
            password="new-secret",
        )

    @patch(
        "apps.data_sources.views.DataSourceService",
    )
    def test_failed_reconfiguration_preserves_existing_data_source(
        self,
        data_source_service_class,
    ):
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
            host="old-db.example.com",
            port=5432,
            database="old_analytics",
            username="old_user",
        )
        data_source.set_password("old-secret")
        data_source.save()

        data_source_service_class.return_value.configure_and_test.side_effect = (
            DataSourceConnectionError("Unable to connect to the data source.")
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "data-source-configure",
                kwargs={"project_id": project.id},
            ),
            {
                "host": "new-db.example.com",
                "port": "5433",
                "database": "new_analytics",
                "username": "new_user",
                "password": "new-secret",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Unable to connect to the data source.",
        )

        data_source.refresh_from_db()

        self.assertEqual(data_source.host, "old-db.example.com")
        self.assertEqual(data_source.port, 5432)
        self.assertEqual(data_source.database, "old_analytics")
        self.assertEqual(data_source.username, "old_user")
        self.assertEqual(data_source.get_password(), "old-secret")


class DataOverviewViewTests(TestCase):
    def test_user_can_access_data_overview_for_own_project(self):
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
            host="db.example.com",
            port=5432,
            database="analytics",
            username="readonly",
            connection_status=DataSource.ConnectionStatus.CONNECTED,
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
                "data-overview",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["project"], project)
        self.assertEqual(response.context["data_source"], data_source)
        self.assertEqual(
            response.context["selected_tables_count"],
            2,
        )

    def test_user_cannot_access_data_overview_for_another_users_project(self):
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
        DataSource.objects.create(
            project=project,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "data-overview",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)

    def test_data_overview_returns_404_when_data_source_is_missing(self):
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
                "data-overview",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)

    def test_data_overview_has_zero_selected_tables_when_scope_is_missing(self):
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
                "data-overview",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["selected_tables_count"],
            0,
        )

    def test_data_overview_displays_test_connection_action(self):
        user = get_user_model().objects.create_user(
            username="marine-test-action",
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
                "data-overview",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse(
                "data-test-connection",
                kwargs={"project_id": project.id},
            ),
        )
        self.assertContains(response, "Test connection")

    def test_data_overview_disables_test_connection_for_archived_project(self):
        user = get_user_model().objects.create_user(
            username="marine-archived-overview",
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

        response = self.client.get(
            reverse(
                "data-overview",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test connection")
        self.assertContains(response, "disabled")


class DataSchemaViewTests(TestCase):
    @patch("apps.data_sources.views.CatalogReader")
    def test_user_can_access_schema_for_own_project(
        self,
        catalog_reader_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )
        table = TableMetadata(
            schema="sales",
            name="customers",
            columns=(),
            relationships=(),
        )
        catalog = KnowledgeCatalog(
            tables=(table,),
        )

        catalog_reader_class.return_value.get_current.return_value = catalog

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "data-schema",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["project"], project)
        self.assertEqual(response.context["catalog"], catalog)
        self.assertEqual(response.context["selected_table"], table)

        catalog_reader_class.return_value.get_current.assert_called_once_with(project)

    @patch("apps.data_sources.views.CatalogReader")
    def test_user_cannot_access_schema_for_another_users_project(
        self,
        catalog_reader_class,
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

        response = self.client.get(
            reverse(
                "data-schema",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)
        catalog_reader_class.return_value.get_current.assert_not_called()

    @patch("apps.data_sources.views.CatalogReader")
    def test_schema_is_available_when_catalog_is_not_ready(
        self,
        catalog_reader_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        catalog_reader_class.return_value.get_current.side_effect = (
            CatalogNotReadyError("Project knowledge catalog is not ready.")
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "data-schema",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["catalog"])

    @patch("apps.data_sources.views.CatalogReader")
    def test_schema_selects_first_table_by_default(
        self,
        catalog_reader_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-default",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        customers = TableMetadata(
            schema="sales",
            name="customers",
            columns=(),
            relationships=(),
        )
        orders = TableMetadata(
            schema="sales",
            name="orders",
            columns=(),
            relationships=(),
        )
        catalog = KnowledgeCatalog(
            tables=(customers, orders),
        )

        catalog_reader_class.return_value.get_current.return_value = catalog

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "data-schema",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_table"], customers)

    @patch("apps.data_sources.views.CatalogReader")
    def test_schema_selects_requested_table(
        self,
        catalog_reader_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-selected",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        customers = TableMetadata(
            schema="sales",
            name="customers",
            columns=(),
            relationships=(),
        )
        orders = TableMetadata(
            schema="sales",
            name="orders",
            columns=(),
            relationships=(),
        )
        catalog = KnowledgeCatalog(
            tables=(customers, orders),
        )

        catalog_reader_class.return_value.get_current.return_value = catalog

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "data-schema",
                kwargs={"project_id": project.id},
            ),
            {
                "table": "sales.orders",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_table"], orders)

    @patch("apps.data_sources.views.CatalogReader")
    def test_schema_separates_references_and_referenced_by(
        self,
        catalog_reader_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-relationships",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        relationship = RelationshipMetadata(
            source_schema="sales",
            source_table="orders",
            source_column="customer_id",
            target_schema="sales",
            target_table="customers",
            target_column="id",
        )

        customers = TableMetadata(
            schema="sales",
            name="customers",
            columns=(),
            relationships=(relationship,),
        )
        orders = TableMetadata(
            schema="sales",
            name="orders",
            columns=(),
            relationships=(relationship,),
        )

        catalog = KnowledgeCatalog(
            tables=(customers, orders),
        )

        catalog_reader_class.return_value.get_current.return_value = catalog
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "data-schema",
                kwargs={"project_id": project.id},
            ),
            {"table": "sales.customers"},
        )

        self.assertEqual(response.context["references"], ())
        self.assertEqual(
            response.context["referenced_by"],
            (relationship,),
        )

        response = self.client.get(
            reverse(
                "data-schema",
                kwargs={"project_id": project.id},
            ),
            {"table": "sales.orders"},
        )

        self.assertEqual(
            response.context["references"],
            (relationship,),
        )
        self.assertEqual(response.context["referenced_by"], ())


class DataTestConnectionViewTests(TestCase):
    @patch("apps.data_sources.views.DataSourceService")
    def test_owner_can_test_data_source_connection(
        self,
        data_source_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-test-connection",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )
        data_source = DataSource.objects.create(
            project=project,
        )

        data_source_service_class.return_value.test_connection.return_value = True

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "data-test-connection",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertRedirects(
            response,
            reverse(
                "data-overview",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )
        data_source_service_class.return_value.test_connection.assert_called_once_with(
            data_source
        )

    @patch("apps.data_sources.views.DataSourceService")
    def test_user_cannot_test_another_users_data_source(
        self,
        data_source_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-test-connection",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="other-test-connection",
            password="test-password",
        )
        project = Project.objects.create(
            owner=other_user,
            name="Other project",
        )
        DataSource.objects.create(
            project=project,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "data-test-connection",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)
        data_source_service_class.return_value.test_connection.assert_not_called()

    @patch("apps.data_sources.views.DataSourceService")
    def test_test_connection_returns_404_when_data_source_is_missing(
        self,
        data_source_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-test-connection",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="My project",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "data-test-connection",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)
        data_source_service_class.return_value.test_connection.assert_not_called()

    @patch("apps.data_sources.views.DataSourceService")
    def test_test_connection_rejects_get(
        self,
        data_source_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-test-connection",
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
                "data-test-connection",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)
        data_source_service_class.return_value.test_connection.assert_not_called()

    @patch("apps.data_sources.views.DataSourceService")
    def test_archived_project_cannot_test_data_source_connection(
        self,
        data_source_service_class,
    ):
        user = get_user_model().objects.create_user(
            username="marine-archived-test-connection",
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
                "data-test-connection",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertRedirects(
            response,
            reverse(
                "data-overview",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )

        data_source_service_class.return_value.test_connection.assert_not_called()
