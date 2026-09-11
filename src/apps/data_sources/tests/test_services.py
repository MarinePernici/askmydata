from django.test import TestCase

from apps.data_sources.models import DataSource
from apps.data_sources.services import DataSourceService
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

