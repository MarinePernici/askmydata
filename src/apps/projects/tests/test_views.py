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
        self.assertContains(
            response,
            reverse(
                "project-detail",
                kwargs={"project_id": own_project.id},
            ),
        )

    def test_project_list_displays_create_project_action(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("project-list"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create project")
        self.assertContains(
            response,
            reverse("project-create"),
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse("project-list"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('project-list')}",
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

        self.assertEqual(
            response.url,
            reverse(
                "data-source-configure",
                kwargs={"project_id": project.id},
            ),
        )

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
            f"{reverse('login')}?next={reverse('project-create')}",
        )
        self.assertFalse(Project.objects.filter(name="New project").exists())

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

    def test_project_detail_redirects_owner_to_data_overview(self):
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

        self.assertRedirects(
            response,
            reverse(
                "data-overview",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )

    def test_user_can_update_own_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Old name",
            description="Old description",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-update",
                kwargs={"project_id": project.id},
            ),
            {
                "name": "New name",
                "description": "New description",
            },
        )

        self.assertEqual(response.status_code, 302)

        project.refresh_from_db()

        self.assertEqual(project.name, "New name")
        self.assertEqual(project.description, "New description")

    def test_user_cannot_update_another_users_project(self):
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
            description="Original description",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-update",
                kwargs={"project_id": project.id},
            ),
            {
                "name": "Hacked name",
                "description": "Hacked description",
            },
        )

        self.assertEqual(response.status_code, 404)

        project.refresh_from_db()

        self.assertEqual(project.name, "Other project")
        self.assertEqual(project.description, "Original description")

    def test_user_can_archive_own_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Project to archive",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-archive",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 302)

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.ARCHIVED,
        )

    def test_user_cannot_archive_another_users_project(self):
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

        response = self.client.post(
            reverse(
                "project-archive",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)

        project.refresh_from_db()

        self.assertNotEqual(
            project.status,
            Project.Status.ARCHIVED,
        )

    def test_user_cannot_create_project_without_name(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("project-create"),
            {
                "name": "",
                "description": "Test description",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.exists())

    def test_user_cannot_update_project_without_name(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Original name",
            description="Original description",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-update",
                kwargs={"project_id": project.id},
            ),
            {
                "name": "",
                "description": "Updated description",
            },
        )

        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()

        self.assertEqual(project.name, "Original name")
        self.assertEqual(project.description, "Original description")

    def test_create_project_without_name_displays_form_error(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("project-create"),
            {
                "name": "",
                "description": "Test description",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_update_project_without_name_displays_form_error(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Original name",
            description="Original description",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-update",
                kwargs={"project_id": project.id},
            ),
            {
                "name": "",
                "description": "Updated description",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_user_cannot_create_project_with_blank_name(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("project-create"),
            {
                "name": "   ",
                "description": "Test description",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.exists())
        self.assertContains(response, "This field is required.")
