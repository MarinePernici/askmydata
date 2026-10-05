from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import translation
from django.views.decorators.http import require_POST

from .forms import UserPreferencesForm
from .models import UserPreferences


@login_required
def dashboard(request):
    return HttpResponse("Dashboard")


@require_POST
def set_interface_language(request):
    language = request.POST.get("language")

    available_languages = {code for code, _ in settings.LANGUAGES}
    if language not in available_languages:
        language = settings.LANGUAGE_CODE

    if request.user.is_authenticated:
        preferences, _ = UserPreferences.objects.get_or_create(
            user=request.user,
        )
        preferences.language = language
        preferences.save(update_fields=["language"])

    translation.activate(language)

    response = redirect(request.POST.get("next") or "/")
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=settings.LANGUAGE_COOKIE_SECURE,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )
    return response


@login_required
def user_preferences(request):
    preferences, _ = UserPreferences.objects.get_or_create(
        user=request.user,
    )

    if request.method == "POST":
        form = UserPreferencesForm(request.POST)

        if form.is_valid():
            preferences.language = form.cleaned_data["language"]
            preferences.save(update_fields=["language"])

            translation.activate(preferences.language)
            request.LANGUAGE_CODE = preferences.language

            response = redirect("user-preferences")
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                preferences.language,
                max_age=settings.LANGUAGE_COOKIE_AGE,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
            )
            return response
    else:
        form = UserPreferencesForm(
            initial={"language": preferences.language},
        )

    return render(
        request,
        "authentication/user_preferences.html",
        {
            "form": form,
        },
    )
