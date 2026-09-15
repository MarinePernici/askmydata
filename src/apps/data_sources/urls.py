from django.urls import path

from .views import data_source_configure, data_overview, data_schema


urlpatterns = [
    path(
        "projects/<uuid:project_id>/data/",
        data_overview,
        name="data-overview",
    ),
    path(
        "projects/<uuid:project_id>/data/schema/",
        data_schema,
        name="data-schema",
    ),
    path(
        "projects/<uuid:project_id>/data-source/",
        data_source_configure,
        name="data-source-configure",
    ),
]
