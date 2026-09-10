from cryptography.fernet import Fernet


class CredentialCipher:
    """Encrypt and decrypt external data source credentials."""

    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode())

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(
            value.encode()
        ).decode()

    def decrypt(self, value: str) -> str:
        return self._fernet.decrypt(
            value.encode()
        ).decode()