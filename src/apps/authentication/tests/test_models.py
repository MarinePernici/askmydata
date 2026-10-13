from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.authentication.models import (
    AccessRequest,
    Invitation,
    UserPreferences,
)


class UserPreferencesModelTests(TestCase):
    def test_default_language_is_english(self):
        user = get_user_model().objects.create_user(
            username="testuser",
            password="test-password",
        )

        preferences = UserPreferences.objects.create(user=user)

        self.assertEqual(
            preferences.language,
            UserPreferences.Language.ENGLISH,
        )

    def test_language_can_be_french(self):
        user = get_user_model().objects.create_user(
            username="testuser",
            password="test-password",
        )

        preferences = UserPreferences.objects.create(
            user=user,
            language=UserPreferences.Language.FRENCH,
        )

        self.assertEqual(
            preferences.language,
            UserPreferences.Language.FRENCH,
        )

    def test_developer_mode_is_disabled_by_default(self):
        user = get_user_model().objects.create_user(
            username="testuser",
            password="test-password",
        )

        preferences = UserPreferences.objects.create(
            user=user,
        )

        self.assertFalse(preferences.developer_mode)

    def test_developer_mode_can_be_enabled(self):
        user = get_user_model().objects.create_user(
            username="testuser",
            password="test-password",
        )

        preferences = UserPreferences.objects.create(
            user=user,
            developer_mode=True,
        )

        preferences.refresh_from_db()

        self.assertTrue(preferences.developer_mode)


class InvitationModelTests(TestCase):
    def test_default_status_is_pending(self):
        invitation = Invitation.objects.create(
            email="invitee@example.com",
            token_hash="a" * 64,
            expires_at="2026-10-14T12:00:00Z",
        )

        self.assertEqual(
            invitation.status,
            Invitation.Status.PENDING,
        )

    def test_string_representation_contains_email_and_status(self):
        invitation = Invitation.objects.create(
            email="invitee@example.com",
            token_hash="b" * 64,
            expires_at="2026-10-14T12:00:00Z",
        )

        self.assertEqual(
            str(invitation),
            "invitee@example.com (pending)",
        )


class AccessRequestModelTests(TestCase):
    def test_default_status_is_pending(self):
        access_request = AccessRequest.objects.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="I would like to evaluate AskMyData.",
        )

        self.assertEqual(
            access_request.status,
            AccessRequest.Status.PENDING,
        )

    def test_invitation_is_optional(self):
        access_request = AccessRequest.objects.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="I would like to evaluate AskMyData.",
        )

        self.assertIsNone(access_request.invitation)

    def test_access_request_can_reference_invitation(self):
        invitation = Invitation.objects.create(
            email="alice@example.com",
            token_hash="c" * 64,
            expires_at="2026-10-14T12:00:00Z",
        )
        access_request = AccessRequest.objects.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="I would like to evaluate AskMyData.",
            invitation=invitation,
        )

        self.assertEqual(access_request.invitation, invitation)
        self.assertEqual(invitation.access_request, access_request)

    def test_string_representation_contains_name_and_email(self):
        access_request = AccessRequest.objects.create(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            reason="I would like to evaluate AskMyData.",
        )

        self.assertEqual(
            str(access_request),
            "Alice Martin <alice@example.com>",
        )
