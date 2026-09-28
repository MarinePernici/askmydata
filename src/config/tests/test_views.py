from django.contrib.auth import get_user_model
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
