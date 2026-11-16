from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from config.demo_datasets import DEMO_DATASETS, get_demo_dataset_connection


@override_settings(DEMO_DB_HOST="demo-db", DEMO_DB_PORT=5432)
class DemoDatasetConnectionTests(SimpleTestCase):
    def test_four_datasets_are_available(self):
        self.assertEqual(
            set(DEMO_DATASETS),
            {"eeg", "pagila", "olist", "badminton"},
        )

    def test_unknown_dataset_is_rejected(self):
        with self.assertRaises(ValueError):
            get_demo_dataset_connection("unknown")

    @patch.dict("os.environ", {"DEMO_EEG_PASSWORD": "test-secret"})
    def test_connection_uses_server_configuration(self):
        connection = get_demo_dataset_connection("eeg")

        self.assertEqual(
            connection,
            {
                "host": "demo-db",
                "port": 5432,
                "database": "askmydata_eeg_public_demo",
                "username": "eeg_demo_readonly",
                "password": "test-secret",
            },
        )

    @patch.dict("os.environ", {"DEMO_EEG_PASSWORD": ""})
    def test_missing_password_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            get_demo_dataset_connection("eeg")
