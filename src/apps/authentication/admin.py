from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils import timezone

from apps.authentication.exceptions import (
    AccountAlreadyExistsError,
    ActiveInvitationExistsError,
    InvalidAccessRequestError,
    InvalidInvitationError,
    PendingAccessRequestExistsError,
)
from apps.authentication.forms_admin import InvitationAdminForm
from apps.authentication.models import AccessRequest, Invitation
from apps.authentication.services import (
    AccessRequestService,
    InvitationService,
)


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "status",
        "created_at",
        "reviewed_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("created_at", "reviewed_at", "invitation")

    change_form_template = "admin/authentication/accessrequest/change_form.html"

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        context["show_approve_button"] = (
            obj is not None
            and obj.status == AccessRequest.Status.PENDING
            and request.user.is_superuser
        )
        return super().render_change_form(request, context, add, change, form_url, obj)

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/approve/",
                self.admin_site.admin_view(self.approve_view),
                name="authentication_accessrequest_approve",
            ),
            path(
                "<path:object_id>/reject/",
                self.admin_site.admin_view(self.reject_view),
                name="authentication_accessrequest_reject",
            ),
        ]
        return custom_urls + super().get_urls()

    def approve_view(self, request, object_id):
        if not request.user.is_active or not request.user.is_superuser:
            raise PermissionDenied

        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

        access_request = self.get_object(request, object_id)

        if access_request is None:
            raise PermissionDenied

        try:
            access_request, invitation, raw_token = AccessRequestService().approve(
                access_request
            )
        except (
            InvalidAccessRequestError,
            AccountAlreadyExistsError,
            ActiveInvitationExistsError,
            PendingAccessRequestExistsError,
        ) as exc:
            self.message_user(
                request,
                str(exc),
                level="error",
            )
            return redirect("admin:authentication_accessrequest_changelist")

        registration_url = request.build_absolute_uri(
            reverse("invitation-register", kwargs={"token": raw_token})
        )

        context = {
            **self.admin_site.each_context(request),
            "title": "Invitation created",
            "access_request": access_request,
            "invitation": invitation,
            "registration_url": registration_url,
        }

        response = render(
            request,
            "admin/authentication/accessrequest/invitation_created.html",
            context,
        )
        response["Cache-Control"] = "no-store"
        return response

    def reject_view(self, request, object_id):
        if not request.user.is_active or not request.user.is_superuser:
            raise PermissionDenied

        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

        access_request = self.get_object(request, object_id)

        if access_request is None:
            raise PermissionDenied

        try:
            AccessRequestService().reject(access_request)
        except InvalidAccessRequestError as exc:
            self.message_user(request, str(exc), level="error")
        else:
            self.message_user(
                request,
                "Access request rejected successfully.",
                level="success",
            )

        return redirect("admin:authentication_accessrequest_changelist")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "status",
        "created_at",
        "expires_at",
        "accepted_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("email",)
    fields = (
        "email",
        "status",
        "expires_at",
        "created_at",
        "accepted_at",
        "revoked_at",
    )
    readonly_fields = (
        "created_at",
        "accepted_at",
        "revoked_at",
    )

    change_list_template = "admin/authentication/invitation/change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["create_invitation_url"] = reverse(
            "admin:authentication_invitation_create"
        )
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        custom_urls = [
            path(
                "create/",
                self.admin_site.admin_view(self.create_invitation_view),
                name="authentication_invitation_create",
            ),
            path(
                "<path:object_id>/revoke/",
                self.admin_site.admin_view(self.revoke_view),
                name="authentication_invitation_revoke",
            ),
        ]
        return custom_urls + super().get_urls()

    def create_invitation_view(self, request):
        if not request.user.is_active or not request.user.is_superuser:
            raise PermissionDenied

        form = InvitationAdminForm(request.POST or None)

        if request.method == "POST" and form.is_valid():
            try:
                invitation, raw_token = InvitationService().create(
                    form.cleaned_data["email"]
                )
            except (
                AccountAlreadyExistsError,
                ActiveInvitationExistsError,
                PendingAccessRequestExistsError,
            ) as exc:
                form.add_error("email", str(exc))
            else:
                registration_url = request.build_absolute_uri(
                    reverse("invitation-register", kwargs={"token": raw_token})
                )

                context = {
                    **self.admin_site.each_context(request),
                    "title": "Invitation created",
                    "invitation": invitation,
                    "registration_url": registration_url,
                }

                response = render(
                    request,
                    "admin/authentication/invitation/invitation_created.html",
                    context,
                )
                response["Cache-Control"] = "no-store"
                return response

        context = {
            **self.admin_site.each_context(request),
            "title": "Create invitation",
            "form": form,
        }

        return render(
            request,
            "admin/authentication/invitation/create.html",
            context,
        )

    def revoke_view(self, request, object_id):
        if not request.user.is_active or not request.user.is_superuser:
            raise PermissionDenied

        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

        invitation = self.get_object(request, object_id)

        if invitation is None:
            raise PermissionDenied

        try:
            InvitationService().revoke(invitation)
        except InvalidInvitationError as exc:
            self.message_user(request, str(exc), level="error")
        else:
            self.message_user(
                request,
                "Invitation revoked successfully.",
                level="success",
            )

        return redirect("admin:authentication_invitation_changelist")

    change_form_template = "admin/authentication/invitation/change_form.html"

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        context["show_revoke_button"] = (
            obj is not None
            and obj.status == Invitation.Status.PENDING
            and obj.expires_at > timezone.now()
            and request.user.is_superuser
        )
        return super().render_change_form(request, context, add, change, form_url, obj)

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser
