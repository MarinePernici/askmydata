from django.test import TestCase

from apps.data_sources.models import DataSource
from apps.data_sources.services import DataSourceService
from apps.catalogs.models import KnowledgeCatalog, SchemaSnapshot
from apps.projects.models import Project


class SuccessfulConnector:
    def __init__(self, config):
        self.config = config

    def test_connection(self):
        return True


class FailingConnector:
    def __init__(self, config):
        self.config = config

    def test_connection(self):
        return False


class DataSourceServiceTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
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

    def test_successful_connection_updates_status_to_connected(self):
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

    def test_failed_connection_updates_status_to_failed(self):
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

    def test_configure_data_source_marks_project_as_configuring(self):
        project = Project.objects.create(
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
        self.data_source.connection_status = (
            DataSource.ConnectionStatus.CONNECTED
        )
        self.data_source.save(
            update_fields=["connection_status"]
        )

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