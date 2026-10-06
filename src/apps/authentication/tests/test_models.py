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
