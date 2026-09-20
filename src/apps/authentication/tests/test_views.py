from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LoginViewTests(TestCase):
    def test_user_can_log_in_with_valid_credentials(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "marine",
                "password": "test-password",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertRedirects(
            response,
            reverse("project-list"),
            fetch_redirect_response=False,
        )

        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            user.id,
        )

    def test_login_redirects_to_requested_page_when_next_is_provided(self):
        get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        next_url = reverse("dashboard")

        response = self.client.post(
            f"{reverse('login')}?next={next_url}",
            {
                "username": "marine",
                "password": "test-password",
                "next": next_url,
            },
        )

        self.assertRedirects(
            response,
            next_url,
            fetch_redirect_response=False,
        )

    def test_user_cannot_log_in_with_invalid_credentials(self):
        get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "marine",
                "password": "wrong-password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_user_can_log_out(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse("logout"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertRedirects(
            response,
            reverse("login"),
            fetch_redirect_response=False,
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse("dashboard"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('dashboard')}",
        )

    def test_authenticated_user_can_access_dashboard(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("dashboard"),
        )

        self.assertEqual(response.status_code, 200)

    def test_login_page_displays_askmydata_sign_in_form(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AskMyData")
        self.assertContains(response, "Welcome back")
        self.assertContains(response, "Username")
        self.assertContains(response, "Password")
        self.assertContains(response, "Log in")
