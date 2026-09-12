from django.test import TestCase

from apps.projects.models import Project


class ProjectModelTests(TestCase):
    def test_create_project(self):
        project = Project.objects.create(
            name="Demo Project",
            description="Project used for testing.",
        )

        self.assertEqual(project.name, "Demo Project")
        self.assertEqual(project.description, "Project used for testing.")
        self.assertIsNotNone(project.id)
        self.assertIsNotNone(project.created_at)
        self.assertIsNotNone(project.updated_at)

    def test_project_is_draft_by_default(self):
        project = Project.objects.create(
            name="Sales project",
        )

        self.assertEqual(
            project.status,
            Project.Status.DRAFT,
        )