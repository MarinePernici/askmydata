from django.test import TestCase

from apps.authentication.forms import (
    AccessRequestForm,
    InvitationRegistrationForm,
)
from apps.authentication.models import AccessRequest


class AccessRequestFormTests(TestCase):
    def test_valid_form(self):
        form = AccessRequestForm(
            data={
                "first_name": "Alice",
                "last_name": "Martin",
                "email": "alice@example.com",
                "reason": "I would like to evaluate AskMyData.",
            }
        )

        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        form = AccessRequestForm(data={})

        self.assertFalse(form.is_valid())
        self.assertEqual(
            set(form.errors),
            {
                "first_name",
                "last_name",
                "email",
                "reason",
            },
        )

    def test_rejects_invalid_email(self):
        form = AccessRequestForm(
            data={
                "first_name": "Alice",
                "last_name": "Martin",
                "email": "not-an-email",
                "reason": "I would like to evaluate AskMyData.",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_rejects_duplicate_pending_email_case_insensitively(self):
        AccessRequest.objects.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="First request.",
        )

        form = AccessRequestForm(
            data={
                "first_name": "Alice",
                "last_name": "Martin",
                "email": "ALICE@EXAMPLE.COM",
                "reason": "Second request.",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_allows_email_from_rejected_request(self):
        AccessRequest.objects.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="First request.",
            status=AccessRequest.Status.REJECTED,
        )

        form = AccessRequestForm(
            data={
                "first_name": "Alice",
                "last_name": "Martin",
                "email": "ALICE@EXAMPLE.COM",
                "reason": "Second request.",
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["email"],
            "alice@example.com",
        )


class InvitationRegistrationFormTests(TestCase):
    def test_valid_registration_form(self):
        form = InvitationRegistrationForm(
            data={
                "username": "alice",
                "password1": "StrongPassword2026!",
                "password2": "StrongPassword2026!",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_password_confirmation_mismatch(self):
        form = InvitationRegistrationForm(
            data={
                "username": "alice",
                "password1": "StrongPassword2026!",
                "password2": "DifferentPassword2026!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
