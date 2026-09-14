from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.data_sources.exceptions import DataSourceConnectionError
from apps.data_sources.models import DataSource
from apps.projects.models import Project


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
        self.assertContains(response, project.name)
        self.assertContains(
            response,
            reverse(
                "project-detail",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertContains(
            response,
            reverse("project-list"),
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
