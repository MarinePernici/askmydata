from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.authentication.exceptions import InvalidInvitationError
from apps.authentication.models import AccessRequest, Invitation
from apps.authentication.services import InvitationService


class AccessRequestAdminTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.superuser = User.objects.create_superuser(
            username="admin_test",
            email="admin@example.com",
            password="test-password",
        )

        self.staff_user = User.objects.create_user(
            username="staff_test",
            email="staff@example.com",
            password="test-password",
            is_staff=True,
        )

        self.access_request = AccessRequest.objects.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="I would like to explore the demo.",
        )

        self.approve_url = reverse(
            "admin:authentication_accessrequest_approve",
            args=[self.access_request.pk],
        )

    def test_superuser_can_view_access_requests(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse("admin:authentication_accessrequest_changelist")
        )

        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_view_access_requests(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse("admin:authentication_accessrequest_changelist")
        )

        self.assertEqual(response.status_code, 403)

    def test_approval_requires_post(self):
        self.client.force_login(self.superuser)

        response = self.client.get(self.approve_url)

        self.assertEqual(response.status_code, 405)
        self.assertFalse(Invitation.objects.exists())

    def test_staff_cannot_approve_access_request(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(self.approve_url)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Invitation.objects.exists())

    def test_approval_creates_invitation_and_displays_link(self):
        self.client.force_login(self.superuser)

        response = self.client.post(self.approve_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "admin/authentication/accessrequest/invitation_created.html",
        )

        self.access_request.refresh_from_db()

        self.assertEqual(
            self.access_request.status,
            AccessRequest.Status.APPROVED,
        )
        self.assertEqual(Invitation.objects.count(), 1)
        self.assertEqual(
            self.access_request.invitation,
            Invitation.objects.get(),
        )

        registration_url = response.context["registration_url"]
        raw_token = registration_url.rsplit("/", 2)[-2]

        invitation = InvitationService().get_valid_by_token(raw_token)

        self.assertEqual(invitation, self.access_request.invitation)
        self.assertContains(response, registration_url)
        self.assertContains(response, "alice@example.com")
        self.assertIn("no-store", response["Cache-Control"])

    def test_access_request_cannot_be_approved_twice(self):
        self.client.force_login(self.superuser)

        first_response = self.client.post(self.approve_url)
        second_response = self.client.post(self.approve_url)

        self.assertEqual(first_response.status_code, 200)
        self.assertRedirects(
            second_response,
            reverse("admin:authentication_accessrequest_changelist"),
        )
        self.assertEqual(Invitation.objects.count(), 1)

    def test_rejection_requires_post(self):
        self.client.force_login(self.superuser)

        reject_url = reverse(
            "admin:authentication_accessrequest_reject",
            args=[self.access_request.pk],
        )

        response = self.client.get(reject_url)

        self.assertEqual(response.status_code, 405)
        self.access_request.refresh_from_db()
        self.assertEqual(
            self.access_request.status,
            AccessRequest.Status.PENDING,
        )

    def test_staff_cannot_reject_access_request(self):
        self.client.force_login(self.staff_user)

        reject_url = reverse(
            "admin:authentication_accessrequest_reject",
            args=[self.access_request.pk],
        )

        response = self.client.post(reject_url)

        self.assertEqual(response.status_code, 403)
        self.access_request.refresh_from_db()
        self.assertEqual(
            self.access_request.status,
            AccessRequest.Status.PENDING,
        )

    def test_rejection_updates_request_without_creating_invitation(self):
        self.client.force_login(self.superuser)

        reject_url = reverse(
            "admin:authentication_accessrequest_reject",
            args=[self.access_request.pk],
        )

        response = self.client.post(reject_url)

        self.assertRedirects(
            response,
            reverse("admin:authentication_accessrequest_changelist"),
        )

        self.access_request.refresh_from_db()

        self.assertEqual(
            self.access_request.status,
            AccessRequest.Status.REJECTED,
        )
        self.assertIsNotNone(self.access_request.reviewed_at)
        self.assertIsNone(self.access_request.invitation)
        self.assertFalse(Invitation.objects.exists())

    def test_access_request_cannot_be_rejected_twice(self):
        self.client.force_login(self.superuser)

        reject_url = reverse(
            "admin:authentication_accessrequest_reject",
            args=[self.access_request.pk],
        )

        self.client.post(reject_url)
        second_response = self.client.post(reject_url)

        self.assertRedirects(
            second_response,
            reverse("admin:authentication_accessrequest_changelist"),
        )

        self.access_request.refresh_from_db()

        self.assertEqual(
            self.access_request.status,
            AccessRequest.Status.REJECTED,
        )
        self.assertFalse(Invitation.objects.exists())

    def test_approval_requires_csrf_token(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        client.force_login(self.superuser)

        response = client.post(self.approve_url)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Invitation.objects.exists())

        self.access_request.refresh_from_db()
        self.assertEqual(
            self.access_request.status,
            AccessRequest.Status.PENDING,
        )


class InvitationAdminTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.superuser = User.objects.create_superuser(
            username="invitation_admin",
            email="admin@example.com",
            password="test-password",
        )

        self.staff_user = User.objects.create_user(
            username="invitation_staff",
            email="staff@example.com",
            password="test-password",
            is_staff=True,
        )

        self.create_url = reverse("admin:authentication_invitation_create")

    def test_superuser_can_access_creation_form(self):
        self.client.force_login(self.superuser)

        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "admin/authentication/invitation/create.html",
        )

    def test_staff_cannot_create_invitation(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            self.create_url,
            {"email": "invitee@example.com"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Invitation.objects.exists())

    def test_create_invitation_displays_valid_registration_link(self):
        self.client.force_login(self.superuser)

        response = self.client.post(
            self.create_url,
            {"email": "INVITEE@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "admin/authentication/invitation/invitation_created.html",
        )

        invitation = Invitation.objects.get()
        self.assertEqual(invitation.email, "invitee@example.com")

        registration_url = response.context["registration_url"]
        raw_token = registration_url.rsplit("/", 2)[-2]

        self.assertEqual(
            InvitationService().get_valid_by_token(raw_token),
            invitation,
        )
        self.assertContains(response, registration_url)
        self.assertIn("no-store", response["Cache-Control"])

    def test_create_rejects_existing_user(self):
        User = get_user_model()
        User.objects.create_user(
            username="existing_user",
            email="invitee@example.com",
            password="test-password",
        )

        self.client.force_login(self.superuser)

        response = self.client.post(
            self.create_url,
            {"email": "invitee@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertFalse(Invitation.objects.exists())

    def test_create_rejects_active_invitation(self):
        InvitationService().create("invitee@example.com")
        self.client.force_login(self.superuser)

        response = self.client.post(
            self.create_url,
            {"email": "invitee@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertEqual(Invitation.objects.count(), 1)

    def test_create_rejects_pending_access_request(self):
        AccessRequest.objects.create(
            first_name="Alice",
            last_name="Martin",
            email="invitee@example.com",
            reason="Demo access",
        )

        self.client.force_login(self.superuser)

        response = self.client.post(
            self.create_url,
            {"email": "invitee@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertFalse(Invitation.objects.exists())

    def test_revocation_requires_post(self):
        self.client.force_login(self.superuser)
        invitation, _ = InvitationService().create("invitee@example.com")

        revoke_url = reverse(
            "admin:authentication_invitation_revoke",
            args=[invitation.pk],
        )

        response = self.client.get(revoke_url)

        self.assertEqual(response.status_code, 405)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, Invitation.Status.PENDING)

    def test_staff_cannot_revoke_invitation(self):
        self.client.force_login(self.staff_user)
        invitation, _ = InvitationService().create("invitee@example.com")

        revoke_url = reverse(
            "admin:authentication_invitation_revoke",
            args=[invitation.pk],
        )

        response = self.client.post(revoke_url)

        self.assertEqual(response.status_code, 403)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, Invitation.Status.PENDING)

    def test_revocation_updates_invitation(self):
        self.client.force_login(self.superuser)
        invitation, raw_token = InvitationService().create("invitee@example.com")

        revoke_url = reverse(
            "admin:authentication_invitation_revoke",
            args=[invitation.pk],
        )

        response = self.client.post(revoke_url)

        self.assertRedirects(
            response,
            reverse("admin:authentication_invitation_changelist"),
        )

        invitation.refresh_from_db()

        self.assertEqual(invitation.status, Invitation.Status.REVOKED)
        self.assertIsNotNone(invitation.revoked_at)

        with self.assertRaises(InvalidInvitationError):
            InvitationService().get_valid_by_token(raw_token)

    def test_invitation_cannot_be_revoked_twice(self):
        self.client.force_login(self.superuser)
        invitation, _ = InvitationService().create("invitee@example.com")

        revoke_url = reverse(
            "admin:authentication_invitation_revoke",
            args=[invitation.pk],
        )

        self.client.post(revoke_url)
        second_response = self.client.post(revoke_url)

        self.assertRedirects(
            second_response,
            reverse("admin:authentication_invitation_changelist"),
        )

        invitation.refresh_from_db()

        self.assertEqual(invitation.status, Invitation.Status.REVOKED)
        self.assertEqual(Invitation.objects.count(), 1)

    def test_invitation_detail_does_not_display_token_hash(self):
        self.client.force_login(self.superuser)
        invitation, _ = InvitationService().create("invitee@example.com")

        detail_url = reverse(
            "admin:authentication_invitation_change",
            args=[invitation.pk],
        )

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, invitation.token_hash)
