"""OpenTelemetry configuration for AskMyData."""

from collections.abc import Generator
from contextlib import contextmanager
from urllib.parse import unquote

from django.conf import settings
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.trace import SpanKind, Status, StatusCode


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
) -> Generator[trace.Span]:
    """Create an application span without recording sensitive content."""
    tracer = trace.get_tracer("askmydata")

    with tracer.start_as_current_span(
        name,
        kind=SpanKind.INTERNAL,
        attributes=attributes,
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        try:
            yield span
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR))
            span.set_attribute("error.type", exc.__class__.__name__)
            raise


@contextmanager
def traced_question_run(
    project_id: int,
    question_run_id: int,
) -> Generator[trace.Span]:
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
) -> Generator[trace.Span]:
    """Trace an LLM call without recording prompts or responses."""
    with traced_operation(
        "llm_call",
        attributes={
            "llm.operation": operation,
        },
    ) as span:
        yield span
