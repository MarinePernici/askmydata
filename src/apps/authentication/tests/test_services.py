import hashlib
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.authentication.exceptions import (
    AccountAlreadyExistsError,
    ActiveInvitationExistsError,
    InvalidAccessRequestError,
    InvalidInvitationError,
    InvitationExpiredError,
    PendingAccessRequestExistsError,
)
from apps.authentication.models import AccessRequest, Invitation
from apps.authentication.services import (
    AccessRequestService,
    InvitationService,
)


class InvitationServiceTests(TestCase):
    def setUp(self):
        self.service = InvitationService()

    def test_create_invitation(self):
        invitation, raw_token = self.service.create("invitee@example.com")

        self.assertEqual(invitation.email, "invitee@example.com")
        self.assertEqual(invitation.status, Invitation.Status.PENDING)
        self.assertEqual(
            invitation.token_hash,
            hashlib.sha256(raw_token.encode()).hexdigest(),
        )
        self.assertNotEqual(invitation.token_hash, raw_token)
        self.assertGreater(invitation.expires_at, timezone.now())

    def test_create_invitation_uses_default_expiration(self):
        before_creation = timezone.now()

        invitation, _ = self.service.create("invitee@example.com")

        expected_expiration = before_creation + timedelta(
            days=InvitationService.DEFAULT_EXPIRATION_DAYS
        )

        self.assertAlmostEqual(
            invitation.expires_at,
            expected_expiration,
            delta=timedelta(seconds=1),
        )

    def test_get_valid_by_token_returns_invitation(self):
        invitation, raw_token = self.service.create("invitee@example.com")

        result = self.service.get_valid_by_token(raw_token)

        self.assertEqual(result, invitation)

    def test_get_by_token_rejects_unknown_token(self):
        with self.assertRaises(InvalidInvitationError):
            self.service.get_by_token("unknown-token")

    def test_validate_rejects_expired_invitation(self):
        invitation = Invitation.objects.create(
            email="invitee@example.com",
            token_hash="a" * 64,
            expires_at=timezone.now() - timedelta(seconds=1),
        )

        with self.assertRaises(InvitationExpiredError):
            self.service.validate(invitation)

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.status,
            Invitation.Status.PENDING,
        )

    def test_validate_rejects_accepted_invitation(self):
        invitation = Invitation.objects.create(
            email="invitee@example.com",
            token_hash="b" * 64,
            status=Invitation.Status.ACCEPTED,
            expires_at=timezone.now() + timedelta(days=1),
        )

        with self.assertRaises(InvalidInvitationError):
            self.service.validate(invitation)

    def test_validate_rejects_revoked_invitation(self):
        invitation = Invitation.objects.create(
            email="invitee@example.com",
            token_hash="c" * 64,
            status=Invitation.Status.REVOKED,
            expires_at=timezone.now() + timedelta(days=1),
        )

        with self.assertRaises(InvalidInvitationError):
            self.service.validate(invitation)

    def test_revoke_invitation(self):
        invitation, _ = self.service.create("invitee@example.com")

        self.service.revoke(invitation)

        invitation.refresh_from_db()

        self.assertEqual(invitation.status, Invitation.Status.REVOKED)
        self.assertIsNotNone(invitation.revoked_at)

    def test_revoke_rejects_non_pending_invitation(self):
        invitation = Invitation.objects.create(
            email="invitee@example.com",
            token_hash="d" * 64,
            status=Invitation.Status.ACCEPTED,
            expires_at=timezone.now() + timedelta(days=1),
        )

        with self.assertRaises(InvalidInvitationError):
            self.service.revoke(invitation)

    def test_accept_creates_user_and_marks_invitation_as_accepted(self):
        invitation, raw_token = self.service.create("invitee@example.com")

        user = self.service.accept(
            raw_token,
            username="invitee",
            password="test-password",
        )

        invitation.refresh_from_db()

        self.assertEqual(user.username, "invitee")
        self.assertEqual(user.email, "invitee@example.com")
        self.assertTrue(user.check_password("test-password"))
        self.assertEqual(invitation.status, Invitation.Status.ACCEPTED)
        self.assertIsNotNone(invitation.accepted_at)

    def test_accept_rejects_already_accepted_invitation(self):
        _, raw_token = self.service.create("invitee@example.com")
        self.service.accept(
            raw_token,
            username="invitee",
            password="test-password",
        )

        with self.assertRaises(InvalidInvitationError):
            self.service.accept(
                raw_token,
                username="second-user",
                password="test-password",
            )

        self.assertFalse(
            get_user_model().objects.filter(username="second-user").exists()
        )

    def test_accept_rejects_expired_invitation_without_creating_user(self):
        raw_token = "expired-token"
        invitation = Invitation.objects.create(
            email="invitee@example.com",
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=timezone.now() - timedelta(seconds=1),
        )

        with self.assertRaises(InvitationExpiredError):
            self.service.accept(
                raw_token,
                username="invitee",
                password="test-password",
            )

        self.assertFalse(get_user_model().objects.filter(username="invitee").exists())

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, Invitation.Status.PENDING)
        self.assertIsNone(invitation.accepted_at)

    def test_accept_rolls_back_if_user_creation_fails(self):
        get_user_model().objects.create_user(
            username="existing-user",
            password="test-password",
        )
        invitation, raw_token = self.service.create("invitee@example.com")

        with self.assertRaises(IntegrityError):
            self.service.accept(
                raw_token,
                username="existing-user",
                password="test-password",
            )

        invitation.refresh_from_db()

        self.assertEqual(invitation.status, Invitation.Status.PENDING)
        self.assertIsNone(invitation.accepted_at)

    def test_accept_rejects_unknown_token_without_creating_user(self):
        with self.assertRaises(InvalidInvitationError):
            self.service.accept(
                "unknown-token",
                username="invitee",
                password="test-password",
            )

        self.assertFalse(get_user_model().objects.filter(username="invitee").exists())

    def test_accept_rejects_revoked_invitation_without_creating_user(self):
        invitation, raw_token = self.service.create("invitee@example.com")
        self.service.revoke(invitation)

        with self.assertRaises(InvalidInvitationError):
            self.service.accept(
                raw_token,
                username="invitee",
                password="test-password",
            )

        self.assertFalse(get_user_model().objects.filter(username="invitee").exists())


class AccessRequestServiceTests(TestCase):
    def setUp(self):
        self.service = AccessRequestService()

    def create_access_request(self):
        return AccessRequest.objects.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="I would like to evaluate AskMyData.",
        )

    def test_approve_creates_invitation_and_updates_access_request(self):
        access_request = self.create_access_request()

        access_request, invitation, raw_token = self.service.approve(access_request)

        access_request.refresh_from_db()

        self.assertEqual(
            access_request.status,
            AccessRequest.Status.APPROVED,
        )
        self.assertIsNotNone(access_request.reviewed_at)
        self.assertEqual(access_request.invitation, invitation)

        self.assertEqual(invitation.email, access_request.email)
        self.assertEqual(invitation.status, Invitation.Status.PENDING)
        self.assertTrue(raw_token)
        self.assertEqual(
            invitation.token_hash,
            hashlib.sha256(raw_token.encode()).hexdigest(),
        )

    def test_approve_rejects_non_pending_access_request(self):
        access_request = self.create_access_request()
        self.service.approve(access_request)

        with self.assertRaises(InvalidAccessRequestError):
            self.service.approve(access_request)

        self.assertEqual(Invitation.objects.count(), 1)

    def test_approve_rejects_stale_access_request(self):
        access_request = self.create_access_request()

        stale_request = AccessRequest.objects.get(pk=access_request.pk)

        self.service.approve(access_request)

        with self.assertRaises(InvalidAccessRequestError):
            self.service.approve(stale_request)

        self.assertEqual(Invitation.objects.count(), 1)

    def test_reject_updates_access_request_without_creating_invitation(self):
        access_request = self.create_access_request()

        self.service.reject(access_request)

        access_request.refresh_from_db()

        self.assertEqual(
            access_request.status,
            AccessRequest.Status.REJECTED,
        )
        self.assertIsNotNone(access_request.reviewed_at)
        self.assertIsNone(access_request.invitation)
        self.assertEqual(Invitation.objects.count(), 0)

    def test_reject_rejects_non_pending_access_request(self):
        access_request = self.create_access_request()
        self.service.reject(access_request)

        with self.assertRaises(InvalidAccessRequestError):
            self.service.reject(access_request)

        self.assertEqual(Invitation.objects.count(), 0)

    def test_reject_rejects_stale_access_request(self):
        access_request = self.create_access_request()

        stale_request = AccessRequest.objects.get(pk=access_request.pk)

        self.service.approve(access_request)

        with self.assertRaises(InvalidAccessRequestError):
            self.service.reject(stale_request)

        access_request.refresh_from_db()

        self.assertEqual(access_request.status, AccessRequest.Status.APPROVED)
        self.assertEqual(Invitation.objects.count(), 1)

    def test_create_access_request(self):
        access_request = self.service.create(
            first_name=" Alice ",
            last_name=" Martin ",
            email=" Alice@Example.COM ",
            reason=" I would like to evaluate AskMyData. ",
        )

        self.assertEqual(access_request.first_name, "Alice")
        self.assertEqual(access_request.last_name, "Martin")
        self.assertEqual(access_request.email, "alice@example.com")
        self.assertEqual(
            access_request.reason,
            "I would like to evaluate AskMyData.",
        )
        self.assertEqual(
            access_request.status,
            AccessRequest.Status.PENDING,
        )

    def test_create_rejects_duplicate_pending_request_case_insensitively(self):
        self.service.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="First request.",
        )

        with self.assertRaises(PendingAccessRequestExistsError):
            self.service.create(
                first_name="Alice",
                last_name="Martin",
                email="ALICE@EXAMPLE.COM",
                reason="Second request.",
            )

        self.assertEqual(AccessRequest.objects.count(), 1)

    def test_create_allows_new_request_after_rejection(self):
        first_request = self.service.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="First request.",
        )
        self.service.reject(first_request)

        second_request = self.service.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="Second request.",
        )

        self.assertEqual(
            second_request.status,
            AccessRequest.Status.PENDING,
        )
        self.assertEqual(AccessRequest.objects.count(), 2)

    def test_create_rejects_new_request_with_active_invitation(self):
        first_request = self.create_access_request()
        self.service.approve(first_request)

        with self.assertRaises(ActiveInvitationExistsError):
            self.service.create(
                first_name="Alice",
                last_name="Martin",
                email="ALICE@example.com",
                reason="Second request.",
            )

        self.assertEqual(AccessRequest.objects.count(), 1)

    def test_create_allows_new_request_after_invitation_expiration(self):
        first_request = self.create_access_request()
        _, invitation, _ = self.service.approve(first_request)

        invitation.expires_at = timezone.now() - timedelta(minutes=1)
        invitation.save(update_fields=["expires_at"])

        second_request = self.service.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="Second request.",
        )

        self.assertEqual(
            second_request.status,
            AccessRequest.Status.PENDING,
        )
        self.assertEqual(AccessRequest.objects.count(), 2)

    def test_create_handles_database_uniqueness_conflict(self):
        self.create_access_request()

        with (
            patch(
                "apps.authentication.services.AccessRequest.objects.filter"
            ) as mock_filter,
            patch(
                "apps.authentication.services.AccessRequest.objects.create",
                side_effect=IntegrityError("Duplicate pending email"),
            ),
        ):
            mock_filter.return_value.exists.side_effect = [False, True]

            with self.assertRaises(PendingAccessRequestExistsError):
                self.service.create(
                    first_name="Alice",
                    last_name="Martin",
                    email="ALICE@example.com",
                    reason="Another access request",
                )

            self.assertEqual(mock_filter.return_value.exists.call_count, 2)

    def test_create_propagates_unrelated_integrity_error(self):
        with (
            patch(
                "apps.authentication.services.AccessRequest.objects.create",
                side_effect=IntegrityError("Unrelated database constraint"),
            ),
            self.assertRaises(IntegrityError),
        ):
            self.service.create(
                first_name="Alice",
                last_name="Martin",
                email="alice@example.com",
                reason="Requesting access",
            )

    def test_create_allows_new_request_after_invitation_revocation(self):
        first_request = self.create_access_request()
        _, invitation, _ = self.service.approve(first_request)

        InvitationService().revoke(invitation)

        second_request = self.service.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="Second request.",
        )

        self.assertEqual(
            second_request.status,
            AccessRequest.Status.PENDING,
        )
        self.assertEqual(AccessRequest.objects.count(), 2)

    def test_create_rejects_existing_user_email(self):
        User = get_user_model()
        User.objects.create_user(
            username="existing_user",
            email="alice@example.com",
            password="test-password-123",
        )

        with self.assertRaises(AccountAlreadyExistsError):
            self.service.create(
                first_name="Alice",
                last_name="Martin",
                email="ALICE@example.com",
                reason="Requesting access.",
            )

        self.assertEqual(AccessRequest.objects.count(), 0)
