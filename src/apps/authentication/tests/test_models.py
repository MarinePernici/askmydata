from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.authentication.models import UserPreferences


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
