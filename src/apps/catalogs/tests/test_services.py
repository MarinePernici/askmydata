from dataclasses import replace
from django.test import TestCase

from apps.catalogs.exceptions import (
    CatalogScopeNotConfiguredError,
    DataSourceNotConfiguredError,
)
from apps.catalogs.models import CatalogScope, KnowledgeCatalog, SchemaSnapshot
from apps.catalogs.services import CatalogService
from apps.data_sources.exceptions import DataSourceConfigurationError
from apps.data_sources.models import DataSource
from apps.projects.models import Project
from catalog.exceptions import SemanticEnrichmentError
from catalog.types import SemanticMetadata
from connectors.types import ColumnMetadata


class FakeConnector:
    def __init__(self, config):
        self.config = config

    def discover_columns(self, schema, table):
        return [
            ColumnMetadata(
                name="id",
                data_type="bigint",
                nullable=False,
                default=None,
            )
        ]

    def discover_relationships(self, schema, table):
        return []


class FailingConnector:
    def __init__(self, config):
        self.config = config

    def discover_columns(self, schema, table):
        raise RuntimeError("Schema discovery failed")

    def discover_relationships(self, schema, table):
        return []


class CatalogStatusCheckingConnector:
    project = None

    def __init__(self, config):
        self.config = config

    def discover_columns(self, schema, table):
        catalog = KnowledgeCatalog.objects.get(
            project=self.project,
        )

        if catalog.status != KnowledgeCatalog.Status.BUILDING:
            raise AssertionError(
                f"Expected catalog to be BUILDING, got {catalog.status}"
            )

        return []

    def discover_relationships(self, schema, table):
        return []


class FakeSemanticEnricher:
    def enrich_catalog(self, catalog):
        return type(catalog)(
            tables=tuple(
                replace(
                    table,
                    semantic_metadata=SemanticMetadata(
                        description=f"Description for {table.name}",
                        business_synonyms=(table.name,),
                    ),
                )
                for table in catalog.tables
            )
        )


class FailingSemanticEnricher:
    def enrich_catalog(self, catalog):
        raise SemanticEnrichmentError(
            "Semantic enrichment failed."
        )


class CatalogServiceTests(TestCase):
    def test_build_for_project_uses_project_catalog_scope(self):
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {
                    "schema": "sales",
                    "table": "orders",
                }
            ],
        )

        service = CatalogService(
            connector_class=FakeConnector,
        )

        catalog = service.build_for_project(project)

        self.assertEqual(len(catalog.tables), 1)
        self.assertEqual(
            catalog.tables[0].schema,
            "sales",
        )
        self.assertEqual(
            catalog.tables[0].name,
            "orders",
        )

    def test_build_for_project_fails_when_data_source_is_missing(self):
        project = Project.objects.create(
            name="Test project",
        )

        service = CatalogService(
            connector_class=FakeConnector,
        )

        with self.assertRaises(DataSourceNotConfiguredError):
            service.build_for_project(project)

    def test_build_for_project_fails_when_catalog_scope_is_missing(self):
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        service = CatalogService(
            connector_class=FakeConnector,
        )

        with self.assertRaises(CatalogScopeNotConfiguredError):
            service.build_for_project(project)

    def test_build_for_project_fails_when_data_source_is_incomplete(self):
        project = Project.objects.create(
            name="Test project",
        )

        DataSource.objects.create(
            project=project,
        )

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {
                    "schema": "sales",
                    "table": "orders",
                }
            ],
        )

        service = CatalogService(
            connector_class=FakeConnector,
        )

        with self.assertRaises(DataSourceConfigurationError):
            service.build_for_project(project)

    def test_build_for_project_persists_new_schema_snapshot(self):
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {
                    "schema": "sales",
                    "table": "orders",
                }
            ],
        )

        knowledge_catalog = KnowledgeCatalog.objects.create(
            project=project,
        )

        service = CatalogService(
            connector_class=FakeConnector,
        )

        service.build_for_project(project)

        knowledge_catalog.refresh_from_db()

        self.assertEqual(
            knowledge_catalog.version,
            1,
        )
        self.assertEqual(
            knowledge_catalog.status,
            KnowledgeCatalog.Status.READY,
        )

        snapshot = SchemaSnapshot.objects.get(
            catalog=knowledge_catalog,
            version=1,
        )

        self.assertEqual(
            snapshot.schema_data["tables"][0]["schema"],
            "sales",
        )
        self.assertEqual(
            snapshot.schema_data["tables"][0]["name"],
            "orders",
        )

    def test_build_for_project_does_not_persist_snapshot_when_build_fails(self):
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {
                    "schema": "sales",
                    "table": "orders",
                }
            ],
        )

        knowledge_catalog = KnowledgeCatalog.objects.create(
            project=project,
            version=1,
            status=KnowledgeCatalog.Status.READY,
        )

        SchemaSnapshot.objects.create(
            catalog=knowledge_catalog,
            version=1,
            schema_data={"tables": []},
        )

        service = CatalogService(
            connector_class=FailingConnector,
        )

        with self.assertRaises(RuntimeError):
            service.build_for_project(project)

        knowledge_catalog.refresh_from_db()

        self.assertEqual(
            knowledge_catalog.version,
            1,
        )
        self.assertEqual(
            knowledge_catalog.status,
            KnowledgeCatalog.Status.READY,
        )
        self.assertEqual(
            knowledge_catalog.snapshots.count(),
            1,
        )

    def test_first_build_failure_marks_catalog_as_failed(self):
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {
                    "schema": "sales",
                    "table": "orders",
                }
            ],
        )

        service = CatalogService(
            connector_class=FailingConnector,
        )

        with self.assertRaises(RuntimeError):
            service.build_for_project(project)

        knowledge_catalog = KnowledgeCatalog.objects.get(
            project=project,
        )

        self.assertEqual(
            knowledge_catalog.status,
            KnowledgeCatalog.Status.FAILED,
        )
        self.assertEqual(
            knowledge_catalog.version,
            0,
        )
        self.assertEqual(
            knowledge_catalog.snapshots.count(),
            0,
        )

    def test_catalog_is_building_while_catalog_is_generated(self):
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {
                    "schema": "sales",
                    "table": "orders",
                }
            ],
        )

        CatalogStatusCheckingConnector.project = project

        service = CatalogService(
            connector_class=CatalogStatusCheckingConnector,
        )

        service.build_for_project(project)

        knowledge_catalog = KnowledgeCatalog.objects.get(
            project=project,
        )

        self.assertEqual(
            knowledge_catalog.status,
            KnowledgeCatalog.Status.READY,
        )
        self.assertEqual(
            knowledge_catalog.version,
            1,
        )

    def test_successful_regeneration_creates_new_snapshot_version(self):
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {
                    "schema": "sales",
                    "table": "orders",
                }
            ],
        )

        knowledge_catalog = KnowledgeCatalog.objects.create(
            project=project,
            version=1,
            status=KnowledgeCatalog.Status.READY,
        )

        SchemaSnapshot.objects.create(
            catalog=knowledge_catalog,
            version=1,
            schema_data={
                "tables": [],
            },
        )

        service = CatalogService(
            connector_class=FakeConnector,
        )

        service.build_for_project(project)

        knowledge_catalog.refresh_from_db()

        self.assertEqual(
            knowledge_catalog.version,
            2,
        )
        self.assertEqual(
            knowledge_catalog.status,
            KnowledgeCatalog.Status.READY,
        )

        self.assertEqual(
            list(
                knowledge_catalog.snapshots
                .order_by("version")
                .values_list("version", flat=True)
            ),
            [1, 2],
        )

    def test_build_for_project_persists_semantically_enriched_catalog(self):
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {
                    "schema": "sales",
                    "table": "orders",
                }
            ],
        )

        service = CatalogService(
            connector_class=FakeConnector,
            semantic_enricher=FakeSemanticEnricher(),
        )

        service.build_for_project(project)

        knowledge_catalog = KnowledgeCatalog.objects.get(
            project=project,
        )

        snapshot = knowledge_catalog.snapshots.get(
            version=1,
        )

        table_data = snapshot.schema_data["tables"][0]

        self.assertEqual(
            table_data["semantic_metadata"]["description"],
            "Description for orders",
        )

    def test_build_for_project_marks_catalog_failed_when_semantic_enrichment_fails(self):
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {
                    "schema": "sales",
                    "table": "orders",
                }
            ],
        )

        service = CatalogService(
            connector_class=FakeConnector,
            semantic_enricher=FailingSemanticEnricher(),
        )

        with self.assertRaises(SemanticEnrichmentError):
            service.build_for_project(project)

        knowledge_catalog = KnowledgeCatalog.objects.get(
            project=project,
        )

        self.assertEqual(
            knowledge_catalog.status,
            KnowledgeCatalog.Status.FAILED,
        )
        self.assertEqual(
            knowledge_catalog.version,
            0,
        )
        self.assertEqual(
            knowledge_catalog.snapshots.count(),
            0,
        )

    def test_regeneration_preserves_previous_catalog_when_semantic_enrichment_fails(self):
        project = Project.objects.create(
            name="Test project",
        )

        data_source = DataSource(
            project=project,
            host="localhost",
            port=5432,
            database="example",
            username="readonly",
        )
        data_source.set_password("secret-password")
        data_source.save()

        CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {
                    "schema": "sales",
                    "table": "orders",
                }
            ],
        )

        successful_service = CatalogService(
            connector_class=FakeConnector,
            semantic_enricher=FakeSemanticEnricher(),
        )

        successful_service.build_for_project(project)

        failing_service = CatalogService(
            connector_class=FakeConnector,
            semantic_enricher=FailingSemanticEnricher(),
        )

        with self.assertRaises(SemanticEnrichmentError):
            failing_service.build_for_project(project)

        knowledge_catalog = KnowledgeCatalog.objects.get(
            project=project,
        )

        self.assertEqual(
            knowledge_catalog.status,
            KnowledgeCatalog.Status.READY,
        )
        self.assertEqual(
            knowledge_catalog.version,
            1,
        )
        self.assertEqual(
            knowledge_catalog.snapshots.count(),
            1,
        )
        self.assertTrue(
            knowledge_catalog.snapshots.filter(
                version=1,
            ).exists()
        )
        self.assertFalse(
            knowledge_catalog.snapshots.filter(
                version=2,
            ).exists()
        )
