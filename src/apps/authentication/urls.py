from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    access_request_success,
    register_with_invitation,
    request_access,
    set_interface_language,
    user_preferences,
)

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="login"),
        name="logout",
    ),
    path(
        "language/",
        set_interface_language,
        name="set-interface-language",
    ),
    path(
        "preferences/",
        user_preferences,
        name="user-preferences",
    ),
    path(
        "request-access/",
        request_access,
        name="request-access",
    ),
    path(
        "request-access/success/",
        access_request_success,
        name="access-request-success",
    ),
    path(
        "register/<str:token>/",
        register_with_invitation,
        name="invitation-register",
    ),
]
