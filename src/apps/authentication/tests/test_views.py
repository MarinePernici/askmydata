from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.authentication.models import UserPreferences


class LoginViewTests(TestCase):
    def test_user_can_log_in_with_valid_credentials(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "marine",
                "password": "test-password",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertRedirects(
            response,
            reverse("project-list"),
            fetch_redirect_response=False,
        )

        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            user.id,
        )

    def test_login_redirects_to_requested_page_when_next_is_provided(self):
        get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        next_url = reverse("project-list")

        response = self.client.post(
            f"{reverse('login')}?next={next_url}",
            {
                "username": "marine",
                "password": "test-password",
                "next": next_url,
            },
        )

        self.assertRedirects(
            response,
            next_url,
            fetch_redirect_response=False,
        )

    def test_user_cannot_log_in_with_invalid_credentials(self):
        get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "marine",
                "password": "wrong-password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_user_can_log_out(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse("logout"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertRedirects(
            response,
            reverse("login"),
            fetch_redirect_response=False,
        )

    def test_login_page_displays_askmydata_sign_in_form(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AskMyData")
        self.assertContains(response, "Welcome back")
        self.assertContains(response, "Username")
        self.assertContains(response, "Password")
        self.assertContains(response, "Log in")


class LanguageViewTests(TestCase):
    def test_authenticated_user_can_switch_to_french(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("set-interface-language"),
            {
                "language": "fr",
                "next": reverse("project-list"),
            },
        )

        self.assertRedirects(
            response,
            reverse("project-list"),
            fetch_redirect_response=False,
        )

        preferences = UserPreferences.objects.get(user=user)
        self.assertEqual(preferences.language, UserPreferences.Language.FRENCH)

    def test_authenticated_user_can_switch_back_to_english(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        UserPreferences.objects.create(
            user=user,
            language=UserPreferences.Language.FRENCH,
        )
        self.client.force_login(user)

        self.client.post(
            reverse("set-interface-language"),
            {
                "language": "en",
                "next": reverse("project-list"),
            },
        )

        user.preferences.refresh_from_db()
        self.assertEqual(
            user.preferences.language,
            UserPreferences.Language.ENGLISH,
        )

    def test_authenticated_user_preference_is_applied_to_request(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        UserPreferences.objects.create(
            user=user,
            language=UserPreferences.Language.FRENCH,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("project-list"))

        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, "fr")

    def test_authenticated_user_can_access_preferences_page(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("user-preferences"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User preferences")
        self.assertContains(response, "English")

    def test_anonymous_user_cannot_access_preferences_page(self):
        response = self.client.get(reverse("user-preferences"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('user-preferences')}",
        )

    def test_preferences_page_updates_language(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("user-preferences"),
            {"language": "fr"},
        )

        self.assertRedirects(
            response,
            reverse("user-preferences"),
            fetch_redirect_response=False,
        )

        preferences = UserPreferences.objects.get(user=user)
        self.assertEqual(
            preferences.language,
            UserPreferences.Language.FRENCH,
        )

    def test_login_page_is_translated_to_french(self):
        response = self.client.post(
            reverse("set_language"),
            {
                "language": "fr",
                "next": reverse("login"),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bon retour parmi nous")
        self.assertContains(response, "Nom d’utilisateur")
        self.assertContains(response, "Mot de passe")
        self.assertContains(response, "Se connecter")

    def test_preferences_page_displays_developer_mode_field(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("user-preferences"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("developer_mode", response.context["form"].fields)
        self.assertFalse(response.context["form"]["developer_mode"].value())

    def test_preferences_page_enables_developer_mode(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("user-preferences"),
            {
                "language": "en",
                "developer_mode": "on",
            },
        )

        self.assertRedirects(
            response,
            reverse("user-preferences"),
            fetch_redirect_response=False,
        )

        preferences = UserPreferences.objects.get(user=user)
        self.assertTrue(preferences.developer_mode)

    def test_preferences_page_disables_developer_mode(self):
        user = get_user_model().objects.create_user(
            username="marine",
            password="test-password",
        )
        UserPreferences.objects.create(
            user=user,
            developer_mode=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("user-preferences"),
            {
                "language": "en",
            },
        )

        self.assertRedirects(
            response,
            reverse("user-preferences"),
            fetch_redirect_response=False,
        )

        user.preferences.refresh_from_db()
        self.assertFalse(user.preferences.developer_mode)
