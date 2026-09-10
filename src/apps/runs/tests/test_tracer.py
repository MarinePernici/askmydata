from django.test import TestCase

from apps.projects.models import Project
from apps.runs.models import ExecutionTrace, QuestionRun
from apps.runs.tracer import DjangoQueryTracer


class DjangoQueryTracerTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test project",
        )
        self.question_run = QuestionRun.objects.create(
            project=self.project,
        )
        self.tracer = DjangoQueryTracer(
            question_run=self.question_run,
        )

    def test_record_persists_execution_trace(self):
        self.tracer.record(
            step="sql_generation",
            status="completed",
            duration_ms=42,
        )

        trace = ExecutionTrace.objects.get()

        self.assertEqual(
            trace.question_run,
            self.question_run,
        )
        self.assertEqual(trace.step, "sql_generation")
        self.assertEqual(trace.status, "completed")
        self.assertEqual(trace.duration_ms, 42)
        self.assertEqual(trace.error_code, "")
        self.assertEqual(trace.error_message, "")

    def test_record_persists_failure_information(self):
        self.tracer.record(
            step="query_execution",
            status="failed",
            duration_ms=120,
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