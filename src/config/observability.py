"""OpenTelemetry configuration for AskMyData."""

import logging
from collections.abc import Generator
from contextlib import contextmanager, nullcontext
from urllib.parse import unquote

from django.conf import settings
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.trace import SpanKind, Status, StatusCode

logger = logging.getLogger(__name__)

_meter = metrics.get_meter("askmydata")

_question_runs_counter = _meter.create_counter(
    "askmydata.question_runs",
    description="Number of AskMyData question runs.",
)

_question_run_duration = _meter.create_histogram(
    "askmydata.question_run.duration",
    unit="ms",
    description="Duration of AskMyData question runs.",
)

_llm_tokens_counter = _meter.create_counter(
    "askmydata.llm.tokens",
    description="Number of LLM tokens used.",
)

_pipeline_step_duration = _meter.create_histogram(
    "askmydata.pipeline_step.duration",
    unit="ms",
    description="Duration of Query Engine pipeline steps.",
)


def configure_opentelemetry() -> None:
    """Configure OpenTelemetry when explicitly enabled."""
    if not settings.OTEL_ENABLED:
        return

    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
        }
    )

    tracer_provider = TracerProvider(
        resource=resource,
        sampler=TraceIdRatioBased(settings.OTEL_TRACES_SAMPLER_ARG),
    )

    span_exporter = OTLPSpanExporter(
        endpoint=f"{settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip('/')}/v1/traces",
        headers=_parse_otlp_headers(settings.OTEL_EXPORTER_OTLP_HEADERS),
    )

    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    metric_exporter = OTLPMetricExporter(
        endpoint=f"{settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip('/')}/v1/metrics",
        headers=_parse_otlp_headers(settings.OTEL_EXPORTER_OTLP_HEADERS),
    )

    metric_reader = PeriodicExportingMetricReader(metric_exporter)

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )

    metrics.set_meter_provider(meter_provider)

    DjangoInstrumentor().instrument(
        excluded_urls=r"health/live/,health/ready/",
    )
    PsycopgInstrumentor().instrument()


def _parse_otlp_headers(raw_headers: str) -> dict[str, str]:
    """Parse OTLP HTTP headers from environment configuration."""
    if not raw_headers:
        return {}

    headers = {}

    for item in raw_headers.split(","):
        key, separator, value = item.partition("=")
        if not separator:
            continue

        headers[key.strip()] = unquote(value.strip())

    return headers


@contextmanager
def traced_operation(
    name: str,
    attributes: dict[str, str | int] | None = None,
) -> Generator[trace.Span | None]:
    """Create an application span without affecting business execution."""
    try:
        tracer = trace.get_tracer("askmydata")
        span_context = tracer.start_as_current_span(
            name,
            kind=SpanKind.INTERNAL,
            attributes=attributes,
            record_exception=False,
            set_status_on_exception=False,
        )
    except Exception:
        logger.exception("Failed to create OpenTelemetry span.")
        span_context = nullcontext(None)

    with span_context as span:
        try:
            yield span
        except Exception as exc:
            if span is not None:
                try:
                    span.set_status(Status(StatusCode.ERROR))
                    span.set_attribute("error.type", exc.__class__.__name__)
                except Exception:
                    logger.exception("Failed to update OpenTelemetry span.")

            raise


@contextmanager
def traced_question_run(
    project_id: int,
    question_run_id: int,
) -> Generator[trace.Span | None]:
    """Trace one question run using safe correlation identifiers only."""
    with traced_operation(
        "question_run",
        attributes={
            "project_id": project_id,
            "question_run_id": question_run_id,
        },
    ) as span:
        yield span


@contextmanager
def traced_llm_call(
    operation: str,
) -> Generator[trace.Span | None]:
    """Trace an LLM call without recording prompts or responses."""
    with traced_operation(
        "llm_call",
        attributes={
            "llm.operation": operation,
        },
    ) as span:
        yield span


def record_question_run_metrics(
    *,
    status: str,
    duration_ms: int,
) -> None:
    """Record operational metrics for a completed question run."""
    attributes = {"status": status}

    _record_metric(
        lambda: _question_runs_counter.add(
            1,
            attributes=attributes,
        )
    )
    _record_metric(
        lambda: _question_run_duration.record(
            duration_ms,
            attributes=attributes,
        )
    )


def record_llm_token_metrics(
    *,
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> None:
    """Record LLM token usage when provided by the model provider."""
    if prompt_tokens is not None:
        _record_metric(
            lambda: _llm_tokens_counter.add(
                prompt_tokens,
                attributes={
                    "type": "prompt",
                    "model": model,
                },
            )
        )

    if completion_tokens is not None:
        _record_metric(
            lambda: _llm_tokens_counter.add(
                completion_tokens,
                attributes={
                    "type": "completion",
                    "model": model,
                },
            )
        )


def record_pipeline_step_metrics(
    *,
    step: str,
    duration_ms: int,
) -> None:
    """Record the duration of a Query Engine pipeline step."""
    _record_metric(
        lambda: _pipeline_step_duration.record(
            duration_ms,
            attributes={
                "step": step,
            },
        )
    )


def _record_metric(operation) -> None:
    """Record a metric without allowing telemetry failures to affect the application."""
    try:
        operation()
    except Exception:
        logger.exception("Failed to record OpenTelemetry metric.")
