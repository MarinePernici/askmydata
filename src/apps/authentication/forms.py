from django import forms

from .models import UserPreferences


class UserPreferencesForm(forms.Form):
    language = forms.ChoiceField(
        choices=UserPreferences.Language.choices,
    )
