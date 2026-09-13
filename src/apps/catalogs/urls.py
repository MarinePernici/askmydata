from django.urls import path

from .views import catalog_build, catalog_scope


urlpatterns = [
    path(
        "projects/<uuid:project_id>/catalog/scope/",
        catalog_scope,
        name="catalog-scope",
    ),
    path(
        "projects/<uuid:project_id>/catalog/build/",
        catalog_build,
        name="catalog-build",
    ),
]