from django.urls import path

from .views import (
    conversation_ask,
    conversation_create,
    conversation_detail,
    conversation_list,
    conversation_rename,
)

urlpatterns = [
    path(
        "projects/<uuid:project_id>/conversations/",
        conversation_list,
        name="conversation-list",
    ),
    path(
        "projects/<uuid:project_id>/conversations/create/",
        conversation_create,
        name="conversation-create",
    ),
    path(
        "projects/<uuid:project_id>/conversations/<uuid:conversation_id>/",
        conversation_detail,
        name="conversation-detail",
    ),
    path(
        "projects/<uuid:project_id>/conversations/<uuid:conversation_id>/ask/",
        conversation_ask,
        name="conversation-ask",
    ),
    path(
        "projects/<uuid:project_id>/conversations/<uuid:conversation_id>/rename/",
        conversation_rename,
        name="conversation-rename",
    ),
]
