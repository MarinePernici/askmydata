from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.projects.models import Project
from apps.projects.tests.factories import create_test_project


class ProjectModelTests(TestCase):
    def test_create_project(self):
        project = create_test_project(
            name="Demo Project",
            description="Project used for testing.",
        )

        self.assertEqual(project.name, "Demo Project")
        self.assertEqual(project.description, "Project used for testing.")
        self.assertIsNotNone(project.id)
        self.assertIsNotNone(project.created_at)
        self.assertIsNotNone(project.updated_at)

    def test_project_is_draft_by_default(self):
        project = create_test_project(
            name="Sales project",
        )

        self.assertEqual(
            project.status,
            Project.Status.DRAFT,
        )

    def test_project_has_owner(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        project = Project.objects.create(
            name="Test project",
            owner=user,
        )

        self.assertEqual(project.owner, user)
