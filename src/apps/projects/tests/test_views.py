from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalogs.models import CatalogScope
from apps.data_sources.models import DataSource
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

    def test_user_can_access_project_setup_info_for_incomplete_project(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Setup project",
            description="Setup description",
            status=Project.Status.CONFIGURING,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "project-setup-info",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Setup project")
        self.assertContains(response, "Setup description")

    def test_user_can_update_project_info_during_setup(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Old name",
            description="Old description",
            status=Project.Status.CONFIGURING,
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-setup-info",
                kwargs={"project_id": project.id},
            ),
            {
                "name": "New name",
                "description": "New description",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "data-source-configure",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )

        project.refresh_from_db()

        self.assertEqual(project.name, "New name")
        self.assertEqual(project.description, "New description")
        self.assertEqual(Project.objects.filter(owner=user).count(), 1)

    def test_ready_project_cannot_access_project_setup_info(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Ready project",
            status=Project.Status.READY,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "project-setup-info",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertRedirects(
            response,
            reverse(
                "project-detail",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )

    def test_user_cannot_access_another_users_project_setup_info(self):
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
            status=Project.Status.CONFIGURING,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "project-setup-info",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)

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
            status=Project.Status.READY,
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

    def test_user_cannot_archive_incomplete_project(self):
        user = get_user_model().objects.create_user(
            username="archive-incomplete-user",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Incomplete project",
            status=Project.Status.CONFIGURING,
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

        self.assertEqual(
            project.status,
            Project.Status.CONFIGURING,
        )

    def test_user_can_restore_own_archived_project(self):
        user = get_user_model().objects.create_user(
            username="restore-user",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Archived project",
            status=Project.Status.ARCHIVED,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-restore",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertRedirects(
            response,
            reverse(
                "project-detail",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.READY,
        )

    def test_user_cannot_restore_active_project(self):
        user = get_user_model().objects.create_user(
            username="restore-active-user",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Ready project",
            status=Project.Status.READY,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-restore",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)

        project.refresh_from_db()

        self.assertEqual(
            project.status,
            Project.Status.READY,
        )

    def test_user_can_delete_own_incomplete_project(self):
        user = get_user_model().objects.create_user(
            username="delete-incomplete-user",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Incomplete project",
            status=Project.Status.CONFIGURING,
        )
        project_id = project.id
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-delete",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertRedirects(
            response,
            reverse("project-list"),
        )

        self.assertFalse(Project.objects.filter(id=project_id).exists())

    def test_user_cannot_delete_ready_project(self):
        user = get_user_model().objects.create_user(
            username="delete-ready-user",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Ready project",
            status=Project.Status.READY,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-delete",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Project.objects.filter(id=project.id).exists())

    def test_user_cannot_restore_another_users_project(self):
        user = get_user_model().objects.create_user(
            username="restore-user",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="restore-other-user",
            password="test-password",
        )
        project = Project.objects.create(
            owner=other_user,
            name="Other archived project",
            status=Project.Status.ARCHIVED,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-restore",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)

        project.refresh_from_db()
        self.assertEqual(
            project.status,
            Project.Status.ARCHIVED,
        )

    def test_user_cannot_delete_another_users_project(self):
        user = get_user_model().objects.create_user(
            username="delete-user",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="delete-other-user",
            password="test-password",
        )
        project = Project.objects.create(
            owner=other_user,
            name="Other incomplete project",
            status=Project.Status.CONFIGURING,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-delete",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 404)

        self.assertTrue(Project.objects.filter(id=project.id).exists())

    def test_project_list_groups_projects_by_lifecycle_status(self):
        user = get_user_model().objects.create_user(
            username="project-list-user",
            password="test-password",
        )
        other_user = get_user_model().objects.create_user(
            username="other-project-list-user",
            password="test-password",
        )

        ready_project = Project.objects.create(
            owner=user,
            name="Ready project",
            status=Project.Status.READY,
        )
        regenerating_project = Project.objects.create(
            owner=user,
            name="Regenerating project",
            status=Project.Status.REGENERATING_CATALOG,
        )
        draft_project = Project.objects.create(
            owner=user,
            name="Draft project",
            status=Project.Status.DRAFT,
        )
        configuring_project = Project.objects.create(
            owner=user,
            name="Configuring project",
            status=Project.Status.CONFIGURING,
        )
        building_project = Project.objects.create(
            owner=user,
            name="Building project",
            status=Project.Status.BUILDING_CATALOG,
        )
        archived_project = Project.objects.create(
            owner=user,
            name="Archived project",
            status=Project.Status.ARCHIVED,
        )

        Project.objects.create(
            owner=other_user,
            name="Other user's project",
            status=Project.Status.READY,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("project-list"),
        )

        self.assertEqual(response.status_code, 200)

        self.assertQuerySetEqual(
            response.context["active_projects"],
            [regenerating_project, ready_project],
        )

        self.assertQuerySetEqual(
            response.context["setup_projects"],
            [building_project, configuring_project, draft_project],
        )
        self.assertQuerySetEqual(
            response.context["archived_projects"],
            [archived_project],
            ordered=False,
        )

    def test_project_list_provides_setup_destination_for_incomplete_projects(self):
        user = get_user_model().objects.create_user(
            username="setup-destination-user",
            password="test-password",
        )

        draft_project = Project.objects.create(
            owner=user,
            name="Draft project",
            status=Project.Status.DRAFT,
        )

        configuring_project = Project.objects.create(
            owner=user,
            name="Configuring project",
            status=Project.Status.CONFIGURING,
        )
        DataSource.objects.create(
            project=configuring_project,
        )

        confirmation_project = Project.objects.create(
            owner=user,
            name="Confirmation project",
            status=Project.Status.CONFIGURING,
        )
        DataSource.objects.create(
            project=confirmation_project,
        )
        CatalogScope.objects.create(
            project=confirmation_project,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("project-list"),
        )

        setup_items = {
            item["project"].id: item["setup_url_name"]
            for item in response.context["setup_project_items"]
        }

        self.assertEqual(
            setup_items[draft_project.id],
            "data-source-configure",
        )
        self.assertEqual(
            setup_items[configuring_project.id],
            "catalog-scope",
        )
        self.assertEqual(
            setup_items[confirmation_project.id],
            "catalog-confirmation",
        )

    def test_user_cannot_update_archived_project(self):
        user = get_user_model().objects.create_user(
            username="archived-update-user",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Archived project",
            description="Original description",
            status=Project.Status.ARCHIVED,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "project-update",
                kwargs={"project_id": project.id},
            ),
            {
                "name": "Modified project",
                "description": "Modified description",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "project-update",
                kwargs={"project_id": project.id},
            ),
            fetch_redirect_response=False,
        )

        project.refresh_from_db()

        self.assertEqual(project.name, "Archived project")
        self.assertEqual(project.description, "Original description")

    def test_archived_project_settings_are_read_only(self):
        user = get_user_model().objects.create_user(
            username="archived-settings-user",
            password="test-password",
        )
        project = Project.objects.create(
            owner=user,
            name="Archived project",
            status=Project.Status.ARCHIVED,
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "project-update",
                kwargs={"project_id": project.id},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Restore project")
        self.assertContains(response, "disabled")
        self.assertNotContains(response, "Save changes")
        self.assertNotContains(response, "Archive project")
