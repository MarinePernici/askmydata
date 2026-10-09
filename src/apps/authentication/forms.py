from typing import ClassVar

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import AccessRequest, UserPreferences


class UserPreferencesForm(forms.Form):
    language = forms.ChoiceField(
        choices=UserPreferences.Language.choices,
    )
    developer_mode = forms.BooleanField(
        required=False,
    )


class AccessRequestForm(forms.ModelForm):
    class Meta:
        model = AccessRequest
        fields: ClassVar[list[str]] = [
            "first_name",
            "last_name",
            "email",
            "reason",
        ]

        labels: ClassVar[dict[str, str]] = {
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "email": _("Email"),
            "reason": _("Why would you like access?"),
        }

        widgets: ClassVar[dict[str, forms.Widget]] = {
            "reason": forms.Textarea(attrs={"rows": 5}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if AccessRequest.objects.filter(
            email__iexact=email,
            status=AccessRequest.Status.PENDING,
        ).exists():
            raise forms.ValidationError(
                _("An access request is already pending for this email.")
            )

        return email


class InvitationRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)
