from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect

from .models import Project
from .services import ProjectService


@login_required
def project_list(request):
    projects = ProjectService().list_for_user(request.user)

    return render(
        request,
        "projects/project_list.html",
        {"projects": projects},
    )

@login_required
def project_create(request):
    if request.method == "POST":
        ProjectService().create(
            owner=request.user,
            name=request.POST["name"],
            description=request.POST.get("description", ""),
        )

        return redirect("project-list")

    return render(
        request,
        "projects/project_create.html",
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

    return render(
        request,
        "projects/project_detail.html",
        {"project": project},
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
        service.update(
            project=project,
            name=request.POST["name"],
            description=request.POST.get("description", ""),
        )

        return redirect(
            "project-detail",
            project_id=project.id,
        )

    return render(
        request,
        "projects/project_update.html",
        {"project": project},
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
        service.archive(project)

        return redirect("project-list")

    raise Http404