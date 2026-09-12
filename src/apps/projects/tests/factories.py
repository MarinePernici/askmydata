import uuid

from django.contrib.auth import get_user_model

from apps.projects.models import Project


def create_test_user():
    return get_user_model().objects.create_user(
        username=f"test-user-{uuid.uuid4()}",
    )


def create_test_project(*, owner=None, **kwargs):
    if owner is None:
        owner = create_test_user()

    return Project.objects.create(
        owner=owner,
        **kwargs,
    )