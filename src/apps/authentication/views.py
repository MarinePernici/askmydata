from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import translation
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .exceptions import (
    AccountAlreadyExistsError,
    ActiveInvitationExistsError,
    InvalidInvitationError,
    InvitationExpiredError,
    PendingAccessRequestExistsError,
)
from .forms import (
    AccessRequestForm,
    InvitationRegistrationForm,
    UserPreferencesForm,
)
from .models import UserPreferences
from .services import AccessRequestService, InvitationService


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
            preferences.developer_mode = form.cleaned_data["developer_mode"]
            preferences.save(
                update_fields=[
                    "language",
                    "developer_mode",
                ]
            )

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
            initial={
                "language": preferences.language,
                "developer_mode": preferences.developer_mode,
            },
        )

    return render(
        request,
        "authentication/user_preferences.html",
        {
            "form": form,
        },
    )


def request_access(request):
    if request.method == "POST":
        form = AccessRequestForm(request.POST)

        if form.is_valid():
            try:
                AccessRequestService().create(**form.cleaned_data)
            except PendingAccessRequestExistsError:
                form.add_error(
                    "email",
                    _("An access request is already pending for this email."),
                )
            except ActiveInvitationExistsError:
                form.add_error(
                    "email",
                    _("An active invitation already exists for this email."),
                )
            except AccountAlreadyExistsError:
                form.add_error(
                    "email",
                    _("An account already exists for this email."),
                )
            else:
                return redirect("access-request-success")
    else:
        form = AccessRequestForm()

    return render(
        request,
        "authentication/request_access.html",
        {"form": form},
    )


def access_request_success(request):
    return render(
        request,
        "authentication/access_request_success.html",
    )


def register_with_invitation(request, token):
    invitation_service = InvitationService()

    try:
        invitation_service.get_valid_by_token(token)
    except (InvalidInvitationError, InvitationExpiredError) as exc:
        raise Http404("Invitation not found or no longer valid.") from exc

    if request.method == "POST":
        form = InvitationRegistrationForm(request.POST)

        if form.is_valid():
            try:
                user = invitation_service.accept(
                    token,
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password1"],
                )
            except (InvalidInvitationError, InvitationExpiredError) as exc:
                raise Http404("Invitation not found or no longer valid.") from exc

            login(request, user)
            messages.success(request, _("Your account has been created."))
            return redirect("project-list")
    else:
        form = InvitationRegistrationForm()

    return render(
        request,
        "authentication/register.html",
        {"form": form},
    )
