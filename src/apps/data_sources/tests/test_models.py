from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase, override_settings

from apps.data_sources.exceptions import DataSourceConfigurationError
from apps.data_sources.models import DataSource
from apps.projects.tests.factories import create_test_project


@override_settings(PUBLIC_DEMO_MODE=False)
class DataSourceModelTests(TestCase):
    def test_data_source_has_not_tested_status_by_default(self):
        project = create_test_project(
            name="Test project",
        )

        data_source = DataSource.objects.create(
            project=project,
        )

        self.assertEqual(
            data_source.connection_status,
            DataSource.ConnectionStatus.NOT_TESTED,
        )

    def test_project_can_have_only_one_data_source(self):
        project = create_test_project(
            name="Test project",
        )

        DataSource.objects.create(
            project=project,
        )

        with self.assertRaises(IntegrityError):
            DataSource.objects.create(
                project=project,
            )

    def test_data_source_encrypts_password(self):
        project = create_test_project(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            database="example",
            username="readonly",
        )

        data_source.set_password("secret-password")

        self.assertNotEqual(
            data_source.encrypted_password,
            "secret-password",
        )

    def test_data_source_can_decrypt_password(self):
        project = create_test_project(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            database="example",
            username="readonly",
        )

        data_source.set_password("secret-password")

        self.assertEqual(
            data_source.get_password(),
            "secret-password",
        )

    def test_data_source_is_not_configured_when_connection_fields_are_missing(self):
        project = create_test_project(
            name="Test project",
        )

        data_source = DataSource.objects.create(
            project=project,
        )

        self.assertFalse(data_source.is_configured())

    def test_data_source_is_configured_when_connection_fields_are_complete(self):
        project = create_test_project(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        data_source.set_password("secret-password")

        self.assertTrue(data_source.is_configured())

    def test_data_source_builds_postgresql_connection_config(self):
        project = create_test_project(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        data_source.set_password("secret-password")

        config = data_source.to_connection_config()

        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 5432)
        self.assertEqual(config.database, "example")
        self.assertEqual(config.user, "readonly")
        self.assertEqual(config.password, "secret-password")

    def test_data_source_cannot_build_config_when_not_configured(self):
        project = create_test_project(
            name="Test project",
        )

        data_source = DataSource.objects.create(
            project=project,
        )

        with self.assertRaises(DataSourceConfigurationError):
            data_source.to_connection_config()

    @override_settings(PUBLIC_DEMO_MODE=True)
    @patch("apps.data_sources.models.get_demo_dataset_connection")
    def test_demo_connection_uses_server_configuration(self, resolver):
        resolver.return_value = {
            "host": "trusted-demo-host",
            "port": 5432,
            "database": "trusted-demo-db",
            "username": "trusted-readonly",
            "password": "server-secret",
        }

        project = create_test_project(name="Demo project")

        data_source = DataSource(
            project=project,
            demo_dataset_key="eeg",
            host="untrusted-host",
            port=9999,
            database="untrusted-db",
            username="untrusted-user",
        )
        data_source.set_password("untrusted-password")

        config = data_source.to_connection_config()

        resolver.assert_called_once_with("eeg")
        self.assertEqual(config.host, "trusted-demo-host")
        self.assertEqual(config.port, 5432)
        self.assertEqual(config.database, "trusted-demo-db")
        self.assertEqual(config.user, "trusted-readonly")
        self.assertEqual(config.password, "server-secret")

    @override_settings(PUBLIC_DEMO_MODE=True)
    def test_demo_connection_rejects_missing_dataset(self):
        project = create_test_project(name="Demo project")

        data_source = DataSource(
            project=project,
            host="localhost",
            database="arbitrary-db",
            username="readonly",
        )
        data_source.set_password("secret")

        with self.assertRaises(DataSourceConfigurationError):
            data_source.to_connection_config()

    @override_settings(PUBLIC_DEMO_MODE=True)
    def test_demo_connection_rejects_unknown_dataset(self):
        project = create_test_project(name="Demo project")

        data_source = DataSource(
            project=project,
            demo_dataset_key="unknown",
        )

        with self.assertRaises(DataSourceConfigurationError):
            data_source.to_connection_config()
