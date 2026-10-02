from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse


class LandingViewTests(TestCase):
    def test_landing_is_publicly_accessible(self):
        response = self.client.get(reverse("landing"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "landing.html")

    def test_authenticated_user_remains_on_landing(self):
        user = get_user_model().objects.create_user(
            username="landing-user",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("landing"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "landing.html")
        self.assertEqual(response.request["PATH_INFO"], "/")


class HealthCheckViewTests(TestCase):
    def test_liveness_returns_ok(self):
        response = self.client.get(reverse("health-live"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_readiness_returns_ok_when_database_is_available(self):
        response = self.client.get(reverse("health-ready"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("config.views.connection.cursor")
    def test_readiness_returns_unavailable_when_database_is_unavailable(
        self,
        mock_cursor,
    ):
        mock_cursor.side_effect = OperationalError("database unavailable")

        response = self.client.get(reverse("health-ready"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
