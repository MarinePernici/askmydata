from django.test import TestCase

from apps.projects.models import Project
from apps.projects.services import ProjectService


class ProjectServiceTests(TestCase):
    def test_archive_project_sets_status_to_archived(self):
        project = Project.objects.create(
            name="Sales project",
        )

        service = ProjectService()

        service.archive(project)

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.ARCHIVED,
        )

    def test_mark_configuring_sets_status_to_configuring(self):
        project = Project.objects.create(
            name="Sales project",
        )

        service = ProjectService()

        service.mark_configuring(project)

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.CONFIGURING,
        )

    def test_mark_building_catalog_sets_status_to_building_catalog(self):
        project = Project.objects.create(
            name="Sales project",
            status=Project.Status.CONFIGURING,
        )

        service = ProjectService()

        service.mark_building_catalog(project)

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.BUILDING_CATALOG,
        )

    def test_mark_ready_sets_status_to_ready(self):
        project = Project.objects.create(
            name="Sales project",
            status=Project.Status.BUILDING_CATALOG,
        )

        service = ProjectService()

        service.mark_ready(project)

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.READY,
        )

    def test_mark_regenerating_catalog_sets_status_to_regenerating_catalog(self):
        project = Project.objects.create(
            name="Sales project",
            status=Project.Status.READY,
        )

        service = ProjectService()

        service.mark_regenerating_catalog(project)

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.REGENERATING_CATALOG,
        )

    def test_create_project_creates_draft_project(self):
        service = ProjectService()

        project = service.create(
            name="Sales analysis",
            description="Analyze sales data.",
        )

        self.assertEqual(
            project.name,
            "Sales analysis",
        )
        self.assertEqual(
            project.description,
            "Analyze sales data.",
        )
        self.assertEqual(
            project.status,
            Project.Status.DRAFT,
        )
        self.assertTrue(
            Project.objects.filter(id=project.id).exists()
        )

    def test_update_project_updates_name_and_description(self):
        project = Project.objects.create(
            name="Old name",
            description="Old description",
        )

        service = ProjectService()

        service.update(
            project=project,
            name="New name",
            description="New description",
        )

        project.refresh_from_db()

        self.assertEqual(
            project.name,
            "New name",
        )
        self.assertEqual(
            project.description,
            "New description",
        )

    def test_archive_is_idempotent(self):
        project = Project.objects.create(
            name="Test project",
            status=Project.Status.ARCHIVED,
        )
        service = ProjectService()

        service.archive(project)

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.ARCHIVED,
        )