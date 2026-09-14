from django import forms


class DataSourceForm(forms.Form):
    host = forms.CharField(max_length=255)
    port = forms.IntegerField(
        min_value=1,
        max_value=65535,
        initial=5432,
    )
    database = forms.CharField(max_length=255)
    username = forms.CharField(max_length=255)
    password = forms.CharField(
        widget=forms.PasswordInput,
    )
