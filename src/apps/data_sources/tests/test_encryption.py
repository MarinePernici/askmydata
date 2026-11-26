from cryptography.fernet import Fernet, InvalidToken
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

    def test_decrypt_rejects_different_key(self):
        encrypted = self.cipher.encrypt("secret-password")
        other_cipher = CredentialCipher(Fernet.generate_key().decode())

        with self.assertRaises(InvalidToken):
            other_cipher.decrypt(encrypted)

    def test_decrypt_rejects_invalid_ciphertext(self):
        with self.assertRaises(InvalidToken):
            self.cipher.decrypt("invalid-ciphertext")
