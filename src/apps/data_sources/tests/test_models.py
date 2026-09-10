from django.db import IntegrityError
from django.test import TestCase

from apps.data_sources.models import DataSource
from apps.projects.models import Project


class DataSourceModelTests(TestCase):
    def test_data_source_has_not_tested_status_by_default(self):
        project = Project.objects.create(
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
        project = Project.objects.create(
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
        project = Project.objects.create(
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
        project = Project.objects.create(
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
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource.objects.create(
            project=project,
        )

        self.assertFalse(data_source.is_configured())

    def test_data_source_is_configured_when_connection_fields_are_complete(self):
        project = Project.objects.create(
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
        project = Project.objects.create(
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
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource.objects.create(
            project=project,
        )

        with self.assertRaises(ValueError):
            data_source.to_connection_config()
