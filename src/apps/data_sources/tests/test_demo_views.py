from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.projects.models import Project


@override_settings(PUBLIC_DEMO_MODE=True)
class DemoDataSourceConfigurationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="demo-test-user",
            password="test-password",
        )
        self.project = Project.objects.create(
            owner=self.user,
            name="Demo project",
        )
        self.client.force_login(self.user)

        self.url = reverse(
            "data-source-configure",
            kwargs={"project_id": self.project.id},
        )

    def test_demo_form_displays_dataset_selection(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["demo_mode"])

        for dataset in ("eeg", "pagila", "olist", "badminton"):
            self.assertContains(response, f'value="{dataset}"')

        self.assertContains(response, 'id="demo-host"')
        self.assertContains(response, 'id="demo-password"')
        self.assertContains(response, "disabled")

    @patch("apps.data_sources.views.DataSourceService")
    @patch("apps.data_sources.views.get_demo_dataset_connection")
    def test_valid_dataset_uses_server_configuration(
        self,
        connection_resolver,
        data_source_service_class,
    ):
        connection_resolver.return_value = {
            "host": "internal-demo-db",
            "port": 5432,
            "database": "pagila",
            "username": "pagila_readonly",
            "password": "server-secret",
        }

        response = self.client.post(
            self.url,
            {
                "dataset": "pagila",
                "host": "attacker.example.com",
                "port": "9999",
                "database": "attacker_db",
                "username": "attacker",
                "password": "attacker-secret",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "catalog-scope",
                kwargs={"project_id": self.project.id},
            ),
            fetch_redirect_response=False,
        )

        connection_resolver.assert_called_once_with("pagila")

        data_source_service_class.return_value.configure_and_test.assert_called_once_with(
            project=self.project,
            host="internal-demo-db",
            port=5432,
            database="pagila",
            username="pagila_readonly",
            password="server-secret",
            demo_dataset_key="pagila",
        )

    @patch("apps.data_sources.views.DataSourceService")
    @patch("apps.data_sources.views.get_demo_dataset_connection")
    def test_unknown_dataset_is_rejected(
        self,
        connection_resolver,
        data_source_service_class,
    ):
        response = self.client.post(
            self.url,
            {"dataset": "unknown"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a valid choice.")

        connection_resolver.assert_not_called()
        data_source_service_class.return_value.configure_and_test.assert_not_called()

    @patch("apps.data_sources.views.DataSourceService")
    def test_demo_mode_blocks_connection_retest(
        self,
        data_source_service_class,
    ):
        response = self.client.post(
            reverse(
                "data-test-connection",
                kwargs={"project_id": self.project.id},
            )
        )

        self.assertEqual(response.status_code, 404)
        data_source_service_class.return_value.test_connection.assert_not_called()

    def test_demo_overview_hides_connection_details(self):
        from apps.data_sources.models import DataSource

        DataSource.objects.create(
            project=self.project,
            host="internal-secret-host",
            port=5432,
            database="internal-secret-database",
            username="readonly",
        )

        response = self.client.get(
            reverse(
                "data-overview",
                kwargs={"project_id": self.project.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "demo-postgresql")
        self.assertNotContains(response, "internal-secret-host")
        self.assertNotContains(response, "internal-secret-database")
        self.assertNotContains(response, "Test connection")

    @patch("apps.data_sources.views.logger")
    @patch("apps.data_sources.views.DataSourceService")
    @patch("apps.data_sources.views.get_demo_dataset_connection")
    def test_missing_dataset_password_is_handled_safely(
        self,
        connection_resolver,
        data_source_service_class,
        logger_mock,
    ):
        connection_resolver.side_effect = ImproperlyConfigured(
            "Missing password configuration for demo dataset: pagila"
        )

        response = self.client.post(
            self.url,
            {"dataset": "pagila"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "The selected demo dataset is temporarily unavailable.",
        )

        self.assertNotContains(
            response,
            "Missing password configuration",
        )

        self.assertNotContains(
            response,
            "DEMO_PAGILA_PASSWORD",
        )

        self.assertNotContains(
            response,
            "ImproperlyConfigured",
        )

        connection_resolver.assert_called_once_with("pagila")
        data_source_service_class.return_value.configure_and_test.assert_not_called()
        logger_mock.exception.assert_called_once()
