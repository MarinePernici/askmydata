from apps.catalogs.exceptions import CatalogNotReadyError
from apps.catalogs.models import (
    KnowledgeCatalog as KnowledgeCatalogModel,
    SchemaSnapshot,
)
from apps.projects.models import Project
from catalog.snapshot_deserializer import CatalogSnapshotDeserializer
from catalog.types import KnowledgeCatalog


class CatalogReader:
    def __init__(
        self,
        deserializer: CatalogSnapshotDeserializer | None = None,
    ) -> None:
        self._deserializer = (
            deserializer or CatalogSnapshotDeserializer()
        )

    def get_current(
        self,
        project: Project,
    ) -> KnowledgeCatalog:
        try:
            catalog = project.knowledge_catalog
        except KnowledgeCatalogModel.DoesNotExist as exc:
            raise CatalogNotReadyError(
                "Project has no knowledge catalog."
            ) from exc

        if (
            catalog.status != KnowledgeCatalogModel.Status.READY
            or catalog.version == 0
        ):
            raise CatalogNotReadyError(
                "Project knowledge catalog is not ready."
            )

        try:
            snapshot = catalog.snapshots.get(
                version=catalog.version,
            )
        except SchemaSnapshot.DoesNotExist as exc:
            raise CatalogNotReadyError(
                "Current catalog snapshot does not exist."
            ) from exc

        return self._deserializer.deserialize(
            snapshot.schema_data
        )