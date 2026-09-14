from django.urls import path

from .views import catalog_build, catalog_scope, catalog_confirmation


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
    path(
        "projects/<uuid:project_id>/catalog/confirmation/",
        catalog_confirmation,
        name="catalog-confirmation",
    ),
]
