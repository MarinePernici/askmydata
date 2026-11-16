from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


@dataclass(frozen=True)
class DemoDataset:
    key: str
    label: str
    description: str
    database: str
    username: str


DEMO_DATASETS = {
    "eeg": DemoDataset(
        key="eeg",
        label="EEG",
        description="Synthetic EEG research data",
        database="askmydata_eeg_public_demo",
        username="eeg_demo_readonly",
    ),
    "pagila": DemoDataset(
        key="pagila",
        label="Pagila",
        description="Film rental data",
        database="pagila",
        username="pagila_readonly",
    ),
    "olist": DemoDataset(
        key="olist",
        label="Olist",
        description="Brazilian e-commerce data",
        database="olist",
        username="olist_readonly",
    ),
    "badminton": DemoDataset(
        key="badminton",
        label="Badminton",
        description="International badminton match results",
        database="badminton",
        username="badminton_readonly",
    ),
}


def get_demo_dataset_connection(dataset_key: str) -> dict:
    """Resolve an allowed demo dataset to its server-side connection settings."""
    dataset = DEMO_DATASETS.get(dataset_key)

    if dataset is None:
        raise ValueError("Unknown demo dataset.")

    password_env_names = {
        "eeg": "DEMO_EEG_PASSWORD",
        "pagila": "DEMO_PAGILA_PASSWORD",
        "olist": "DEMO_OLIST_PASSWORD",
        "badminton": "DEMO_BADMINTON_PASSWORD",
    }

    import os

    password = os.environ.get(password_env_names[dataset_key])

    if not password:
        raise ImproperlyConfigured(
            f"Missing password configuration for demo dataset: {dataset_key}"
        )

    return {
        "host": settings.DEMO_DB_HOST,
        "port": settings.DEMO_DB_PORT,
        "database": dataset.database,
        "username": dataset.username,
        "password": password,
    }
