from django import forms


class ProjectForm(forms.Form):
    name = forms.CharField(max_length=255)
    description = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )
