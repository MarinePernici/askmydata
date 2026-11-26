import os
import subprocess
import sys
from pathlib import Path

from cryptography.fernet import Fernet
from django.test import SimpleTestCase


class EncryptionSettingsTests(SimpleTestCase):
    def run_django_check(self, encryption_key: str):
        env = os.environ.copy()
        env["DATASOURCE_ENCRYPTION_KEY"] = encryption_key

        manage_py = Path(__file__).resolve().parents[2] / "manage.py"

        return subprocess.run(
            [sys.executable, str(manage_py), "check"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def test_valid_encryption_key_allows_startup(self):
        result = self.run_django_check(Fernet.generate_key().decode())

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_encryption_key_prevents_startup(self):
        result = self.run_django_check("invalid-key")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "ImproperlyConfigured: DATASOURCE_ENCRYPTION_KEY "
            "must be a valid Fernet key.",
            result.stderr,
        )

    def test_empty_encryption_key_prevents_startup(self):
        result = self.run_django_check("")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "ImproperlyConfigured: DATASOURCE_ENCRYPTION_KEY "
            "must be a valid Fernet key.",
            result.stderr,
        )
