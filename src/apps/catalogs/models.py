import uuid

from django.db import models

from catalog.types import (
    CatalogScope as DomainCatalogScope,
    CatalogTableSelection,
)
from apps.projects.models import Project


class CatalogScope(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="catalog_scope",
    )

    selected_tables = models.JSONField(
        default=list,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_domain(self) -> DomainCatalogScope:
        return DomainCatalogScope(
            tables=tuple(
                CatalogTableSelection(
                    schema=selection["schema"],
                    table=selection["table"],
                )
                for selection in self.selected_tables
            )
        )


class KnowledgeCatalog(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        BUILDING = "building", "Building"
        READY = "ready", "Ready"
        STALE = "stale", "Stale"
        FAILED = "failed", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="knowledge_catalog",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    version = models.PositiveIntegerField(
        default=0,
    )

    last_regenerated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )


class SchemaSnapshot(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    catalog = models.ForeignKey(
        KnowledgeCatalog,
        on_delete=models.CASCADE,
        related_name="snapshots",
    )

    version = models.PositiveIntegerField()

    schema_data = models.JSONField(
        default=dict,
    )

    captured_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["catalog", "version"],
                name="unique_catalog_snapshot_version",
            )
        ]
