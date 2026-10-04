from datetime import UTC, datetime

from django.test import TestCase

from apps.projects.tests.factories import create_test_project
from apps.runs.models import ExecutionTrace, QuestionRun
from apps.runs.tracer import DjangoQueryTracer


class DjangoQueryTracerTests(TestCase):
    def setUp(self):
        self.project = create_test_project(
            name="Test project",
        )
        self.question_run = QuestionRun.objects.create(
            project=self.project,
        )
        self.tracer = DjangoQueryTracer(
            question_run=self.question_run,
        )
        self.started_at = datetime(
            2026,
            10,
            4,
            12,
            0,
            0,
            tzinfo=UTC,
        )
        self.completed_at = datetime(
            2026,
            10,
            4,
            12,
            0,
            1,
            tzinfo=UTC,
        )

    def test_record_persists_execution_trace(self):
        self.tracer.record(
            step="sql_generation",
            status="completed",
            duration_ms=42,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )

        trace = ExecutionTrace.objects.get()

        self.assertEqual(
            trace.question_run,
            self.question_run,
        )
        self.assertEqual(trace.step, "sql_generation")
        self.assertEqual(trace.status, "completed")
        self.assertEqual(trace.duration_ms, 42)
        self.assertEqual(trace.started_at, self.started_at)
        self.assertEqual(trace.completed_at, self.completed_at)
        self.assertEqual(trace.error_code, "")
        self.assertEqual(trace.error_message, "")

    def test_record_persists_failure_information(self):
        self.tracer.record(
            step="query_execution",
            status="failed",
            duration_ms=120,
            started_at=self.started_at,
            completed_at=self.completed_at,
            error_code="QueryCanceled",
            error_message="Query execution timed out.",
        )

        trace = ExecutionTrace.objects.get()

        self.assertEqual(trace.step, "query_execution")
        self.assertEqual(trace.status, "failed")
        self.assertEqual(trace.duration_ms, 120)
        self.assertEqual(trace.error_code, "QueryCanceled")
        self.assertEqual(
            trace.error_message,
            "Query execution timed out.",
        )

    def test_record_persists_technical_metadata(self):
        metadata = {
            "sql": "SELECT COUNT(*) FROM users",
        }

        self.tracer.record(
            step="sql_generation",
            status="completed",
            duration_ms=42,
            started_at=self.started_at,
            completed_at=self.completed_at,
            technical_metadata=metadata,
        )

        trace = ExecutionTrace.objects.get()

        self.assertEqual(
            trace.technical_metadata,
            metadata,
        )
