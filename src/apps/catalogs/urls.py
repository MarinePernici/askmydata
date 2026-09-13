from django.urls import path

from .views import catalog_scope


urlpatterns = [
    path(
        "projects/<uuid:project_id>/catalog/scope/",
        catalog_scope,
        name="catalog-scope",
    ),
]