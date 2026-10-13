from django import forms


class InvitationAdminForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        max_length=254,
    )
