import json
import logging
from unittest import TestCase

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
