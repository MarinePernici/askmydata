from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render

from apps.projects.models import Project
from apps.projects.services import ProjectService

from .exceptions import DataSourceConnectionError
from .forms import DataSourceForm
from .models import DataSource
from .services import DataSourceService

@login_required
def data_source_configure(request, project_id):
    try:
        project = ProjectService().get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    if request.method == "POST":
        form = DataSourceForm(request.POST)

        if form.is_valid():
            try:
                DataSourceService().configure_and_test(
                    project=project,
                    host=form.cleaned_data["host"],
                    port=form.cleaned_data["port"],
                    database=form.cleaned_data["database"],
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password"],
                )
            except DataSourceConnectionError as exc:
                form.add_error(None, str(exc))
            else:
                return redirect(
                    "catalog-scope",
                    project_id=project.id,
                )
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
        },
    )