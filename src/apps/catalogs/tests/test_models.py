from django.db import IntegrityError
from django.test import TestCase

from apps.catalogs.models import CatalogScope, KnowledgeCatalog, SchemaSnapshot
from apps.projects.tests.factories import create_test_project


class CatalogScopeModelTests(TestCase):
    def test_catalog_scope_has_empty_selection_by_default(self):
        project = create_test_project(
            name="Test project",
        )

        scope = CatalogScope.objects.create(
            project=project,
        )

        self.assertEqual(
            scope.selected_tables,
            [],
        )

    def test_project_can_have_only_one_catalog_scope(self):
        project = create_test_project(
            name="Test project",
        )

        CatalogScope.objects.create(
            project=project,
        )

        with self.assertRaises(IntegrityError):
            CatalogScope.objects.create(
                project=project,
            )

    def test_catalog_scope_converts_selection_to_domain_scope(self):
        project = create_test_project(
            name="Test project",
        )

        scope = CatalogScope.objects.create(
            project=project,
            selected_tables=[
                {
                    "schema": "sales",
                    "table": "customers",
                },
                {
                    "schema": "sales",
                    "table": "orders",
                },
            ],
        )

        domain_scope = scope.to_domain()

        self.assertEqual(
            [(table.schema, table.table) for table in domain_scope.tables],
            [
                ("sales", "customers"),
                ("sales", "orders"),
            ],
        )

    def test_empty_catalog_scope_converts_to_empty_domain_scope(self):
        project = create_test_project(
            name="Test project",
        )

        scope = CatalogScope.objects.create(
            project=project,
        )

        domain_scope = scope.to_domain()

        self.assertEqual(
            domain_scope.tables,
            (),
        )


class KnowledgeCatalogModelTests(TestCase):
    def test_knowledge_catalog_defaults_to_pending_version_zero(self):
        project = create_test_project(
            name="Test project",
        )

        catalog = KnowledgeCatalog.objects.create(
            project=project,
        )

        self.assertEqual(
            catalog.status,
            KnowledgeCatalog.Status.PENDING,
        )
        self.assertEqual(
            catalog.version,
            0,
        )

    def test_catalog_can_have_multiple_schema_snapshots(self):
        project = create_test_project(
            name="Test project",
        )

        catalog = KnowledgeCatalog.objects.create(
            project=project,
        )

        snapshot_v1 = SchemaSnapshot.objects.create(
            catalog=catalog,
            version=1,
            schema_data={
                "tables": [],
            },
        )

        snapshot_v2 = SchemaSnapshot.objects.create(
            catalog=catalog,
            version=2,
            schema_data={
                "tables": [],
            },
        )

        self.assertEqual(
            catalog.snapshots.count(),
            2,
        )
        self.assertEqual(
            list(
                catalog.snapshots.values_list(
                    "version",
                    flat=True,
                ).order_by("version")
            ),
            [1, 2],
        )
        self.assertEqual(
            snapshot_v1.catalog,
            catalog,
        )
        self.assertEqual(
            snapshot_v2.catalog,
            catalog,
        )

    def test_catalog_cannot_have_two_snapshots_with_same_version(self):
        project = create_test_project(
            name="Test project",
        )

        catalog = KnowledgeCatalog.objects.create(
            project=project,
        )

        SchemaSnapshot.objects.create(
            catalog=catalog,
            version=1,
            schema_data={
                "tables": [],
            },
        )

        with self.assertRaises(IntegrityError):
            SchemaSnapshot.objects.create(
                catalog=catalog,
                version=1,
                schema_data={
                    "tables": [],
                },
            )
