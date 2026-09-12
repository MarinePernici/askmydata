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