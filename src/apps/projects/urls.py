from django.urls import path

from .views import (
    project_archive,
    project_create,
    project_delete,
    project_detail,
    project_list,
    project_restore,
    project_setup_info,
    project_update,
)


urlpatterns = [
    path(
        "projects/",
        project_list,
        name="project-list",
    ),
    path(
        "projects/create/",
        project_create,
        name="project-create",
    ),
    path(
        "projects/<uuid:project_id>/setup/project-info/",
        project_setup_info,
        name="project-setup-info",
    ),
    path(
        "projects/<uuid:project_id>/",
        project_detail,
        name="project-detail",
    ),
    path(
        "projects/<uuid:project_id>/edit/",
        project_update,
        name="project-update",
    ),
    path(
        "projects/<uuid:project_id>/archive/",
        project_archive,
        name="project-archive",
    ),
    path(
        "projects/<uuid:project_id>/restore/",
        project_restore,
        name="project-restore",
    ),
    path(
        "projects/<uuid:project_id>/delete/",
        project_delete,
        name="project-delete",
    ),
]
