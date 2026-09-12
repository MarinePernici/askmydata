from django.urls import path

from .views import project_create, project_detail, project_list


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
]