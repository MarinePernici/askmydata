import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.shortcuts import redirect, render

from apps.catalogs.exceptions import CatalogNotReadyError
from apps.catalogs.models import CatalogScope
from apps.catalogs.readers import CatalogReader
from apps.projects.exceptions import (
    ArchivedProjectError,
    InvalidProjectStateError,
)
from apps.projects.models import Project
from apps.projects.services import ProjectService
from config.demo_datasets import get_demo_dataset_connection

from .exceptions import DataSourceConnectionError
from .forms import DataSourceForm, DemoDataSourceForm
from .models import DataSource
from .services import DataSourceService

logger = logging.getLogger(__name__)


@login_required
def data_source_configure(request, project_id):
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

    demo_mode = settings.PUBLIC_DEMO_MODE
    form_class = DemoDataSourceForm if demo_mode else DataSourceForm

    if request.method == "POST":
        form = form_class(request.POST)

        if form.is_valid():
            try:
                if demo_mode:
                    dataset_key = form.cleaned_data["dataset"]
                    connection = get_demo_dataset_connection(dataset_key)
                    connection["demo_dataset_key"] = dataset_key
                else:
                    connection = {
                        field: form.cleaned_data[field]
                        for field in (
                            "host",
                            "port",
                            "database",
                            "username",
                            "password",
                        )
                    }

                DataSourceService().configure_and_test(
                    project=project,
                    **connection,
                )

            except ImproperlyConfigured:
                logger.exception(
                    "Demo dataset configuration is incomplete.",
                    extra={
                        "event": "demo_dataset.configuration_error",
                        "project_id": str(project.id),
                    },
                )
                form.add_error(
                    None,
                    "The selected demo dataset is temporarily unavailable.",
                )

            except DataSourceConnectionError as exc:
                form.add_error(None, str(exc))

            else:
                return redirect(
                    "catalog-scope",
                    project_id=project.id,
                )
    else:
        if demo_mode:
            form = DemoDataSourceForm()
        else:
            try:
                data_source = project.data_source
            except DataSource.DoesNotExist:
                form = DataSourceForm()
            else:
                form = DataSourceForm(
                    initial={
                        "host": data_source.host,
                        "port": data_source.port,
                        "database": data_source.database,
                        "username": data_source.username,
                    }
                )

    return render(
        request,
        "data_sources/configure.html",
        {
            "project": project,
            "form": form,
            "creation_mode": True,
            "demo_mode": demo_mode,
        },
    )


@login_required
def data_overview(request, project_id):
    try:
        project = ProjectService().get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    try:
        data_source = project.data_source
    except DataSource.DoesNotExist:
        raise Http404

    try:
        selected_tables_count = len(project.catalog_scope.selected_tables)
    except CatalogScope.DoesNotExist:
        selected_tables_count = 0

    return render(
        request,
        "data_sources/overview.html",
        {
            "project": project,
            "data_source": data_source,
            "selected_tables_count": selected_tables_count,
            "demo_mode": settings.PUBLIC_DEMO_MODE,
        },
    )


@login_required
def data_test_connection(request, project_id):
    if request.method != "POST":
        raise Http404

    if settings.PUBLIC_DEMO_MODE:
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
            "data-overview",
            project_id=project.id,
        )

    try:
        data_source = project.data_source
    except DataSource.DoesNotExist:
        raise Http404

    DataSourceService().test_connection(data_source)

    return redirect(
        "data-overview",
        project_id=project.id,
    )


@login_required
def data_schema(request, project_id):
    try:
        project = ProjectService().get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    try:
        catalog = CatalogReader().get_current(project)
    except CatalogNotReadyError:
        catalog = None

    selected_table = None

    if catalog and catalog.tables:
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

    references = ()
    referenced_by = ()
    foreign_key_columns = frozenset()

    if selected_table:
        references = tuple(
            relationship
            for relationship in selected_table.relationships
            if (
                relationship.source_schema == selected_table.schema
                and relationship.source_table == selected_table.name
            )
        )

        referenced_by = tuple(
            relationship
            for relationship in selected_table.relationships
            if (
                relationship.target_schema == selected_table.schema
                and relationship.target_table == selected_table.name
            )
        )

        foreign_key_columns = frozenset(
            relationship.source_column for relationship in references
        )

    return render(
        request,
        "data_sources/schema.html",
        {
            "project": project,
            "catalog": catalog,
            "selected_table": selected_table,
            "references": references,
            "referenced_by": referenced_by,
            "foreign_key_columns": foreign_key_columns,
        },
    )
