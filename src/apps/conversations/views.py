from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from apps.projects.exceptions import ArchivedProjectError
from apps.projects.models import Project
from apps.projects.services import ProjectService
from apps.runs.error_messages import get_safe_interface_error_message
from config.services import create_question_run_service
from query_engine.exceptions import (
    DataSourceConnectionError,
    DataSourcePermissionError,
    QueryTimeoutError,
    SQLValidationError,
)

from .models import Conversation
from .services import ConversationService


def _get_message_question_run(message):
    try:
        return message.generated_by_run
    except ObjectDoesNotExist:
        return None


DEVELOPER_STEP_LABELS = {
    "sql_generation": _("SQL generation"),
    "sql_validation": _("SQL validation"),
    "query_execution": _("Query execution"),
    "result_validation": _("Result validation"),
    "answer_generation": _("Answer generation"),
}


def _get_developer_status_badge(status):
    return {
        "completed": "success",
        "failed": "error",
        "rejected": "warning",
        "needs_clarification": "info",
        "running": "info",
        "pending": "neutral",
        "abandoned": "neutral",
    }.get(status, "neutral")


def _build_developer_details(message):
    run = _get_message_question_run(message)

    if run is None:
        return None

    traces = list(run.execution_traces.all())

    generated_sql = None
    for trace in traces:
        if trace.step == "sql_validation":
            generated_sql = trace.technical_metadata.get("sql")
            break

    return {
        "status": run.get_status_display(),
        "status_badge": _get_developer_status_badge(run.status),
        "latency_ms": run.latency_ms,
        "model_name": run.model_name,
        "prompt_tokens": run.prompt_tokens,
        "completion_tokens": run.completion_tokens,
        "row_count": run.row_count,
        "generated_sql": generated_sql,
        "steps": [
            {
                "name": DEVELOPER_STEP_LABELS.get(
                    trace.step,
                    trace.step.replace("_", " ").capitalize(),
                ),
                "status": trace.get_status_display(),
                "status_badge": _get_developer_status_badge(trace.status),
                "duration_ms": trace.duration_ms,
            }
            for trace in traces
        ],
    }


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

    developer_mode = getattr(
        getattr(request.user, "preferences", None),
        "developer_mode",
        False,
    )

    conversation_messages = conversation.messages.order_by("sequence_number")

    if developer_mode:
        conversation_messages = conversation_messages.select_related(
            "generated_by_run",
        ).prefetch_related(
            "generated_by_run__execution_traces",
        )

        conversation_messages = list(conversation_messages)

        for message in conversation_messages:
            message.developer_details = _build_developer_details(message)

    conversations = ConversationService().list_conversations(project)

    return render(
        request,
        "conversations/detail.html",
        {
            "project": project,
            "conversation": conversation,
            "conversation_messages": conversation_messages,
            "conversations": conversations,
            "developer_mode": developer_mode,
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
            _("Project is not ready."),
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

    except (
        DataSourceConnectionError,
        DataSourcePermissionError,
        QueryTimeoutError,
    ) as exc:
        messages.error(
            request,
            get_safe_interface_error_message(exc),
            extra_tags="question-error",
        )
    except SQLValidationError:
        pass
    except Exception as exc:  # noqa: BLE001 - Final UI safety net.
        messages.error(
            request,
            get_safe_interface_error_message(exc),
            extra_tags="question-error",
        )

    return redirect(
        "conversation-detail",
        project_id=project.id,
        conversation_id=conversation.id,
    )
