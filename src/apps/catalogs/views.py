import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from apps.data_sources.models import DataSource
from apps.projects.exceptions import (
    ArchivedProjectError,
    InvalidProjectStateError,
)
from apps.projects.models import Project
from apps.projects.services import ProjectService
from config.services import create_catalog_service

from .exceptions import (
    CatalogNotReadyError,
    CatalogScopeNotConfiguredError,
    DataSourceNotConfiguredError,
)
from .models import CatalogScope, KnowledgeCatalog
from .readers import CatalogReader
from .scope_service import (
    CatalogScopeService,
    InvalidCatalogScopeSelectionError,
)

logger = logging.getLogger(__name__)


@login_required
def catalog_detail(request, project_id):
    try:
        project = ProjectService().get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    try:
        catalog_model = project.knowledge_catalog
    except KnowledgeCatalog.DoesNotExist:
        catalog_model = None

    catalog = None

    if catalog_model is not None:
        try:
            catalog = CatalogReader().get_current(project)
        except CatalogNotReadyError:
            pass

    selected_table = None
    tables_count = 0
    columns_count = 0
    business_synonyms_count = 0

    if catalog is not None:
        tables_count = len(catalog.tables)
        columns_count = sum(len(table.columns) for table in catalog.tables)
        business_synonyms_count = sum(
            len(table.semantic_metadata.business_synonyms)
            for table in catalog.tables
            if table.semantic_metadata is not None
        )

        if catalog.tables:
            requested_table = request.GET.get("table")

            if requested_table:
                selected_table = next(
                    (
                        table
                        for table in catalog.tables
                        if f"{table.schema}.{table.name}" == requested_table
                    ),
                    None,
                )

            if selected_table is None:
                selected_table = catalog.tables[0]

    return render(
        request,
        "catalogs/detail.html",
        {
            "project": project,
            "catalog_model": catalog_model,
            "catalog": catalog,
            "selected_table": selected_table,
            "tables_count": tables_count,
            "columns_count": columns_count,
            "business_synonyms_count": business_synonyms_count,
        },
    )


@login_required
def catalog_scope(request, project_id):
    project_service = ProjectService()

    try:
        project = project_service.get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    try:
        project_service.ensure_setup_incomplete(project)
    except InvalidProjectStateError:
        return redirect(
            "project-detail",
            project_id=project.id,
        )

    try:
        _ = project.data_source
    except DataSource.DoesNotExist:
        return render(
            request,
            "catalogs/scope.html",
            {
                "project": project,
                "available_tables": {},
                "data_source_missing": True,
                "creation_mode": True,
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
                    "creation_mode": True,
                },
            )

        return redirect(
            "catalog-confirmation",
            project_id=project.id,
        )

    try:
        selected_tables = {
            f"{selection['schema']}.{selection['table']}"
            for selection in project.catalog_scope.selected_tables
        }
    except CatalogScope.DoesNotExist:
        selected_tables = set()

    return render(
        request,
        "catalogs/scope.html",
        {
            "project": project,
            "available_tables": available_tables,
            "selected_tables": selected_tables,
            "data_source_missing": False,
            "creation_mode": True,
        },
    )


@login_required
def catalog_confirmation(request, project_id):
    project_service = ProjectService()

    try:
        project = project_service.get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    try:
        project_service.ensure_setup_incomplete(project)
    except InvalidProjectStateError:
        return redirect(
            "project-detail",
            project_id=project.id,
        )

    try:
        data_source = project.data_source
    except DataSource.DoesNotExist:
        return redirect(
            "data-source-configure",
            project_id=project.id,
        )

    try:
        selected_tables = project.catalog_scope.selected_tables
    except CatalogScope.DoesNotExist:
        return redirect(
            "catalog-scope",
            project_id=project.id,
        )

    available_tables = CatalogScopeService().discover_available_tables(project)
    available_tables_count = sum(len(tables) for tables in available_tables.values())

    return render(
        request,
        "catalogs/confirmation.html",
        {
            "project": project,
            "data_source": data_source,
            "selected_tables": selected_tables,
            "available_tables_count": available_tables_count,
            "creation_mode": True,
        },
    )


@login_required
def catalog_build(request, project_id):
    if request.method != "POST":
        raise Http404

    project_service = ProjectService()

    try:
        project = project_service.get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    try:
        project_service.ensure_setup_incomplete(project)
    except InvalidProjectStateError:
        return redirect(
            "project-detail",
            project_id=project.id,
        )

    try:
        create_catalog_service().build_for_project(project)
    except DataSourceNotConfiguredError:
        messages.error(
            request,
            _("Configure a data source before building the catalog."),
        )

        return redirect(
            "catalog-scope",
            project_id=project.id,
        )
    except CatalogScopeNotConfiguredError:
        messages.error(
            request,
            _("Select the project data before building the catalog."),
        )

        return redirect(
            "catalog-scope",
            project_id=project.id,
        )
    except Exception:
        logger.exception(
            "Unexpected catalog build failure.",
            extra={
                "event": "catalog.build_failed",
                "project_id": project.id,
            },
        )
        messages.error(
            request,
            _("Unable to build the catalog."),
        )

        return redirect(
            "catalog-scope",
            project_id=project.id,
        )

    return redirect(
        "conversation-list",
        project_id=project.id,
    )


@login_required
def catalog_regenerate(request, project_id):
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
        ProjectService().ensure_writable(project)
    except ArchivedProjectError:
        return redirect(
            "catalog-detail",
            project_id=project.id,
        )

    try:
        create_catalog_service().build_for_project(project)
    except (
        DataSourceNotConfiguredError,
        CatalogScopeNotConfiguredError,
    ):
        return redirect(
            "catalog-detail",
            project_id=project.id,
        )
    except Exception:
        logger.exception(
            "Unexpected catalog regeneration failure.",
            extra={
                "event": "catalog.regeneration_failed",
                "project_id": project.id,
            },
        )
        messages.error(
            request,
            _("Unable to regenerate the catalog."),
        )

    return redirect(
        "catalog-detail",
        project_id=project.id,
    )
