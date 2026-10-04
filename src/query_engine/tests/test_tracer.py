import unittest
from datetime import UTC, datetime

from query_engine.tracer import NullQueryTracer, QueryTracer


class QueryTracerTests(unittest.TestCase):
    def test_query_tracer_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            QueryTracer()

    def test_null_query_tracer_accepts_trace_events(self):
        tracer = NullQueryTracer()

        started_at = datetime(
            2026,
            10,
            4,
            12,
            0,
            0,
            tzinfo=UTC,
        )
        completed_at = datetime(
            2026,
            10,
            4,
            12,
            0,
            1,
            tzinfo=UTC,
        )

        tracer.record(
            step="sql_generation",
            status="completed",
            duration_ms=12,
            started_at=started_at,
            completed_at=completed_at,
        )
