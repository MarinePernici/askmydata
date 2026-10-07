import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.projects.models import Project


class QuestionRun(models.Model):
    """Persistent record of one AI query pipeline execution."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        RUNNING = "running", _("Running")
        NEEDS_CLARIFICATION = "needs_clarification", _("Needs clarification")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")
        REJECTED = "rejected", _("Rejected")
        ABANDONED = "abandoned", _("Abandoned")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="question_runs",
    )

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    latency_ms = models.PositiveIntegerField(null=True, blank=True)

    model_name = models.CharField(
        max_length=255,
        blank=True,
    )

    prompt_tokens = models.PositiveIntegerField(null=True, blank=True)
    completion_tokens = models.PositiveIntegerField(null=True, blank=True)

    estimated_cost = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
    )

    row_count = models.PositiveIntegerField(null=True, blank=True)

    error_code = models.CharField(
        max_length=100,
        blank=True,
    )

    error_message = models.TextField(blank=True)

    conversation = models.ForeignKey(
        "conversations.Conversation",
        on_delete=models.CASCADE,
        related_name="question_runs",
        null=True,
        blank=True,
    )

    user_message = models.OneToOneField(
        "conversations.Message",
        on_delete=models.SET_NULL,
        related_name="question_run",
        null=True,
        blank=True,
    )

    assistant_message = models.OneToOneField(
        "conversations.Message",
        on_delete=models.SET_NULL,
        related_name="generated_by_run",
        null=True,
        blank=True,
    )


class ExecutionTrace(models.Model):
    """Persistent trace of one query pipeline step."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        RUNNING = "running", _("Running")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    question_run = models.ForeignKey(
        QuestionRun,
        on_delete=models.CASCADE,
        related_name="execution_traces",
    )

    step = models.CharField(max_length=100)

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    duration_ms = models.PositiveIntegerField(null=True, blank=True)

    technical_metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    error_code = models.CharField(
        max_length=100,
        blank=True,
    )

    error_message = models.TextField(blank=True)
