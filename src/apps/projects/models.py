import uuid

from django.conf import settings
from django.db import models


class Project(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        CONFIGURING = "configuring", "Configuring"
        BUILDING_CATALOG = "building_catalog", "Building catalog"
        READY = "ready", "Ready"
        REGENERATING_CATALOG = "regenerating_catalog", "Regenerating catalog"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )

    def __str__(self) -> str:
        return self.name
