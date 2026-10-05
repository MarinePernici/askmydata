import json
import logging
from unittest import TestCase
from unittest.mock import patch

from opentelemetry.sdk.trace import TracerProvider

from config.logging import JsonFormatter


class JsonFormatterTests(TestCase):
    def setUp(self):
        self.formatter = JsonFormatter()

    def create_record(self, **extra):
        record = logging.LogRecord(
            name="apps.runs.services",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Question run event.",
            args=(),
            exc_info=None,
        )

        for key, value in extra.items():
            setattr(record, key, value)

        return record

    def test_format_includes_standard_fields(self):
        record = self.create_record()

        payload = json.loads(self.formatter.format(record))

        self.assertIn("timestamp", payload)
        self.assertEqual(payload["level"], "INFO")
        self.assertEqual(payload["logger"], "apps.runs.services")
        self.assertEqual(payload["message"], "Question run event.")

    def test_format_includes_supported_structured_fields(self):
        record = self.create_record(
            event="question_run.failed",
            project_id="project-123",
            question_run_id="run-456",
            connection_status="connected",
            catalog_version=2,
        )

        payload = json.loads(self.formatter.format(record))

        self.assertEqual(payload["event"], "question_run.failed")
        self.assertEqual(payload["project_id"], "project-123")
        self.assertEqual(payload["question_run_id"], "run-456")
        self.assertEqual(payload["connection_status"], "connected")
        self.assertEqual(payload["catalog_version"], 2)

    def test_format_omits_missing_structured_fields(self):
        record = self.create_record(event="catalog.build_failed")

        payload = json.loads(self.formatter.format(record))

        self.assertEqual(payload["event"], "catalog.build_failed")
        self.assertNotIn("project_id", payload)
        self.assertNotIn("question_run_id", payload)
        self.assertNotIn("connection_status", payload)
        self.assertNotIn("catalog_version", payload)

    def test_format_includes_exception(self):
        try:
            raise RuntimeError("Test failure")
        except RuntimeError:
            record = self.create_record()
            record.exc_info = __import__("sys").exc_info()

        payload = json.loads(self.formatter.format(record))

        self.assertIn("exception", payload)
        self.assertIn("RuntimeError: Test failure", payload["exception"])

    def test_format_includes_trace_context_when_span_is_active(self):
        tracer_provider = TracerProvider()
        tracer = tracer_provider.get_tracer("test")

        with tracer.start_as_current_span("test-span") as span:
            span_context = span.get_span_context()
            record = self.create_record()

            payload = json.loads(self.formatter.format(record))

        self.assertEqual(
            payload["trace_id"],
            format(span_context.trace_id, "032x"),
        )
        self.assertEqual(
            payload["span_id"],
            format(span_context.span_id, "016x"),
        )

    def test_format_omits_trace_context_without_active_span(self):
        record = self.create_record()

        payload = json.loads(self.formatter.format(record))

        self.assertNotIn("trace_id", payload)
        self.assertNotIn("span_id", payload)

    @patch(
        "config.logging.trace.get_current_span",
        side_effect=RuntimeError("OpenTelemetry failure"),
    )
    def test_format_still_works_when_trace_context_fails(self, get_current_span):
        record = self.create_record()

        payload = json.loads(self.formatter.format(record))

        self.assertEqual(payload["message"], "Question run event.")
        self.assertNotIn("trace_id", payload)
        self.assertNotIn("span_id", payload)
