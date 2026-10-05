import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.data_sources.encryption import CredentialCipher
from apps.data_sources.exceptions import DataSourceConfigurationError
from apps.projects.models import Project
from connectors.postgresql import PostgreSQLConnectionConfig


class DataSource(models.Model):
    class SourceType(models.TextChoices):
        POSTGRESQL = "postgresql", "PostgreSQL"

    class ConnectionStatus(models.TextChoices):
        NOT_TESTED = "not_tested", _("Not tested")
        CONNECTED = "connected", _("Connected")
        FAILED = "failed", _("Failed")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="data_source",
    )

    source_type = models.CharField(
        max_length=32,
        choices=SourceType.choices,
        default=SourceType.POSTGRESQL,
    )

    connection_status = models.CharField(
        max_length=32,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.NOT_TESTED,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_connection_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    host = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    port = models.PositiveIntegerField(
        default=5432,
    )

    database = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    username = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    encrypted_password = models.TextField(
        null=True,
        blank=True,
    )

    def set_password(self, password: str) -> None:
        cipher = CredentialCipher(settings.DATASOURCE_ENCRYPTION_KEY)
        self.encrypted_password = cipher.encrypt(password)

    def get_password(self) -> str:
        cipher = CredentialCipher(settings.DATASOURCE_ENCRYPTION_KEY)
        return cipher.decrypt(self.encrypted_password)

    def is_configured(self) -> bool:
        return all(
            [
                self.host,
                self.port,
                self.database,
                self.username,
                self.encrypted_password,
            ]
        )

    def to_connection_config(self) -> PostgreSQLConnectionConfig:
        if not self.is_configured():
            raise DataSourceConfigurationError("Data source is not fully configured.")

        return PostgreSQLConnectionConfig(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.username,
            password=self.get_password(),
        )
