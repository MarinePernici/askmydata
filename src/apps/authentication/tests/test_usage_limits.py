from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.authentication.exceptions import (
    QuestionTooLongError,
    UsageLimitExceededError,
)
from apps.authentication.models import DailyUsage
from apps.authentication.usage_limits import UsageLimitService
from apps.projects.models import Project


@override_settings(
    PUBLIC_DEMO_MODE=True,
    DEMO_MAX_PROJECTS_PER_USER=2,
    DEMO_MAX_DAILY_QUESTIONS=3,
    DEMO_MAX_DAILY_CATALOG_BUILDS=2,
    DEMO_MAX_QUESTION_LENGTH=2000,
)
class UsageLimitServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser",
            password="test-password",
        )
        cls.other_user = get_user_model().objects.create_user(
            username="otheruser",
            password="test-password",
        )

    def setUp(self):
        self.service = UsageLimitService()

    def create_project(self, name="Test project", **kwargs):
        return Project.objects.create(
            owner=self.user,
            name=name,
            **kwargs,
        )

    def test_project_creation_allowed_below_limit(self):
        self.create_project()

        self.service.ensure_project_creation_allowed(self.user)

    def test_project_creation_rejected_at_limit(self):
        self.create_project(name="Project 1")
        self.create_project(name="Project 2")

        with self.assertRaises(UsageLimitExceededError):
            self.service.ensure_project_creation_allowed(self.user)

    def test_archived_projects_count_towards_limit(self):
        self.create_project(name="Project 1")
        self.create_project(
            name="Archived project",
            status=Project.Status.ARCHIVED,
        )

        with self.assertRaises(UsageLimitExceededError):
            self.service.ensure_project_creation_allowed(self.user)

    def test_deleted_incomplete_project_frees_project_slot(self):
        self.create_project(name="Project 1")
        project = self.create_project(
            name="Incomplete project",
            status=Project.Status.DRAFT,
        )

        project.delete()

        self.service.ensure_project_creation_allowed(self.user)

    def test_project_limit_is_independent_for_each_user(self):
        self.create_project(name="Project 1")
        self.create_project(name="Project 2")

        self.service.ensure_project_creation_allowed(self.other_user)

    def test_question_at_maximum_length_is_allowed(self):
        self.service.ensure_question_length_allowed("a" * 2000)

    def test_question_above_maximum_length_is_rejected(self):
        with self.assertRaises(QuestionTooLongError):
            self.service.ensure_question_length_allowed("a" * 2001)

    def test_question_reservation_increments_counter(self):
        self.service.reserve_question(self.user)

        usage = DailyUsage.objects.get(
            user=self.user,
            date=timezone.localdate(),
        )

        self.assertEqual(usage.question_count, 1)
        self.assertEqual(usage.catalog_count, 0)

    def test_question_reservation_rejected_at_daily_limit(self):
        for _ in range(3):
            self.service.reserve_question(self.user)

        with self.assertRaises(UsageLimitExceededError):
            self.service.reserve_question(self.user)

        usage = DailyUsage.objects.get(
            user=self.user,
            date=timezone.localdate(),
        )

        self.assertEqual(usage.question_count, 3)

    def test_catalog_reservation_increments_counter(self):
        self.service.reserve_catalog_build(self.user)

        usage = DailyUsage.objects.get(
            user=self.user,
            date=timezone.localdate(),
        )

        self.assertEqual(usage.catalog_count, 1)
        self.assertEqual(usage.question_count, 0)

    def test_catalog_reservation_rejected_at_daily_limit(self):
        for _ in range(2):
            self.service.reserve_catalog_build(self.user)

        with self.assertRaises(UsageLimitExceededError):
            self.service.reserve_catalog_build(self.user)

        usage = DailyUsage.objects.get(
            user=self.user,
            date=timezone.localdate(),
        )

        self.assertEqual(usage.catalog_count, 2)

    def test_question_and_catalog_limits_are_independent(self):
        for _ in range(3):
            self.service.reserve_question(self.user)

        self.service.reserve_catalog_build(self.user)

        usage = DailyUsage.objects.get(
            user=self.user,
            date=timezone.localdate(),
        )

        self.assertEqual(usage.question_count, 3)
        self.assertEqual(usage.catalog_count, 1)

    def test_daily_limits_are_independent_for_each_user(self):
        for _ in range(3):
            self.service.reserve_question(self.user)

        for _ in range(2):
            self.service.reserve_catalog_build(self.user)

        self.service.reserve_question(self.other_user)
        self.service.reserve_catalog_build(self.other_user)

        usage = DailyUsage.objects.get(
            user=self.other_user,
            date=timezone.localdate(),
        )

        self.assertEqual(usage.question_count, 1)
        self.assertEqual(usage.catalog_count, 1)

    def test_daily_limits_reset_on_new_day(self):
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)

        DailyUsage.objects.create(
            user=self.user,
            date=today,
            question_count=3,
            catalog_count=2,
        )

        with patch(
            "apps.authentication.usage_limits.timezone.localdate",
            return_value=tomorrow,
        ):
            self.service.reserve_question(self.user)
            self.service.reserve_catalog_build(self.user)

        previous_usage = DailyUsage.objects.get(
            user=self.user,
            date=today,
        )
        new_usage = DailyUsage.objects.get(
            user=self.user,
            date=tomorrow,
        )

        self.assertEqual(previous_usage.question_count, 3)
        self.assertEqual(previous_usage.catalog_count, 2)
        self.assertEqual(new_usage.question_count, 1)
        self.assertEqual(new_usage.catalog_count, 1)

    def test_project_deletion_does_not_reset_daily_usage(self):
        project = self.create_project(
            status=Project.Status.DRAFT,
        )

        self.service.reserve_question(self.user)
        self.service.reserve_catalog_build(self.user)

        project.delete()

        usage = DailyUsage.objects.get(
            user=self.user,
            date=timezone.localdate(),
        )

        self.assertEqual(usage.question_count, 1)
        self.assertEqual(usage.catalog_count, 1)

    @override_settings(PUBLIC_DEMO_MODE=False)
    def test_standard_mode_does_not_enforce_limits(self):
        self.create_project(name="Project 1")
        self.create_project(name="Project 2")

        self.service.ensure_project_creation_allowed(self.user)
        self.service.ensure_question_length_allowed("a" * 2001)

        for _ in range(4):
            self.service.reserve_question(self.user)
            self.service.reserve_catalog_build(self.user)

        self.assertFalse(
            DailyUsage.objects.filter(user=self.user).exists(),
        )
