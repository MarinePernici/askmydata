from django.urls import path

from .views import (
    catalog_build,
    catalog_confirmation,
    catalog_detail,
    catalog_scope,
    catalog_regenerate,
)


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
    path(
        "projects/<uuid:project_id>/catalog/detail/",
        catalog_detail,
        name="catalog-detail",
    ),
    path(
        "projects/<uuid:project_id>/catalog/regenerate/",
        catalog_regenerate,
        name="catalog-regenerate",
    ),
]
