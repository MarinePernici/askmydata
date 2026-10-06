from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse

from apps.authentication.models import UserPreferences


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

    def test_anonymous_user_can_switch_to_french(self):
        response = self.client.post(
            reverse("set_language"),
            {
                "language": "fr",
                "next": reverse("landing"),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, "fr")

    def test_anonymous_user_sees_french_landing_after_switch(self):
        response = self.client.post(
            reverse("set_language"),
            {
                "language": "fr",
                "next": reverse("landing"),
            },
            follow=True,
        )

        self.assertContains(response, "Comment ça marche")
        self.assertContains(response, "Se connecter")

    def test_authenticated_user_can_switch_language_from_landing(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        UserPreferences.objects.create(
            user=user,
            language=UserPreferences.Language.FRENCH,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("set-interface-language"),
            {
                "language": "en",
                "next": reverse("landing"),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, "en")

        user.preferences.refresh_from_db()
        self.assertEqual(
            user.preferences.language,
            UserPreferences.Language.ENGLISH,
        )

        self.assertContains(response, "How it works")


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
