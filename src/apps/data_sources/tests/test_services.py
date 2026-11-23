from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from apps.catalogs.models import KnowledgeCatalog, SchemaSnapshot
from apps.data_sources.exceptions import DataSourceConnectionError
from apps.data_sources.models import DataSource
from apps.data_sources.services import DataSourceService
from apps.projects.models import Project
from apps.projects.tests.factories import create_test_project


class SuccessfulConnector:
    def __init__(self, config):
        self.config = config

    def test_connection(self):
        return True

    def has_read_only_permissions(self):
        return True


class WritableConnector:
    def __init__(self, config):
        self.config = config

    def test_connection(self):
        return True

    def has_read_only_permissions(self):
        return False


class FailingConnector:
    def __init__(self, config):
        self.config = config

    def test_connection(self):
        return False


@override_settings(PUBLIC_DEMO_MODE=False)
class DataSourceServiceTests(TestCase):
    def setUp(self):
        self.project = create_test_project(
            name="Test project",
        )

        self.data_source = DataSource(
            project=self.project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        self.data_source.set_password("secret-password")
        self.data_source.save()

    @patch("apps.data_sources.services.logger")
    def test_successful_connection_updates_status_to_connected(self, logger):
        service = DataSourceService(
            connector_class=SuccessfulConnector,
        )

        result = service.test_connection(
            self.data_source,
        )

        self.data_source.refresh_from_db()

        self.assertTrue(result)
        self.assertEqual(
            self.data_source.connection_status,
            DataSource.ConnectionStatus.CONNECTED,
        )
        self.assertIsNotNone(
            self.data_source.last_connection_at,
        )

        logger.info.assert_called_once_with(
            "Data source connection tested.",
            extra={
                "event": "data_source.connection_tested",
                "project_id": self.project.id,
                "connection_status": DataSource.ConnectionStatus.CONNECTED,
            },
        )

    @patch("apps.data_sources.services.logger")
    def test_failed_connection_updates_status_to_failed(self, logger):
        service = DataSourceService(
            connector_class=FailingConnector,
        )

        result = service.test_connection(
            self.data_source,
        )

        self.data_source.refresh_from_db()

        self.assertFalse(result)
        self.assertEqual(
            self.data_source.connection_status,
            DataSource.ConnectionStatus.FAILED,
        )
        self.assertIsNotNone(
            self.data_source.last_connection_at,
        )

        logger.info.assert_called_once_with(
            "Data source connection tested.",
            extra={
                "event": "data_source.connection_tested",
                "project_id": self.project.id,
                "connection_status": DataSource.ConnectionStatus.FAILED,
            },
        )

    def test_configure_data_source_marks_project_as_configuring(self):
        project = create_test_project(
            name="Test project",
        )

        service = DataSourceService()

        data_source = service.configure(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
            password="secret-password",
        )

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.CONFIGURING,
        )
        self.assertEqual(
            data_source.project,
            project,
        )

    def test_configure_updates_existing_data_source(self):
        service = DataSourceService()

        data_source_id = self.data_source.id

        updated_data_source = service.configure(
            project=self.project,
            host="new-host",
            port=5433,
            database="new_database",
            username="new_user",
            password="new-password",
        )

        self.assertEqual(
            updated_data_source.id,
            data_source_id,
        )
        self.assertEqual(
            updated_data_source.host,
            "new-host",
        )
        self.assertEqual(
            updated_data_source.port,
            5433,
        )
        self.assertEqual(
            updated_data_source.database,
            "new_database",
        )
        self.assertEqual(
            updated_data_source.username,
            "new_user",
        )
        self.assertEqual(
            updated_data_source.get_password(),
            "new-password",
        )

    def test_configure_resets_connection_status_to_not_tested(self):
        self.data_source.connection_status = DataSource.ConnectionStatus.CONNECTED
        self.data_source.save(update_fields=["connection_status"])

        service = DataSourceService()

        updated_data_source = service.configure(
            project=self.project,
            host="new-host",
            port=5432,
            database="new_database",
            username="new_user",
            password="new-password",
        )

        self.assertEqual(
            updated_data_source.connection_status,
            DataSource.ConnectionStatus.NOT_TESTED,
        )

    def test_configure_does_not_set_last_connection_at(self):
        service = DataSourceService()

        data_source = service.configure(
            project=self.project,
            host="new-host",
            port=5432,
            database="new_database",
            username="new_user",
            password="new-password",
        )

        self.assertIsNone(
            data_source.last_connection_at,
        )

    def test_configure_marks_existing_catalog_as_stale(self):
        self.project.status = Project.Status.READY
        self.project.save(update_fields=["status"])

        knowledge_catalog = KnowledgeCatalog.objects.create(
            project=self.project,
            status=KnowledgeCatalog.Status.READY,
            version=1,
        )

        SchemaSnapshot.objects.create(
            catalog=knowledge_catalog,
            version=1,
            schema_data={"tables": []},
        )

        service = DataSourceService()

        service.configure(
            project=self.project,
            host="new-host",
            port=5432,
            database="new_database",
            username="new_user",
            password="new-password",
        )

        knowledge_catalog.refresh_from_db()

        self.assertEqual(
            knowledge_catalog.status,
            KnowledgeCatalog.Status.STALE,
        )
        self.assertEqual(
            knowledge_catalog.version,
            1,
        )
        self.assertEqual(
            knowledge_catalog.snapshots.count(),
            1,
        )

    @patch("apps.data_sources.services.logger")
    def test_configure_and_test_saves_valid_configuration(self, logger):
        project = create_test_project(name="Test project")
        service = DataSourceService(
            connector_class=SuccessfulConnector,
        )

        data_source = service.configure_and_test(
            project=project,
            host="localhost",
            port=5432,
            database="sales",
            username="readonly",
            password="secret",
        )

        self.assertEqual(
            data_source.connection_status,
            DataSource.ConnectionStatus.CONNECTED,
        )
        self.assertIsNotNone(
            data_source.last_connection_at,
        )

        logger.info.assert_called_once_with(
            "Data source connection tested.",
            extra={
                "event": "data_source.connection_tested",
                "project_id": project.id,
                "connection_status": DataSource.ConnectionStatus.CONNECTED,
            },
        )

    def test_configure_and_test_does_not_replace_existing_configuration_on_failure(
        self,
    ):
        project = create_test_project(name="Test project")

        existing = DataSource(
            project=project,
            host="old-host",
            port=5432,
            database="old-db",
            username="old-user",
            connection_status=DataSource.ConnectionStatus.CONNECTED,
        )
        existing.set_password("old-password")
        existing.save()

        service = DataSourceService(
            connector_class=FailingConnector,
        )

        with self.assertRaises(DataSourceConnectionError):
            service.configure_and_test(
                project=project,
                host="new-host",
                port=5432,
                database="new-db",
                username="new-user",
                password="new-password",
            )

        existing.refresh_from_db()

        self.assertEqual(existing.host, "old-host")
        self.assertEqual(existing.database, "old-db")
        self.assertEqual(existing.username, "old-user")
        self.assertEqual(
            existing.connection_status,
            DataSource.ConnectionStatus.CONNECTED,
        )
        self.assertEqual(existing.get_password(), "old-password")

    def test_configure_and_test_does_not_create_data_source_on_failure(self):
        project = create_test_project(name="Test project")

        service = DataSourceService(
            connector_class=FailingConnector,
        )

        with self.assertRaises(DataSourceConnectionError):
            service.configure_and_test(
                project=project,
                host="localhost",
                port=5432,
                database="sales",
                username="readonly",
                password="wrong-password",
            )

        self.assertFalse(DataSource.objects.filter(project=project).exists())

    def test_configure_and_test_failure_does_not_change_project_status(self):
        project = create_test_project(
            name="Test project",
            status=Project.Status.READY,
        )

        service = DataSourceService(
            connector_class=FailingConnector,
        )

        with self.assertRaises(DataSourceConnectionError):
            service.configure_and_test(
                project=project,
                host="localhost",
                port=5432,
                database="sales",
                username="readonly",
                password="wrong-password",
            )

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.READY,
        )

    def test_configure_and_test_rejects_writable_database_user(self):
        project = create_test_project(name="Test project")

        service = DataSourceService(
            connector_class=WritableConnector,
        )

        with self.assertRaises(DataSourceConnectionError):
            service.configure_and_test(
                project=project,
                host="localhost",
                port=5432,
                database="sales",
                username="writable",
                password="secret",
            )

        self.assertFalse(DataSource.objects.filter(project=project).exists())

    @override_settings(PUBLIC_DEMO_MODE=True)
    @patch("apps.data_sources.services.get_demo_dataset_connection")
    def test_demo_configuration_rejects_missing_server_password(self, resolver):
        resolver.side_effect = ImproperlyConfigured(
            "Missing password configuration for demo dataset: pagila"
        )

        service = DataSourceService(
            connector_class=SuccessfulConnector,
        )

        original_host = self.data_source.host
        original_database = self.data_source.database
        original_password = self.data_source.encrypted_password

        with self.assertRaises(ImproperlyConfigured):
            service.configure_and_test(
                project=self.project,
                host="attacker.example.com",
                port=9999,
                database="attacker_db",
                username="attacker",
                password="attacker-secret",
                demo_dataset_key="pagila",
            )

        resolver.assert_called_once_with("pagila")

        self.data_source.refresh_from_db()

        self.assertEqual(self.data_source.host, original_host)
        self.assertEqual(self.data_source.database, original_database)
        self.assertEqual(self.data_source.encrypted_password, original_password)
        self.assertIsNone(self.data_source.demo_dataset_key)


@override_settings(PUBLIC_DEMO_MODE=True)
class DemoDataSourceServiceTests(TestCase):
    @patch("apps.data_sources.services.get_demo_dataset_connection")
    def test_demo_configuration_ignores_arbitrary_connection_parameters(
        self,
        resolver,
    ):
        resolver.return_value = {
            "host": "trusted-demo-host",
            "port": 5432,
            "database": "pagila",
            "username": "pagila_readonly",
            "password": "server-secret",
        }

        project = create_test_project(name="Demo project")
        service = DataSourceService(connector_class=SuccessfulConnector)

        data_source = service.configure_and_test(
            project=project,
            host="attacker-host",
            port=9999,
            database="attacker-db",
            username="attacker",
            password="attacker-password",
            demo_dataset_key="pagila",
        )

        data_source.refresh_from_db()

        self.assertEqual(data_source.demo_dataset_key, "pagila")
        self.assertEqual(data_source.host, "trusted-demo-host")
        self.assertEqual(data_source.port, 5432)
        self.assertEqual(data_source.database, "pagila")
        self.assertEqual(data_source.username, "pagila_readonly")
        self.assertEqual(data_source.get_password(), "server-secret")
        self.assertEqual(
            data_source.connection_status, DataSource.ConnectionStatus.CONNECTED
        )

    @patch("apps.data_sources.services.get_demo_dataset_connection")
    def test_demo_configuration_rejects_missing_dataset(self, resolver):
        project = create_test_project(name="Demo project")
        service = DataSourceService(connector_class=SuccessfulConnector)

        with self.assertRaises(DataSourceConnectionError):
            service.configure_and_test(
                project=project,
                host="attacker-host",
                port=5432,
                database="attacker-db",
                username="attacker",
                password="attacker-password",
            )

        resolver.assert_not_called()
        self.assertFalse(DataSource.objects.filter(project=project).exists())

    @patch("apps.data_sources.services.get_demo_dataset_connection")
    def test_demo_configuration_rejects_unknown_dataset(self, resolver):
        resolver.side_effect = ValueError("Unknown demo dataset.")
        project = create_test_project(name="Demo project")
        service = DataSourceService(connector_class=SuccessfulConnector)

        with self.assertRaises(DataSourceConnectionError):
            service.configure_and_test(
                project=project,
                host="attacker-host",
                port=5432,
                database="attacker-db",
                username="attacker",
                password="attacker-password",
                demo_dataset_key="unknown",
            )

        self.assertFalse(DataSource.objects.filter(project=project).exists())
