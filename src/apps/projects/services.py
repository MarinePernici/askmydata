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
        )