from django.core.exceptions import ObjectDoesNotExist

from apps.projects.exceptions import (
    ArchivedProjectError,
    InvalidProjectStateError,
)
from apps.projects.models import Project


class ProjectService:
    def archive(self, project: Project) -> None:
        if project.is_archived:
            return

        if project.status != Project.Status.READY:
            raise InvalidProjectStateError("Only ready projects can be archived.")

        project.status = Project.Status.ARCHIVED
        project.save(update_fields=["status"])

    def restore(self, project: Project) -> None:
        if not project.is_archived:
            raise InvalidProjectStateError("Only archived projects can be restored.")

        project.status = Project.Status.READY
        project.save(update_fields=["status"])

    def delete_incomplete(self, project: Project) -> None:
        incomplete_statuses = {
            Project.Status.DRAFT,
            Project.Status.CONFIGURING,
            Project.Status.BUILDING_CATALOG,
        }

        if project.status not in incomplete_statuses:
            raise InvalidProjectStateError("Only incomplete projects can be deleted.")

        project.delete()

    def mark_configuring(self, project: Project) -> None:
        project.status = Project.Status.CONFIGURING
        project.save(update_fields=["status"])

    def mark_building_catalog(self, project: Project) -> None:
        project.status = Project.Status.BUILDING_CATALOG
        project.save(update_fields=["status"])

    def mark_ready(self, project: Project) -> None:
        project.status = Project.Status.READY
        project.save(update_fields=["status"])

    def mark_regenerating_catalog(self, project: Project) -> None:
        project.status = Project.Status.REGENERATING_CATALOG
        project.save(update_fields=["status"])

    def create(
        self,
        owner,
        name: str,
        description: str = "",
    ) -> Project:
        return Project.objects.create(
            owner=owner,
            name=name,
            description=description,
        )

    def update(
        self,
        project: Project,
        name: str,
        description: str,
    ) -> None:
        project.name = name
        project.description = description
        project.save(
            update_fields=[
                "name",
                "description",
                "updated_at",
            ]
        )

    def get_for_user(
        self,
        project_id,
        user,
    ) -> Project:
        return Project.objects.get(
            id=project_id,
            owner=user,
        )

    def list_for_user(self, user):
        return Project.objects.filter(
            owner=user,
        ).order_by("-created_at", "-id")

    def ensure_writable(self, project: Project) -> None:
        if project.is_archived:
            raise ArchivedProjectError("Archived projects are read-only.")

    def get_setup_url_name(self, project: Project) -> str:
        incomplete_statuses = {
            Project.Status.DRAFT,
            Project.Status.CONFIGURING,
            Project.Status.BUILDING_CATALOG,
        }

        if project.status not in incomplete_statuses:
            raise InvalidProjectStateError(
                "Project setup can only be resumed for incomplete projects."
            )

        try:
            _ = project.data_source
        except ObjectDoesNotExist:
            return "data-source-configure"

        try:
            _ = project.catalog_scope
        except ObjectDoesNotExist:
            return "catalog-scope"

        return "catalog-confirmation"

    def ensure_setup_incomplete(self, project: Project) -> None:
        incomplete_statuses = {
            Project.Status.DRAFT,
            Project.Status.CONFIGURING,
            Project.Status.BUILDING_CATALOG,
        }

        if project.status not in incomplete_statuses:
            raise InvalidProjectStateError("Project setup is already complete.")
