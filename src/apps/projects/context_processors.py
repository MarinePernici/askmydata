from .models import Project


def sidebar_projects(request):
    if not request.user.is_authenticated:
        return {"sidebar_projects": Project.objects.none()}

    projects = Project.objects.filter(
        owner=request.user,
        status__in=[
            Project.Status.READY,
            Project.Status.REGENERATING_CATALOG,
            Project.Status.ARCHIVED,
        ],
    ).order_by("name")

    return {"sidebar_projects": projects}
