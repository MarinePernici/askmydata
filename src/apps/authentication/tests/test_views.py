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

        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            user.id,
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