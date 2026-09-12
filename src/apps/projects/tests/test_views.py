from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.projects.models import Project


class ProjectListViewTests(TestCase):
    def test_user_only_sees_own_projects(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="other-user",
            password="test-password",
        )

        own_project = Project.objects.create(
            owner=user,
            name="My project",
        )
        other_project = Project.objects.create(
            owner=other_user,
            name="Other project",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("project-list"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own_project.name)
        self.assertNotContains(response, other_project.name)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse("project-list"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("project-list")}',
        )

    def test_authenticated_user_can_create_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("project-create"),
            {
                "name": "New project",
                "description": "Test description",
            },
        )

        self.assertEqual(response.status_code, 302)

        project = Project.objects.get(name="New project")

        self.assertEqual(project.owner, user)
        self.assertEqual(project.description, "Test description")

    def test_anonymous_user_cannot_create_project(self):
        response = self.client.post(
            reverse("project-create"),
            {
                "name": "New project",
                "description": "Test description",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("project-create")}',
        )
        self.assertFalse(
            Project.objects.filter(name="New project").exists()
        )

    def test_user_cannot_access_another_users_project(self):
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
                "project-detail",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)

    def test_user_can_access_own_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            owner=user,
            name="My project",
            description="My description",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "project-detail",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, project.name)
        self.assertContains(response, project.description)