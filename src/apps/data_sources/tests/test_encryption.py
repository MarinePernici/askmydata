from cryptography.fernet import Fernet
from django.test import SimpleTestCase

from apps.data_sources.encryption import CredentialCipher


class CredentialCipherTests(SimpleTestCase):
    def setUp(self):
        key = Fernet.generate_key().decode()
        self.cipher = CredentialCipher(key)

    def test_encrypt_does_not_return_plain_text(self):
        encrypted = self.cipher.encrypt("secret-password")

        self.assertNotEqual(
            encrypted,
            "secret-password",
        )

    def test_decrypt_restores_original_value(self):
        encrypted = self.cipher.encrypt("secret-password")

        decrypted = self.cipher.decrypt(encrypted)

        self.assertEqual(
            decrypted,
            "secret-password",
        )
