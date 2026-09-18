from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect

from .exceptions import (
    ArchivedProjectError,
    InvalidProjectStateError,
)
from .forms import ProjectForm
from .models import Project
from .services import ProjectService


@login_required
def project_list(request):
    projects = ProjectService().list_for_user(request.user)

    active_projects = projects.filter(
        status__in=[
            Project.Status.READY,
            Project.Status.REGENERATING_CATALOG,
        ]
    )

    setup_projects = projects.filter(
        status__in=[
            Project.Status.DRAFT,
            Project.Status.CONFIGURING,
            Project.Status.BUILDING_CATALOG,
        ]
    )

    setup_project_items = [
        {
            "project": project,
            "setup_url_name": ProjectService().get_setup_url_name(project),
        }
        for project in setup_projects
    ]

    archived_projects = projects.filter(
        status=Project.Status.ARCHIVED,
    )

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": projects,
            "active_projects": active_projects,
            "setup_projects": setup_projects,
            "setup_project_items": setup_project_items,
            "archived_projects": archived_projects,
        },
    )


@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            project = ProjectService().create(
                owner=request.user,
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
            )

            return redirect(
                "data-source-configure",
                project_id=project.id,
            )
    else:
        form = ProjectForm()

    return render(
        request,
        "projects/project_create.html",
        {
            "form": form,
            "creation_mode": True,
        },
    )


@login_required
def project_setup_info(request, project_id):
    service = ProjectService()

    try:
        project = service.get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    try:
        service.ensure_setup_incomplete(project)
    except InvalidProjectStateError:
        return redirect(
            "project-detail",
            project_id=project.id,
        )

    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            service.update(
                project=project,
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
            )

            return redirect(
                "data-source-configure",
                project_id=project.id,
            )
    else:
        form = ProjectForm(
            initial={
                "name": project.name,
                "description": project.description,
            }
        )

    return render(
        request,
        "projects/project_create.html",
        {
            "project": project,
            "form": form,
        },
    )


@login_required
def project_detail(request, project_id):
    try:
        project = ProjectService().get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    return redirect(
        "data-overview",
        project_id=project.id,
    )


@login_required
def project_update(request, project_id):
    service = ProjectService()

    try:
        project = service.get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    if request.method == "POST":
        try:
            service.ensure_writable(project)
        except ArchivedProjectError:
            return redirect(
                "project-update",
                project_id=project.id,
            )

        form = ProjectForm(request.POST)

        if form.is_valid():
            service.update(
                project=project,
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
            )

            return redirect(
                "project-detail",
                project_id=project.id,
            )

    else:
        form = ProjectForm(
            initial={
                "name": project.name,
                "description": project.description,
            }
        )

    return render(
        request,
        "projects/project_update.html",
        {
            "project": project,
            "form": form,
        },
    )


@login_required
def project_archive(request, project_id):
    service = ProjectService()

    try:
        project = service.get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    if request.method == "POST":
        try:
            service.archive(project)
        except InvalidProjectStateError:
            raise Http404

        return redirect("project-list")

    raise Http404


@login_required
def project_restore(request, project_id):
    service = ProjectService()

    try:
        project = service.get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    if request.method == "POST":
        try:
            service.restore(project)
        except InvalidProjectStateError:
            raise Http404

        return redirect(
            "project-detail",
            project_id=project.id,
        )

    raise Http404


@login_required
def project_delete(request, project_id):
    service = ProjectService()

    try:
        project = service.get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    if request.method == "POST":
        try:
            service.delete_incomplete(project)
        except InvalidProjectStateError:
            raise Http404

        return redirect("project-list")

    raise Http404
