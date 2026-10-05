<!-- docs/adrs/0005-opentelemetry-observability.md -->

# ADR-0005 — Adopt OpenTelemetry for Application Observability

## Status

Accepted

**Date:** 2026-10-04

---

# Context

AskMyData is intended to demonstrate production-oriented software engineering practices for an AI-powered application.

The application already provides several complementary observability mechanisms:

- structured JSON application logs;
- correlation through Project and QuestionRun identifiers;
- persistent QuestionRun execution metrics;
- persistent ExecutionTrace records for Query Engine steps;
- liveness and readiness health checks.

These mechanisms provide application-specific diagnostics and execution history but do not provide a standardized telemetry layer for external monitoring systems.

The Production-ready Portfolio stage requires operational monitoring of critical application and AI pipeline operations.

The observability architecture should therefore:

- provide standardized traces and operational metrics;
- preserve the existing domain-level observability mechanisms;
- support correlation across HTTP requests, application logs and AI pipeline operations;
- avoid exposing user data, SQL, prompts or other sensitive information;
- remain optional and non-blocking;
- avoid unnecessary infrastructure for the expected Public Demo workload;
- remain portable between observability backends.

---

# Decision

AskMyData adopts **OpenTelemetry** as the standard framework for exportable application telemetry.

OpenTelemetry complements, but does not replace:

- `QuestionRun`, which stores persistent metrics for individual AI query executions;
- `ExecutionTrace`, which stores persistent Query Engine step traceability;
- structured application logs, which provide operational and diagnostic events.

The initial OpenTelemetry implementation provides **distributed traces and operational metrics**.

## Instrumentation Strategy

AskMyData combines automatic infrastructure instrumentation with targeted custom instrumentation.

Automatic instrumentation covers:

- Django HTTP requests;
- PostgreSQL interactions supported by the OpenTelemetry instrumentation ecosystem.

Frequently invoked technical endpoints such as liveness and readiness health checks are excluded from HTTP tracing where appropriate.

Custom spans are limited to high-value AI pipeline operations, including:

- QuestionRun execution;
- SQL generation;
- SQL validation;
- query execution;
- answer generation;
- LLM calls.

Instrumentation is intentionally selective rather than exhaustive.

OpenTelemetry spans do not replace persistent `ExecutionTrace` records.

## LLM Instrumentation

LLM calls are represented by dedicated spans so that their latency can be distinguished from SQL validation, database execution and other pipeline operations.

Only explicitly allowed technical metadata may be attached to LLM spans, such as:

- LLM provider;
- model name;
- operation type.

Prompts, generated content and user questions are never exported.

## Operational Metrics

The initial OpenTelemetry integration exposes a deliberately small set of operational metrics:

- QuestionRun count, classified by status;
- QuestionRun duration;
- LLM token usage, classified by token type and model;
- pipeline step duration, classified by step.

Detailed per-execution information remains stored in PostgreSQL through `QuestionRun` and `ExecutionTrace`.

Additional metrics should only be introduced when justified by a concrete monitoring requirement.

Estimated LLM cost is not exported while cost calculation is not implemented by the application.

## Telemetry Attributes

Exported telemetry follows an explicit allowlist.

Permitted attributes may include:

- Project identifier;
- QuestionRun identifier;
- pipeline step;
- run status;
- LLM provider;
- LLM model;
- data source type;
- error type.

Numerical measurements such as durations, token counts and returned row counts may also be exported when appropriate.

The following content must never be exported through OpenTelemetry:

- user questions;
- generated answers;
- generated SQL;
- LLM prompts;
- query results;
- business data;
- database schemas or catalog content;
- credentials or connection strings;
- unrestricted exception messages;
- exception stack traces that may contain sensitive information.

Errors are represented through span status and explicitly allowed error categories rather than unrestricted exception payloads.

## Log Correlation

When an OpenTelemetry span context is active, structured application logs include:

- `trace_id`;
- `span_id`.

These identifiers complement the existing Project and QuestionRun correlation identifiers.

This enables navigation between:

- exported OpenTelemetry traces;
- structured application logs;
- persistent QuestionRun and ExecutionTrace records.

OpenTelemetry does not replace the existing structured logging implementation.

## Configuration

OpenTelemetry configuration is centralized in a dedicated infrastructure module.

Telemetry is disabled by default and enabled explicitly through environment configuration.

Expected behavior by environment is:

- local development: disabled by default, optionally enabled for observability testing;
- automated tests and CI: disabled;
- Public Demo / production: enabled when valid telemetry configuration is provided.

Observability credentials and OTLP endpoint configuration are provided exclusively through environment variables and are never stored in source code.

## Export Architecture

The Public Demo exports telemetry directly from the Django application to an external OpenTelemetry-compatible backend using OTLP.

An OpenTelemetry Collector is not introduced for the initial Public Demo.

The initial monitoring backend is **Grafana Cloud Free**.

Grafana-specific dependencies must not be introduced into the application domain or Query Engine. The application depends on OpenTelemetry standards and OTLP so that the backend can be replaced later without redesigning the application.

## Sampling

The Public Demo initially samples **100% of instrumented traces** because the expected traffic is limited and complete traces provide greater diagnostic value during initial deployment.

The sampling rate remains configurable so that it can be reduced if traffic or telemetry volume increases.

## Failure Isolation

Observability is not a functional dependency of AskMyData.

Telemetry export must be non-blocking and failures in the telemetry backend must not cause:

- HTTP request failures;
- QuestionRun failures;
- Query Engine failures;
- database transaction failures.

AskMyData must remain operational when the external observability backend is unavailable or OpenTelemetry is disabled.

## Testing

Automated tests validate AskMyData's OpenTelemetry integration without contacting the external monitoring backend.

Tests cover application-owned behavior such as:

- conditional initialization;
- custom span creation;
- permitted telemetry attributes;
- operational metric emission;
- safe error representation;
- log correlation;
- failure isolation.

Tests use local or in-memory OpenTelemetry testing facilities where appropriate.

No Grafana Cloud credentials are required by the automated test suite.

---

# Rationale

OpenTelemetry provides a vendor-neutral standard for application traces and metrics.

Using OpenTelemetry enables AskMyData to demonstrate production-oriented observability practices while keeping monitoring concerns separate from the application domain.

The selected approach provides:

- standardized telemetry;
- end-to-end visibility from HTTP requests to AI pipeline operations;
- visibility into LLM latency and token usage;
- correlation between traces, logs and persistent execution records;
- compatibility with external monitoring platforms;
- portability between observability backends;
- controlled handling of sensitive information.

A selective instrumentation strategy limits implementation and maintenance complexity while preserving meaningful operational visibility.

Direct OTLP export avoids introducing an additional infrastructure component for the limited Public Demo workload.

Using a managed backend avoids operating a dedicated observability stack while still demonstrating realistic monitoring practices.

---

# Consequences

## Positive

- Standardized application telemetry.
- Improved visibility into application and AI pipeline performance.
- End-to-end request tracing.
- Dedicated visibility into LLM operations.
- Operational metrics suitable for dashboards and alerting.
- Correlation between traces, logs, QuestionRuns and ExecutionTraces.
- Vendor-neutral instrumentation.
- No additional observability infrastructure service required for the Public Demo.
- No external observability dependency during local development or CI.
- Future observability backends can be introduced without changing business logic.

## Negative

- Additional OpenTelemetry dependencies and configuration.
- Additional instrumentation code must be maintained.
- Telemetry introduces a small runtime overhead.
- Exported telemetry requires careful control to prevent sensitive-data leakage.
- Direct backend export provides less routing and processing flexibility than an OpenTelemetry Collector.
- Full trace sampling may need to be reduced if traffic increases.
- Monitoring depends on an external SaaS provider when enabled.

---

# Alternatives Considered

## Existing Logs and Persistent Execution Traces Only

AskMyData could rely exclusively on structured logs, QuestionRun metrics and ExecutionTrace records.

### Advantages

- No additional dependencies.
- No external telemetry service.
- Lower implementation complexity.

### Reasons for rejection

These mechanisms provide application-specific diagnostics but do not provide standardized distributed tracing or operational metrics suitable for external monitoring.

They would also require custom solutions to provide trace visualization and aggregated operational dashboards.

---

## Self-Hosted Observability Stack

AskMyData could deploy its own observability infrastructure using components such as Grafana, Prometheus and Tempo.

### Advantages

- Full infrastructure control.
- No dependency on a managed observability provider.
- Demonstrates additional infrastructure engineering.

### Reasons for rejection

The operational complexity is not justified for a single-developer portfolio application with limited expected traffic.

Operating several additional services would increase:

- deployment complexity;
- resource consumption;
- configuration effort;
- maintenance effort.

The portfolio objective is better served by demonstrating correct instrumentation and monitoring practices rather than operating an unnecessarily large observability platform.

---

## OpenTelemetry Collector

An OpenTelemetry Collector could be deployed between AskMyData and the monitoring backend.

### Advantages

- Centralized telemetry processing.
- Flexible routing and transformation.
- Easier support for multiple telemetry backends.
- Reduced coupling between application instances and exporters.

### Reasons for rejection

The Public Demo initially consists of a limited deployment and does not require a dedicated telemetry processing layer.

Direct OTLP export provides sufficient backend portability while keeping the deployment architecture simpler.

The Collector may be introduced later without changing application-level instrumentation.

---

## Vendor-Specific Monitoring SDK

AskMyData could integrate directly with a monitoring provider's proprietary SDK.

### Advantages

- Potentially simpler provider-specific setup.
- Access to vendor-specific features.

### Reasons for rejection

A proprietary SDK would unnecessarily couple application instrumentation to the selected monitoring provider.

OpenTelemetry provides the required tracing and metrics capabilities while preserving portability.

---

# Future Evolution

The observability architecture may evolve to include:

- an OpenTelemetry Collector;
- reduced or adaptive trace sampling;
- additional operational metrics;
- monitoring dashboards;
- alerting;
- dedicated error tracking;
- additional connector instrumentation;
- additional deployment and infrastructure telemetry;
- migration to another OTLP-compatible observability backend.

These changes should preserve the separation between application-specific persistent observability data and externally exported operational telemetry.

---

# Related Documents

- `docs/application-components.md`
- `docs/domain-model.md`
- `docs/requirements.md`
- `docs/mvp-scope.md`
- `docs/adrs/0001-modular-monolith-architecture.md`
- `docs/adrs/0004-sql-query-validation.md`