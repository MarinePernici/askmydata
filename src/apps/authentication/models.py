import uuid

from django.conf import settings
from django.db import models
from django.db.models.functions import Lower


class UserPreferences(models.Model):
    class Language(models.TextChoices):
        ENGLISH = "en", "English"
        FRENCH = "fr", "Français"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    language = models.CharField(
        max_length=2,
        choices=Language.choices,
        default=Language.ENGLISH,
    )
    developer_mode = models.BooleanField(
        default=False,
    )

    def __str__(self) -> str:
        return f"{self.user} preferences"


class Invitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        EXPIRED = "expired", "Expired"
        REVOKED = "revoked", "Revoked"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    email = models.EmailField()

    token_hash = models.CharField(
        max_length=64,
        unique=True,
    )

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.email} ({self.status})"


class AccessRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    first_name = models.CharField(max_length=150)

    last_name = models.CharField(max_length=150)

    email = models.EmailField()

    reason = models.TextField()

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    invitation = models.OneToOneField(
        Invitation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_request",
    )

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                Lower("email"),
                condition=models.Q(status="pending"),
                name="unique_pending_access_request_email",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} <{self.email}>"
