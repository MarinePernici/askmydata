from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.authentication.services import InvitationService


class InvitationRegistrationViewTests(TestCase):
    def test_valid_invitation_displays_registration_form(self):
        invitation, token = InvitationService().create(email="alice@example.com")

        response = self.client.get(
            reverse("invitation-register", kwargs={"token": token})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "authentication/register.html",
        )
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'name="password2"')
        self.assertNotContains(response, 'name="email"')

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, invitation.Status.PENDING)

    def test_invalid_invitation_returns_404(self):
        response = self.client.get(
            reverse(
                "invitation-register",
                kwargs={"token": "invalid-token"},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_revoked_invitation_returns_404(self):
        invitation, token = InvitationService().create(email="alice@example.com")
        InvitationService().revoke(invitation)

        response = self.client.get(
            reverse(
                "invitation-register",
                kwargs={"token": token},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_expired_invitation_returns_404(self):
        invitation, token = InvitationService().create(email="alice@example.com")

        invitation.expires_at = timezone.now() - timedelta(minutes=1)
        invitation.save(update_fields=["expires_at"])

        response = self.client.get(
            reverse(
                "invitation-register",
                kwargs={"token": token},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_valid_invitation_creates_account_and_logs_user_in(self):
        invitation, token = InvitationService().create(email="alice@example.com")

        response = self.client.post(
            reverse(
                "invitation-register",
                kwargs={"token": token},
            ),
            data={
                "username": "alice",
                "password1": "StrongPassword2026!",
                "password2": "StrongPassword2026!",
            },
        )

        user = get_user_model().objects.get(username="alice")

        self.assertEqual(user.email, "alice@example.com")
        self.assertTrue(user.check_password("StrongPassword2026!"))

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, invitation.Status.ACCEPTED)
        self.assertIsNotNone(invitation.accepted_at)

        self.assertEqual(
            str(self.client.session["_auth_user_id"]),
            str(user.pk),
        )
        self.assertEqual(response.status_code, 302)

    def test_accepted_invitation_cannot_be_reused(self):
        invitation, token = InvitationService().create(email="alice@example.com")

        url = reverse(
            "invitation-register",
            kwargs={"token": token},
        )

        self.client.post(
            url,
            data={
                "username": "alice",
                "password1": "StrongPassword2026!",
                "password2": "StrongPassword2026!",
            },
        )

        response = self.client.post(
            url,
            data={
                "username": "bob",
                "password1": "AnotherStrongPassword2026!",
                "password2": "AnotherStrongPassword2026!",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(get_user_model().objects.filter(username="bob").exists())
        self.assertEqual(get_user_model().objects.count(), 1)

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, invitation.Status.ACCEPTED)

    def test_invalid_registration_form_does_not_create_account(self):
        invitation, token = InvitationService().create(email="alice@example.com")

        response = self.client.post(
            reverse(
                "invitation-register",
                kwargs={"token": token},
            ),
            data={
                "username": "alice",
                "password1": "StrongPassword2026!",
                "password2": "DifferentPassword2026!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "authentication/register.html",
        )
        self.assertContains(response, 'name="password2"')
        self.assertTrue(response.context["form"].errors)

        self.assertFalse(get_user_model().objects.filter(username="alice").exists())

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, invitation.Status.PENDING)
        self.assertIsNone(invitation.accepted_at)

    def test_existing_username_does_not_consume_invitation(self):
        get_user_model().objects.create_user(
            username="alice",
            email="existing@example.com",
            password="ExistingPassword2026!",
        )

        invitation, token = InvitationService().create(email="new@example.com")

        response = self.client.post(
            reverse(
                "invitation-register",
                kwargs={"token": token},
            ),
            data={
                "username": "alice",
                "password1": "StrongPassword2026!",
                "password2": "StrongPassword2026!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("username", response.context["form"].errors)

        self.assertEqual(get_user_model().objects.count(), 1)

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, invitation.Status.PENDING)
        self.assertIsNone(invitation.accepted_at)

    def test_accepted_invitation_returns_404_on_get(self):
        _, token = InvitationService().create(email="alice@example.com")

        InvitationService().accept(
            token,
            username="alice",
            password="StrongPassword2026!",
        )

        response = self.client.get(
            reverse(
                "invitation-register",
                kwargs={"token": token},
            )
        )

        self.assertEqual(response.status_code, 404)
