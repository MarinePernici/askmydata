import unittest

from query_engine.tracer import QueryTracer, NullQueryTracer


class QueryTracerTests(unittest.TestCase):
    def test_query_tracer_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            QueryTracer()

    def test_null_query_tracer_accepts_trace_events(self):
        tracer = NullQueryTracer()

        tracer.record(
            step="sql_generation",
            status="completed",
            duration_ms=12,
        )
