from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from apps.projects.models import Project
from apps.projects.services import ProjectService
from apps.projects.tests.factories import create_test_project


class ProjectServiceTests(TestCase):
    def test_archive_project_sets_status_to_archived(self):
        project = create_test_project(
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
        project = create_test_project(
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
        project = create_test_project(
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
        project = create_test_project(
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
        project = create_test_project(
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
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        service = ProjectService()

        project = service.create(
            owner=user,
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
        self.assertEqual(
            project.owner,
            user,
        )
        self.assertTrue(Project.objects.filter(id=project.id).exists())

    def test_update_project_updates_name_and_description(self):
        project = create_test_project(
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
        project = create_test_project(
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

    def test_create_project_assigns_owner(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        service = ProjectService()

        project = service.create(
            owner=user,
            name="Sales analysis",
            description="Analyze sales data.",
        )

        self.assertEqual(project.owner, user)

    def test_get_project_returns_project_for_owner(self):
        owner = get_user_model().objects.create_user(
            username="owner",
            password="test-password",
        )

        project = Project.objects.create(
            owner=owner,
            name="Test project",
        )

        service = ProjectService()

        result = service.get_for_user(
            project_id=project.id,
            user=owner,
        )

        self.assertEqual(result, project)

    def test_get_project_hides_project_from_non_owner(self):
        owner = get_user_model().objects.create_user(
            username="owner2",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="other2",
            password="test-password",
        )

        project = Project.objects.create(
            owner=owner,
            name="Private project",
        )

        service = ProjectService()

        with self.assertRaises(ObjectDoesNotExist):
            service.get_for_user(
                project_id=project.id,
                user=other_user,
            )

    def test_list_for_user_returns_only_owned_projects(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="other",
            password="test-password",
        )

        owned_project = Project.objects.create(
            owner=user,
            name="Owned project",
        )
        Project.objects.create(
            owner=other_user,
            name="Other project",
        )

        service = ProjectService()

        projects = service.list_for_user(user)

        self.assertEqual(list(projects), [owned_project])
