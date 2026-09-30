from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from apps.catalogs.models import CatalogScope
from apps.data_sources.models import DataSource
from apps.projects.exceptions import (
    ArchivedProjectError,
    InvalidProjectStateError,
)
from apps.projects.models import Project
from apps.projects.services import ProjectService
from apps.projects.tests.factories import create_test_project


class ProjectServiceTests(TestCase):
    def test_archive_project_sets_status_to_archived(self):
        project = create_test_project(
            name="Sales project",
            status=Project.Status.READY,
        )

        service = ProjectService()

        service.archive(project)

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.ARCHIVED,
        )

    def test_archive_rejects_incomplete_project(self):
        project = create_test_project(
            status=Project.Status.CONFIGURING,
        )

        with self.assertRaises(InvalidProjectStateError):
            ProjectService().archive(project)

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.CONFIGURING,
        )

    def test_restore_archived_project_sets_status_to_ready(self):
        project = create_test_project(
            status=Project.Status.ARCHIVED,
        )

        ProjectService().restore(project)

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.READY,
        )

    def test_restore_rejects_active_project(self):
        project = create_test_project(
            status=Project.Status.READY,
        )

        with self.assertRaises(InvalidProjectStateError):
            ProjectService().restore(project)

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.READY,
        )

    def test_delete_incomplete_project(self):
        project = create_test_project(
            status=Project.Status.CONFIGURING,
        )
        project_id = project.id

        ProjectService().delete_incomplete(project)

        self.assertFalse(Project.objects.filter(id=project_id).exists())

    def test_delete_incomplete_rejects_ready_project(self):
        project = create_test_project(
            status=Project.Status.READY,
        )

        with self.assertRaises(InvalidProjectStateError):
            ProjectService().delete_incomplete(project)

        self.assertTrue(Project.objects.filter(id=project.id).exists())

    def test_delete_incomplete_rejects_archived_project(self):
        project = create_test_project(
            status=Project.Status.ARCHIVED,
        )

        with self.assertRaises(InvalidProjectStateError):
            ProjectService().delete_incomplete(project)

        self.assertTrue(Project.objects.filter(id=project.id).exists())

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
        newer_project = Project.objects.create(
            owner=user,
            name="Newer project",
        )
        Project.objects.create(
            owner=other_user,
            name="Other project",
        )

        service = ProjectService()

        projects = service.list_for_user(user)

        self.assertEqual(
            list(projects),
            [newer_project, owned_project],
        )

    def test_ensure_writable_allows_active_project(self):
        project = create_test_project(
            status=Project.Status.READY,
        )

        ProjectService().ensure_writable(project)

    def test_ensure_writable_rejects_archived_project(self):
        project = create_test_project(
            status=Project.Status.ARCHIVED,
        )

        with self.assertRaises(ArchivedProjectError):
            ProjectService().ensure_writable(project)

    def test_ensure_setup_incomplete_allows_incomplete_project_statuses(self):
        allowed_statuses = [
            Project.Status.DRAFT,
            Project.Status.CONFIGURING,
            Project.Status.BUILDING_CATALOG,
        ]

        for status in allowed_statuses:
            with self.subTest(status=status):
                project = create_test_project(
                    status=status,
                )

                ProjectService().ensure_setup_incomplete(project)

    def test_ensure_setup_incomplete_rejects_completed_project_statuses(self):
        rejected_statuses = [
            Project.Status.READY,
            Project.Status.REGENERATING_CATALOG,
            Project.Status.ARCHIVED,
        ]

        for status in rejected_statuses:
            with self.subTest(status=status):
                project = create_test_project(
                    status=status,
                )

                with self.assertRaises(InvalidProjectStateError):
                    ProjectService().ensure_setup_incomplete(project)

    def test_get_setup_url_name_returns_data_source_when_missing(self):
        project = create_test_project(
            status=Project.Status.DRAFT,
        )

        url_name = ProjectService().get_setup_url_name(project)

        self.assertEqual(
            url_name,
            "data-source-configure",
        )

    def test_get_setup_url_name_returns_catalog_scope_when_data_source_exists(self):
        project = create_test_project(
            status=Project.Status.CONFIGURING,
        )
        DataSource.objects.create(
            project=project,
        )

        url_name = ProjectService().get_setup_url_name(project)

        self.assertEqual(
            url_name,
            "catalog-scope",
        )

    def test_get_setup_url_name_returns_confirmation_when_scope_exists(self):
        project = create_test_project(
            status=Project.Status.CONFIGURING,
        )
        DataSource.objects.create(
            project=project,
        )
        CatalogScope.objects.create(
            project=project,
        )

        url_name = ProjectService().get_setup_url_name(project)

        self.assertEqual(
            url_name,
            "catalog-confirmation",
        )

    def test_get_setup_url_name_handles_residual_building_state(self):
        project = create_test_project(
            status=Project.Status.BUILDING_CATALOG,
        )
        DataSource.objects.create(
            project=project,
        )
        CatalogScope.objects.create(
            project=project,
        )

        url_name = ProjectService().get_setup_url_name(project)

        self.assertEqual(
            url_name,
            "catalog-confirmation",
        )

    def test_get_setup_url_name_rejects_ready_project(self):
        project = create_test_project(
            status=Project.Status.READY,
        )

        with self.assertRaises(InvalidProjectStateError):
            ProjectService().get_setup_url_name(project)
