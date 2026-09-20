from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.projects.context_processors import sidebar_projects
from apps.projects.models import Project


class SidebarProjectsContextProcessorTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="sidebar-user",
            password="test-password",
        )
        self.factory = RequestFactory()

    def test_sidebar_contains_operational_and_archived_projects(self):
        ready_project = Project.objects.create(
            owner=self.user,
            name="Ready project",
            status=Project.Status.READY,
        )
        regenerating_project = Project.objects.create(
            owner=self.user,
            name="Regenerating project",
            status=Project.Status.REGENERATING_CATALOG,
        )
        archived_project = Project.objects.create(
            owner=self.user,
            name="Archived project",
            status=Project.Status.ARCHIVED,
        )

        Project.objects.create(
            owner=self.user,
            name="Draft project",
            status=Project.Status.DRAFT,
        )

        request = self.factory.get("/")
        request.user = self.user

        projects = list(sidebar_projects(request)["sidebar_projects"])

        self.assertEqual(
            projects,
            [
                archived_project,
                ready_project,
                regenerating_project,
            ],
        )

    def test_sidebar_excludes_other_users_projects(self):
        other_user = get_user_model().objects.create_user(
            username="other-user",
            password="test-password",
        )

        own_project = Project.objects.create(
            owner=self.user,
            name="Own project",
            status=Project.Status.READY,
        )
        Project.objects.create(
            owner=other_user,
            name="Other project",
            status=Project.Status.READY,
        )

        request = self.factory.get("/")
        request.user = self.user

        projects = list(sidebar_projects(request)["sidebar_projects"])

        self.assertEqual(projects, [own_project])
