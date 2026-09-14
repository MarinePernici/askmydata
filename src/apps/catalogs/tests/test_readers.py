from django.test import TestCase

from apps.catalogs.exceptions import CatalogNotReadyError
from apps.catalogs.models import (
    KnowledgeCatalog as KnowledgeCatalogModel,
    SchemaSnapshot,
)
from apps.catalogs.readers import CatalogReader
from apps.projects.tests.factories import create_test_project

from catalog.snapshot_serializer import CatalogSnapshotSerializer
from catalog.types import (
    KnowledgeCatalog,
    SemanticMetadata,
    TableMetadata,
)
from connectors.types import ColumnMetadata


class CatalogReaderTests(TestCase):
    def test_get_current_returns_current_catalog_snapshot(self):
        project = create_test_project(
            name="Test project",
        )

        domain_catalog = KnowledgeCatalog(
            tables=(
                TableMetadata(
                    schema="sales",
                    name="orders",
                    columns=(
                        ColumnMetadata(
                            name="id",
                            data_type="integer",
                            nullable=False,
                            default=None,
                        ),
                    ),
                    relationships=(),
                    semantic_metadata=SemanticMetadata(
                        description="Customer orders",
                        business_synonyms=(
                            "sales orders",
                            "purchases",
                        ),
                    ),
                ),
            )
        )

        catalog = KnowledgeCatalogModel.objects.create(
            project=project,
            status=KnowledgeCatalogModel.Status.READY,
            version=2,
        )

        SchemaSnapshot.objects.create(
            catalog=catalog,
            version=1,
            schema_data={"tables": []},
        )

        SchemaSnapshot.objects.create(
            catalog=catalog,
            version=2,
            schema_data=CatalogSnapshotSerializer().serialize(domain_catalog),
        )

        result = CatalogReader().get_current(
            project=project,
        )

        self.assertEqual(
            result,
            domain_catalog,
        )

    def test_get_current_raises_when_project_has_no_catalog(self):
        project = create_test_project(
            name="Test project",
        )

        reader = CatalogReader()

        with self.assertRaises(CatalogNotReadyError):
            reader.get_current(
                project=project,
            )

    def test_get_current_raises_when_catalog_is_not_ready(self):
        project = create_test_project(
            name="Test project",
        )

        KnowledgeCatalogModel.objects.create(
            project=project,
            status=KnowledgeCatalogModel.Status.BUILDING,
            version=1,
        )

        reader = CatalogReader()

        with self.assertRaises(CatalogNotReadyError):
            reader.get_current(
                project=project,
            )

    def test_get_current_raises_when_current_snapshot_does_not_exist(self):
        project = create_test_project(
            name="Test project",
        )

        catalog = KnowledgeCatalogModel.objects.create(
            project=project,
            status=KnowledgeCatalogModel.Status.READY,
            version=2,
        )

        SchemaSnapshot.objects.create(
            catalog=catalog,
            version=1,
            schema_data={"tables": []},
        )

        reader = CatalogReader()

        with self.assertRaises(CatalogNotReadyError):
            reader.get_current(
                project=project,
            )

    def test_get_current_rejects_stale_catalog(self):
        project = create_test_project(
            name="Test project",
        )

        knowledge_catalog = KnowledgeCatalogModel.objects.create(
            project=project,
            status=KnowledgeCatalogModel.Status.STALE,
            version=1,
        )

        SchemaSnapshot.objects.create(
            catalog=knowledge_catalog,
            version=1,
            schema_data={"tables": []},
        )

        reader = CatalogReader()

        with self.assertRaises(CatalogNotReadyError):
            reader.get_current(project)
