from django.urls import path

from .views import data_source_configure


urlpatterns = [
    path(
        "projects/<uuid:project_id>/data-source/",
        data_source_configure,
        name="data-source-configure",
    ),
]
