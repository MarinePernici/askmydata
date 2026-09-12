from apps.projects.models import Project


class ProjectService:
    def archive(self, project: Project) -> None:
        project.status = Project.Status.ARCHIVED
        project.save(update_fields=["status"])

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