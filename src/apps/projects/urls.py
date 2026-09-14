from django.urls import path

from .views import (
    project_archive,
    project_create,
    project_detail,
    project_list,
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
]
