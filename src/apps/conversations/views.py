from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render

from apps.projects.exceptions import ArchivedProjectError
from apps.projects.models import Project
from apps.projects.services import ProjectService
from config.services import create_question_run_service

from .models import Conversation
from .services import ConversationService


@login_required
def conversation_list(request, project_id):
    try:
        project = ProjectService().get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    conversations = ConversationService().list_conversations(project)

    return render(
        request,
        "conversations/list.html",
        {
            "project": project,
            "conversations": conversations,
        },
    )


@login_required
def conversation_create(request, project_id):
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
            "conversation-list",
            project_id=project.id,
        )

    conversation = ConversationService().create_conversation(
        project=project,
        title=request.POST.get("title", "").strip(),
    )

    return redirect(
        "conversation-detail",
        project_id=project.id,
        conversation_id=conversation.id,
    )


@login_required
def conversation_detail(
    request,
    project_id,
    conversation_id,
):
    try:
        project = ProjectService().get_for_user(
            project_id=project_id,
            user=request.user,
        )
    except Project.DoesNotExist:
        raise Http404

    try:
        conversation = ConversationService().get_conversation(
            project=project,
            conversation_id=conversation_id,
        )
    except Conversation.DoesNotExist:
        raise Http404

    conversation_messages = conversation.messages.order_by("sequence_number")

    conversations = ConversationService().list_conversations(project)

    return render(
        request,
        "conversations/detail.html",
        {
            "project": project,
            "conversation": conversation,
            "conversation_messages": conversation_messages,
            "conversations": conversations,
        },
    )


@login_required
def conversation_rename(request, project_id, conversation_id):
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
        conversation = ConversationService().get_conversation(
            project=project,
            conversation_id=conversation_id,
        )
    except Conversation.DoesNotExist:
        raise Http404

    try:
        ProjectService().ensure_writable(project)
    except ArchivedProjectError:
        return redirect(
            "conversation-detail",
            project_id=project.id,
            conversation_id=conversation.id,
        )

    title = request.POST.get("title", "").strip()

    if title:
        ConversationService().rename_conversation(
            conversation=conversation,
            title=title,
        )

    return redirect(
        "conversation-detail",
        project_id=project.id,
        conversation_id=conversation.id,
    )


@login_required
def conversation_ask(
    request,
    project_id,
    conversation_id,
):
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
        conversation = ConversationService().get_conversation(
            project=project,
            conversation_id=conversation_id,
        )
    except Conversation.DoesNotExist:
        raise Http404

    try:
        ProjectService().ensure_writable(project)
    except ArchivedProjectError:
        return redirect(
            "conversation-detail",
            project_id=project.id,
            conversation_id=conversation.id,
        )

    question = request.POST.get("question", "").strip()

    if not question:
        return redirect(
            "conversation-detail",
            project_id=project.id,
            conversation_id=conversation.id,
        )

    if project.status != Project.Status.READY:
        messages.error(
            request,
            "Project is not ready.",
        )

        return redirect(
            "conversation-detail",
            project_id=project.id,
            conversation_id=conversation.id,
        )

    service = create_question_run_service()

    try:
        service.run(
            project=project,
            conversation=conversation,
            question=question,
        )
    except Exception:
        messages.error(
            request,
            "Unable to process your question.",
        )

    return redirect(
        "conversation-detail",
        project_id=project.id,
        conversation_id=conversation.id,
    )
