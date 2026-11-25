from django.conf import settings
from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.authentication.exceptions import (
    QuestionTooLongError,
    UsageLimitExceededError,
)
from apps.authentication.models import DailyUsage
from apps.projects.models import Project


class UsageLimitService:
    """Enforce resource usage limits in Public Demo mode."""

    def ensure_project_creation_allowed(self, user) -> None:
        if not settings.PUBLIC_DEMO_MODE:
            return

        project_count = Project.objects.filter(
            owner=user,
        ).count()

        if project_count >= settings.DEMO_MAX_PROJECTS_PER_USER:
            raise UsageLimitExceededError(
                _("You have reached the maximum number of projects (%(limit)s).")
                % {"limit": settings.DEMO_MAX_PROJECTS_PER_USER}
            )

    def ensure_question_length_allowed(self, question: str) -> None:
        if not settings.PUBLIC_DEMO_MODE:
            return

        if len(question) > settings.DEMO_MAX_QUESTION_LENGTH:
            raise QuestionTooLongError(
                _("Your question cannot exceed %(limit)s characters.")
                % {"limit": settings.DEMO_MAX_QUESTION_LENGTH}
            )

    def reserve_question(self, user) -> None:
        if not settings.PUBLIC_DEMO_MODE:
            return

        self._reserve(
            user=user,
            counter="question_count",
            limit=settings.DEMO_MAX_DAILY_QUESTIONS,
            error_message=_("You have reached your daily question limit (%(limit)s).")
            % {"limit": settings.DEMO_MAX_DAILY_QUESTIONS},
        )

    def reserve_catalog_build(self, user) -> None:
        if not settings.PUBLIC_DEMO_MODE:
            return

        self._reserve(
            user=user,
            counter="catalog_count",
            limit=settings.DEMO_MAX_DAILY_CATALOG_BUILDS,
            error_message=_(
                "You have reached your daily catalog generation limit (%(limit)s)."
            )
            % {"limit": settings.DEMO_MAX_DAILY_CATALOG_BUILDS},
        )

    def _reserve(
        self,
        user,
        counter: str,
        limit: int,
        error_message: str,
    ) -> None:
        usage, _created = DailyUsage.objects.get_or_create(
            user=user,
            date=timezone.localdate(),
        )

        updated = DailyUsage.objects.filter(
            pk=usage.pk,
            **{f"{counter}__lt": limit},
        ).update(
            **{counter: F(counter) + 1},
        )

        if updated == 0:
            raise UsageLimitExceededError(error_message)
