import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone

from apps.catalogs.exceptions import (
    CatalogScopeNotConfiguredError,
    DataSourceNotConfiguredError,
)
from apps.catalogs.models import (
    KnowledgeCatalog as KnowledgeCatalogModel,
)
from apps.catalogs.models import (
    SchemaSnapshot,
)
from apps.projects.models import Project
from apps.projects.services import ProjectService
from catalog.builder import CatalogBuilder
from catalog.semantic_enricher import SemanticEnricher
from catalog.snapshot_serializer import CatalogSnapshotSerializer
from catalog.types import KnowledgeCatalog as DomainKnowledgeCatalog
from connectors.postgresql import PostgreSQLConnector

logger = logging.getLogger(__name__)


class CatalogService:
    def __init__(
        self,
        connector_class=PostgreSQLConnector,
        semantic_enricher: SemanticEnricher | None = None,
        project_service: ProjectService | None = None,
    ) -> None:
        self._connector_class = connector_class
        self._semantic_enricher = semantic_enricher
        self._project_service = project_service or ProjectService()

    def build_for_project(
        self,
        project: Project,
    ) -> DomainKnowledgeCatalog:
        try:
            data_source = project.data_source
        except ObjectDoesNotExist as exc:
            raise DataSourceNotConfiguredError("Project has no data source.") from exc

        try:
            scope = project.catalog_scope
        except ObjectDoesNotExist as exc:
            raise CatalogScopeNotConfiguredError(
                "Project has no catalog scope."
            ) from exc

        config = data_source.to_connection_config()
        domain_scope = scope.to_domain()

        connector = self._connector_class(config)
        builder = CatalogBuilder(connector)

        knowledge_catalog, _ = KnowledgeCatalogModel.objects.get_or_create(
            project=project,
        )

        previous_status = knowledge_catalog.status

        is_rebuild_from_stale = previous_status == KnowledgeCatalogModel.Status.STALE

        if knowledge_catalog.version == 0 or is_rebuild_from_stale:
            self._project_service.mark_building_catalog(project)
        else:
            self._project_service.mark_regenerating_catalog(project)

        knowledge_catalog.status = KnowledgeCatalogModel.Status.BUILDING
        knowledge_catalog.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        try:
            catalog = builder.build(
                scope=domain_scope,
            )

            if self._semantic_enricher is not None:
                catalog = self._semantic_enricher.enrich_catalog(catalog)

        except Exception:
            if knowledge_catalog.version == 0 or is_rebuild_from_stale:
                knowledge_catalog.status = (
                    KnowledgeCatalogModel.Status.STALE
                    if is_rebuild_from_stale
                    else KnowledgeCatalogModel.Status.FAILED
                )
                knowledge_catalog.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

                self._project_service.mark_configuring(project)

            else:
                knowledge_catalog.status = KnowledgeCatalogModel.Status.READY
                knowledge_catalog.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

                self._project_service.mark_ready(project)

            raise

        serializer = CatalogSnapshotSerializer()
        schema_data = serializer.serialize(catalog)

        with transaction.atomic():
            next_version = knowledge_catalog.version + 1

            SchemaSnapshot.objects.create(
                catalog=knowledge_catalog,
                version=next_version,
                schema_data=schema_data,
            )

            knowledge_catalog.version = next_version
            knowledge_catalog.status = KnowledgeCatalogModel.Status.READY
            knowledge_catalog.last_regenerated_at = timezone.now()
            knowledge_catalog.save(
                update_fields=[
                    "version",
                    "status",
                    "last_regenerated_at",
                    "updated_at",
                ]
            )

        self._project_service.mark_ready(project)

        logger.info(
            "Catalog built successfully.",
            extra={
                "event": "catalog.built",
                "project_id": project.id,
                "catalog_version": knowledge_catalog.version,
            },
        )

        return catalog

    def mark_stale(
        self,
        project: Project,
    ) -> None:
        try:
            knowledge_catalog = project.knowledge_catalog
        except ObjectDoesNotExist:
            return

        knowledge_catalog.status = KnowledgeCatalogModel.Status.STALE
        knowledge_catalog.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )
