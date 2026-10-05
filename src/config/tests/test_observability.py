from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
from opentelemetry.trace import SpanKind, StatusCode

from config.observability import (
    _parse_otlp_headers,
    configure_opentelemetry,
    record_llm_token_metrics,
    record_pipeline_step_metrics,
    record_question_run_metrics,
    traced_llm_call,
    traced_operation,
)


class ConfigureOpenTelemetryTests(SimpleTestCase):
    @override_settings(OTEL_ENABLED=False)
    @patch("config.observability.DjangoInstrumentor.instrument")
    @patch("config.observability.PsycopgInstrumentor.instrument")
    def test_does_not_instrument_when_disabled(
        self,
        psycopg_instrument,
        django_instrument,
    ):
        configure_opentelemetry()

        django_instrument.assert_not_called()
        psycopg_instrument.assert_not_called()

    @override_settings(
        OTEL_ENABLED=True,
        OTEL_SERVICE_NAME="askmydata-test",
        OTEL_EXPORTER_OTLP_ENDPOINT="https://example.test/otlp",
        OTEL_EXPORTER_OTLP_HEADERS="Authorization=test-token",
        OTEL_TRACES_SAMPLER_ARG=1.0,
    )
    @patch("config.observability.metrics.set_meter_provider")
    @patch("config.observability.trace.set_tracer_provider")
    @patch("config.observability.PsycopgInstrumentor.instrument")
    @patch("config.observability.DjangoInstrumentor.instrument")
    def test_instruments_django_and_psycopg_when_enabled(
        self,
        django_instrument,
        psycopg_instrument,
        set_meter_provider,
        set_tracer_provider,
    ):
        configure_opentelemetry()

        django_instrument.assert_called_once_with(
            excluded_urls=r"health/live/,health/ready/",
        )
        psycopg_instrument.assert_called_once_with()
        set_meter_provider.assert_called_once()
        set_tracer_provider.assert_called_once()


class ParseOtlpHeadersTests(SimpleTestCase):
    def test_returns_empty_dict_for_empty_headers(self):
        self.assertEqual(_parse_otlp_headers(""), {})

    def test_parses_headers(self):
        headers = _parse_otlp_headers("Authorization=Basic%20abc123,X-Custom=value")

        self.assertEqual(
            headers,
            {
                "Authorization": "Basic abc123",
                "X-Custom": "value",
            },
        )

    def test_ignores_malformed_headers(self):
        headers = _parse_otlp_headers("invalid,Authorization=Basic%20abc123")

        self.assertEqual(
            headers,
            {"Authorization": "Basic abc123"},
        )


class TracedOperationTests(SimpleTestCase):
    @patch("config.observability.trace.get_tracer")
    def test_creates_span_with_allowed_attributes(self, get_tracer):
        span = MagicMock()
        tracer = get_tracer.return_value
        tracer.start_as_current_span.return_value.__enter__.return_value = span

        from config.observability import traced_operation

        with traced_operation(
            "sql_validation",
            attributes={"pipeline_step": "sql_validation"},
        ):
            pass

        tracer.start_as_current_span.assert_called_once_with(
            "sql_validation",
            kind=SpanKind.INTERNAL,
            attributes={"pipeline_step": "sql_validation"},
            record_exception=False,
            set_status_on_exception=False,
        )

    @patch("config.observability.trace.get_tracer")
    def test_marks_span_as_error_without_recording_exception(self, get_tracer):
        span = MagicMock()
        tracer = get_tracer.return_value
        tracer.start_as_current_span.return_value.__enter__.return_value = span

        from config.observability import traced_operation

        with self.assertRaises(ValueError), traced_operation("sql_validation"):
            raise ValueError("sensitive error message")

        span.set_status.assert_called_once()
        status = span.set_status.call_args.args[0]
        self.assertEqual(status.status_code, StatusCode.ERROR)
        span.set_attribute.assert_called_once_with("error.type", "ValueError")
        span.record_exception.assert_not_called()

    @patch("config.observability.trace.get_tracer")
    def test_span_creation_failure_does_not_affect_business_execution(
        self,
        get_tracer,
    ):
        get_tracer.side_effect = RuntimeError("telemetry unavailable")

        executed = False

        with traced_operation("sql_validation") as span:
            executed = True

        self.assertTrue(executed)
        self.assertIsNone(span)

    @patch("config.observability.trace.get_tracer")
    def test_telemetry_failure_does_not_replace_business_exception(
        self,
        get_tracer,
    ):
        span = MagicMock()
        span.set_status.side_effect = RuntimeError("telemetry unavailable")

        tracer = get_tracer.return_value
        tracer.start_as_current_span.return_value.__enter__.return_value = span

        with (
            self.assertRaisesRegex(ValueError, "business failure"),
            traced_operation("sql_validation"),
        ):
            raise ValueError("business failure")


class TracedLlmCallTests(SimpleTestCase):
    @patch("config.observability.traced_operation")
    def test_traced_llm_call_uses_safe_operation_attribute(self, traced_operation):
        span = MagicMock()
        traced_operation.return_value.__enter__.return_value = span

        with traced_llm_call("sql_generation") as returned_span:
            self.assertIs(returned_span, span)

        traced_operation.assert_called_once_with(
            "llm_call",
            attributes={
                "llm.operation": "sql_generation",
            },
        )


class QuestionRunMetricsTests(SimpleTestCase):
    @patch("config.observability._question_run_duration")
    @patch("config.observability._question_runs_counter")
    def test_records_question_run_status_and_duration(
        self,
        question_runs_counter,
        question_run_duration,
    ):
        record_question_run_metrics(
            status="completed",
            duration_ms=125,
        )

        question_runs_counter.add.assert_called_once_with(
            1,
            attributes={"status": "completed"},
        )
        question_run_duration.record.assert_called_once_with(
            125,
            attributes={"status": "completed"},
        )


class LLMTokenMetricsTests(SimpleTestCase):
    @patch("config.observability._llm_tokens_counter")
    def test_records_prompt_and_completion_tokens(self, llm_tokens_counter):
        record_llm_token_metrics(
            model="test-model",
            prompt_tokens=100,
            completion_tokens=20,
        )

        self.assertEqual(llm_tokens_counter.add.call_count, 2)
        llm_tokens_counter.add.assert_any_call(
            100,
            attributes={
                "type": "prompt",
                "model": "test-model",
            },
        )
        llm_tokens_counter.add.assert_any_call(
            20,
            attributes={
                "type": "completion",
                "model": "test-model",
            },
        )

    @patch("config.observability._llm_tokens_counter")
    def test_ignores_missing_token_values(self, llm_tokens_counter):
        record_llm_token_metrics(
            model="test-model",
            prompt_tokens=None,
            completion_tokens=None,
        )

        llm_tokens_counter.add.assert_not_called()


class PipelineStepMetricsTests(SimpleTestCase):
    @patch("config.observability._pipeline_step_duration")
    def test_records_pipeline_step_duration(self, pipeline_step_duration):
        record_pipeline_step_metrics(
            step="sql_validation",
            duration_ms=42,
        )

        pipeline_step_duration.record.assert_called_once_with(
            42,
            attributes={
                "step": "sql_validation",
            },
        )


class MetricFailureIsolationTests(SimpleTestCase):
    @patch("config.observability._question_runs_counter")
    @patch("config.observability._question_run_duration")
    def test_question_run_metric_failure_does_not_propagate(
        self,
        question_run_duration,
        question_runs_counter,
    ):
        question_runs_counter.add.side_effect = RuntimeError("telemetry unavailable")

        record_question_run_metrics(
            status="completed",
            duration_ms=125,
        )

        question_run_duration.record.assert_called_once_with(
            125,
            attributes={"status": "completed"},
        )
