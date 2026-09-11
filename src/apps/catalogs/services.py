from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone

from apps.catalogs.exceptions import (
    CatalogScopeNotConfiguredError,
    DataSourceNotConfiguredError,
)
from apps.catalogs.models import (
    KnowledgeCatalog as KnowledgeCatalogModel,
    SchemaSnapshot,
)
from apps.projects.models import Project
from catalog.builder import CatalogBuilder
from catalog.semantic_enricher import SemanticEnricher
from catalog.snapshot_serializer import CatalogSnapshotSerializer
from catalog.types import KnowledgeCatalog as DomainKnowledgeCatalog
from connectors.postgresql import PostgreSQLConnector


class CatalogService:
    def __init__(
        self,
        connector_class=PostgreSQLConnector,
        semantic_enricher: SemanticEnricher | None = None,
    ) -> None:
        self._connector_class = connector_class
        self._semantic_enricher = semantic_enricher

    def build_for_project(
        self,
        project: Project,
    ) -> DomainKnowledgeCatalog:
        try:
            data_source = project.data_source
        except ObjectDoesNotExist as exc:
            raise DataSourceNotConfiguredError(
                "Project has no data source."
            ) from exc

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
            if knowledge_catalog.version == 0:
                knowledge_catalog.status = KnowledgeCatalogModel.Status.FAILED
                knowledge_catalog.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )
            else:
                knowledge_catalog.status = KnowledgeCatalogModel.Status.READY
                knowledge_catalog.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )
            raise

        if self._semantic_enricher is not None:
            catalog = self._semantic_enricher.enrich_catalog(catalog)

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

        return catalog
    