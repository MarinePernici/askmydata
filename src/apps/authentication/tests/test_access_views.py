from django.test import TestCase
from django.urls import reverse

from apps.authentication.models import AccessRequest


class AccessRequestViewTests(TestCase):
    def test_request_access_page_is_public(self):
        response = self.client.get(reverse("request-access"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "authentication/request_access.html",
        )

    def test_access_request_success_page_is_public(self):
        response = self.client.get(reverse("access-request-success"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "authentication/access_request_success.html",
        )

    def test_valid_access_request_creates_pending_request(self):
        response = self.client.post(
            reverse("request-access"),
            {
                "first_name": "Alice",
                "last_name": "Martin",
                "email": "Alice.Martin@Example.com",
                "reason": "I would like to explore the demo.",
            },
        )

        self.assertRedirects(
            response,
            reverse("access-request-success"),
        )

        self.assertEqual(AccessRequest.objects.count(), 1)

        access_request = AccessRequest.objects.get()

        self.assertEqual(access_request.first_name, "Alice")
        self.assertEqual(access_request.last_name, "Martin")
        self.assertEqual(access_request.email, "alice.martin@example.com")
        self.assertEqual(access_request.status, AccessRequest.Status.PENDING)
        self.assertIsNone(access_request.invitation)

    def test_duplicate_pending_access_request_is_rejected(self):
        AccessRequest.objects.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="First request",
        )

        response = self.client.post(
            reverse("request-access"),
            {
                "first_name": "Alice",
                "last_name": "Martin",
                "email": "ALICE@EXAMPLE.COM",
                "reason": "Second request",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "authentication/request_access.html",
        )

        self.assertFormError(
            response.context["form"],
            "email",
            "An access request is already pending for this email.",
        )

        self.assertEqual(AccessRequest.objects.count(), 1)

    def test_access_request_with_missing_fields_is_rejected(self):
        response = self.client.post(
            reverse("request-access"),
            {
                "first_name": "Alice",
                "last_name": "",
                "email": "alice@example.com",
                "reason": "",
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context["form"]

        self.assertIn("last_name", form.errors)
        self.assertIn("reason", form.errors)

        self.assertFalse(AccessRequest.objects.exists())
