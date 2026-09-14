from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render

from apps.data_sources.models import DataSource
from apps.projects.models import Project
from apps.projects.services import ProjectService

from .exceptions import (
    CatalogScopeNotConfiguredError,
    DataSourceNotConfiguredError,
)
from .models import CatalogScope, KnowledgeCatalog
from .scope_service import (
    CatalogScopeService,
    InvalidCatalogScopeSelectionError,
)
from .services import CatalogService


@login_required
def catalog_scope(request, project_id):
    try:
        project = ProjectService().get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    try:
        project.data_source
    except DataSource.DoesNotExist:
        return render(
            request,
            "catalogs/scope.html",
            {
                "project": project,
                "available_tables": {},
                "data_source_missing": True,
            },
        )

    service = CatalogScopeService()

    available_tables = service.discover_available_tables(project)

    if request.method == "POST":
        selections = []

        for value in request.POST.getlist("tables"):
            schema, table = value.split(".", 1)

            selections.append(
                {
                    "schema": schema,
                    "table": table,
                }
            )

        try:
            service.save_selection(
                project=project,
                selections=selections,
                available_tables=available_tables,
            )
        except InvalidCatalogScopeSelectionError as exc:
            return render(
                request,
                "catalogs/scope.html",
                {
                    "project": project,
                    "available_tables": available_tables,
                    "data_source_missing": False,
                    "error": str(exc),
                },
            )

        return redirect(
            "catalog-scope",
            project_id=project.id,
        )

    try:
        selected_tables = {
            f"{selection['schema']}.{selection['table']}"
            for selection in project.catalog_scope.selected_tables
        }
    except CatalogScope.DoesNotExist:
        selected_tables = set()

    try:
        knowledge_catalog = project.knowledge_catalog
    except KnowledgeCatalog.DoesNotExist:
        knowledge_catalog = None

    return render(
        request,
        "catalogs/scope.html",
        {
            "project": project,
            "available_tables": available_tables,
            "selected_tables": selected_tables,
            "data_source_missing": False,
            "knowledge_catalog": knowledge_catalog,
        },
    )


@login_required
def catalog_build(request, project_id):
    if request.method != "POST":
        raise Http404

    try:
        project = ProjectService().get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    try:
        CatalogService().build_for_project(project)
    except (
        CatalogScopeNotConfiguredError,
        DataSourceNotConfiguredError,
    ) as exc:
        messages.error(request, str(exc))

        return redirect(
            "catalog-scope",
            project_id=project.id,
        )
    except Exception:
        messages.error(
            request,
            "Unable to build the catalog.",
        )

        return redirect(
            "catalog-scope",
            project_id=project.id,
        )

    return redirect(
        "conversation-list",
        project_id=project.id,
    )
