from django import forms

from config.demo_datasets import DEMO_DATASETS


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


class DemoDataSourceForm(forms.Form):
    dataset = forms.ChoiceField(
        choices=[
            (dataset.key, f"{dataset.label} — {dataset.description}")
            for dataset in DEMO_DATASETS.values()
        ],
    )
