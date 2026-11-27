# Deployment Guide

## 1. Overview

This document describes how to configure, deploy, validate and maintain
AskMyData across local development, demonstration and production
environments.

AskMyData supports the following deployment configurations:

- Standard local development.
- Local Public Demo.
- Production deployment.
- Production Public Demo.

The Public Demo is the primary target of the Production-ready Portfolio
stage. It provides controlled access to predefined PostgreSQL datasets
without allowing users to configure arbitrary external data sources.

The deployment architecture relies on Docker Compose, PostgreSQL,
Gunicorn, WhiteNoise and Caddy. OpenTelemetry provides optional
integration with an external observability backend.

The local deployment configurations, individual production components
and configurable Public Demo usage limits have been validated locally.

Remote deployment, public HTTPS access, final security checks and
production validation remain to be completed before opening the
Public Demo to invited users.

This guide focuses on operational procedures. Functional requirements,
architectural decisions and dataset-specific documentation are maintained
in their respective documents.

## 2. Prerequisites

### 2.1. General Requirements

All Docker-based deployment configurations require:

- Git.
- Docker Engine or Docker Desktop.
- Docker Compose v2 with support for the `!reset` and `!override` tags
  (version 2.24.4 or later).
- Internet access to download container images and application dependencies.
- A valid OpenAI API key.
- Sufficient disk space for container images and PostgreSQL data volumes.

Python, PostgreSQL and Gunicorn do not need to be installed directly
on the host when using Docker.

### 2.2. Local Development

For development activities outside Docker, the following tools are
also required:

- Python 3.13.
- uv.

These tools support local dependency management, automated testing
and code quality checks.

### 2.3. Public Demo

Public Demo deployments additionally require:

- The four PostgreSQL dataset archives.
- Dedicated database credentials for each demonstration dataset.
- Sufficient disk space for dataset restoration and persistent storage.

Dataset preparation and licensing considerations are documented in
[Demo Datasets](demo-datasets/README.md).

### 2.4. Production Deployment

A remote production deployment additionally requires:

- A Linux server with Docker and Docker Compose installed.
- SSH access to the server.
- A public domain name pointing to the server.
- Correctly configured DNS records.
- Incoming TCP traffic permitted on ports 80 and 443.
- Outbound HTTPS access to the LLM provider and, when enabled,
  the observability backend.
- Persistent storage for PostgreSQL databases and Caddy configuration.
- A backup strategy for application data and deployment secrets.

Caddy manages HTTPS certificate provisioning and renewal.

### 2.5. Optional Observability

External telemetry export requires:

- An OTLP-compatible observability backend.
- An OTLP HTTP endpoint.
- Valid authentication credentials when required by the backend.

Grafana Cloud Free is the initial observability backend selected
for AskMyData.

OpenTelemetry remains optional and is disabled by default.

## 3. Deployment Architecture

### 3.1. Docker Compose Configurations

AskMyData uses a base Docker Compose configuration and two optional
override files.

| File | Purpose |
|---|---|
| `compose.yaml` | Standard application and PostgreSQL services |
| `compose.demo.yaml` | Public Demo datasets and configuration |
| `compose.prod.yaml` | Production application server and reverse proxy |

The files must be combined in the following order:

| Deployment | Compose files |
|---|---|
| Standard local | `compose.yaml` |
| Local Public Demo | `compose.yaml`, `compose.demo.yaml` |
| Standard production | `compose.yaml`, `compose.prod.yaml` |
| Production Public Demo | `compose.yaml`, `compose.demo.yaml`, `compose.prod.yaml` |

The Production Public Demo is the intended publicly accessible
deployment configuration.

Standard production deployment is technically supported by the
container configuration, but exposing arbitrary external data source
connections publicly is outside the current portfolio scope.

### 3.2. Services

The deployment architecture consists of the following services.

| Service | Technology | Responsibility |
|---|---|---|
| `web` | Django / Python 3.13 | Application and Query Engine |
| `db` | PostgreSQL 17 | Application database |
| `demo-db` | PostgreSQL 17 | Predefined demonstration datasets |
| `caddy` | Caddy 2 | Production reverse proxy and HTTPS |

The `demo-db` service is only included in Public Demo deployments.

The `caddy` service is only included in production deployments.

### 3.3. Application Image

The application Docker image:

- Uses Python 3.13-slim as its base image.
- Installs dependencies using uv and the committed lock file.
- Excludes development dependencies.
- Compiles French translation files.
- Collects static assets during the image build.
- Uses the Django development server by default.

The production configuration replaces the development server with
Gunicorn.

Production containers run the application code included in the
Docker image rather than mounting the host source directory.

During the image build, a temporary Fernet key is generated
to satisfy Django configuration validation when collecting
static assets.

This build-time key is independent of deployment secrets
and is not persisted as a runtime environment variable.

The runtime encryption key must be supplied through the
deployment environment.

### 3.4. Network Architecture

In local development, the application is directly accessible through
a published host port.

| Configuration | Published application port |
|---|---|
| Standard local | 8000 |
| Local Public Demo | 8001 |
| Production | None |

In production, Caddy is the public entry point and forwards requests
to Gunicorn through the internal Docker network.

```mermaid
flowchart LR
    User[User] -->|HTTPS| Caddy[Caddy]
    Caddy -->|HTTP| Web[Gunicorn / Django]
    Web --> AppDB[(Application PostgreSQL)]
    Web --> DemoDB[(Demo PostgreSQL)]
    Web -->|HTTPS| LLM[LLM Provider]
    Web -.->|OTLP HTTPS| Monitoring[Observability Backend]
```

Neither PostgreSQL service publishes a database port to the host.

The application database and demonstration databases are hosted in
separate PostgreSQL services.

### 3.5. Persistent Storage

Docker named volumes preserve state across container restarts
and recreation.

| Volume | Content |
|---|---|
| `postgres_data` | Application database |
| `demo_postgres_data` | Demonstration databases |
| `caddy_data` | Caddy data, including TLS certificates |
| `caddy_config` | Caddy configuration state |

Volume names are scoped to the Docker Compose project.

Using distinct project names allows local development and Public Demo
environments to coexist with independent databases and containers.

Removing containers does not normally remove named volumes.

Removing volumes explicitly deletes their persistent contents.

---

## 4. Environment Configuration

### 4.1. Environment File

The repository provides `.env.example` as the reference configuration.

Create a local environment file:

```bash
cp .env.example .env
```

Do not overwrite an existing `.env` file containing valid credentials.

The `.env` file contains deployment-specific configuration and secrets
and must never be committed to version control.

The structure of `.env` should remain aligned with `.env.example`
to simplify configuration maintenance.

Docker Compose uses the environment file for variable interpolation
and passes its application configuration to the web container.

Explicit service-level environment values override corresponding
values from the environment file.

### 4.2. Application and Django Settings

| Variable | Purpose |
|---|---|
| `APP_ENV` | Application environment identifier |
| `APP_DOMAIN` | Public domain used by Caddy |
| `DJANGO_SECRET_KEY` | Django cryptographic secret |
| `DJANGO_DEBUG` | Django debug mode |
| `DJANGO_ALLOWED_HOSTS` | Allowed HTTP host names |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Trusted CSRF origins |

`DJANGO_ALLOWED_HOSTS` contains comma-separated host names without
protocol prefixes.

`DJANGO_CSRF_TRUSTED_ORIGINS` contains comma-separated origins,
including their protocol.

`APP_DOMAIN` is required when using `compose.prod.yaml`.

The production Compose configuration explicitly sets:

```dotenv
APP_ENV=production
DJANGO_DEBUG=False
```

### 4.3. Application Database

| Variable | Purpose |
|---|---|
| `POSTGRES_DB` | Application database name |
| `POSTGRES_USER` | Application database user |
| `POSTGRES_PASSWORD` | Application database password |
| `DATABASE_URL` | Database connection for execution outside Docker |
| `DATABASE_URL_DOCKER` | Database connection for the web container |

For local execution outside Docker, a typical connection URL is:

```dotenv
DATABASE_URL=postgresql://askmydata:your_password@localhost:5432/askmydata
```

This requires a PostgreSQL instance accessible from the host.

For Docker-based execution:

```dotenv
DATABASE_URL_DOCKER=postgresql://askmydata:your_password@db:5432/askmydata
```

Docker Compose assigns `DATABASE_URL_DOCKER` to the application's
`DATABASE_URL` setting inside the web container.

Database credentials must be consistent across the PostgreSQL
service configuration and connection URLs.

Passwords containing reserved URL characters must be appropriately
URL-encoded in connection URLs.

### 4.4. LLM Configuration

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | OpenAI API credentials |
| `LLM_MODEL` | Model used by the Query Engine |

The default model is:

```dotenv
LLM_MODEL=gpt-5-mini
```

A valid API key is required for LLM-powered operations.

The API key must remain server-side and must never be exposed
through the user interface or committed to the repository.

### 4.5. Data Source Encryption

The `DATASOURCE_ENCRYPTION_KEY` variable must contain a valid
Fernet key.

It is used to encrypt and decrypt stored external data source
passwords.

The encryption key is validated during Django settings
initialization. An empty or invalid key prevents the application
from starting.

Startup validation verifies the key format but does not verify
whether the key matches existing encrypted credentials.

If stored credentials cannot be decrypted, the application
handles the failure as a data source configuration error.

The following operations handle this error in a controlled manner:

- Connection testing marks the data source connection as failed.
- Catalog setup redirects the user to data source configuration.
- Catalog regeneration displays a configuration error.
- Question execution records a failed run and returns a safe
  error message.

User-facing error messages do not expose encryption keys,
encrypted credentials or cryptographic exception details.

The same encryption key must be preserved across application
restarts, updates and database restorations.

Replacing the key without migrating existing encrypted credentials
makes those credentials unreadable.

See Section 12.7 for credential rotation requirements and
Section 13.10 for encryption failure troubleshooting.

### 4.6. Public Demo Configuration

| Variable | Default | Purpose |
|---|---|---|
| `PUBLIC_DEMO_MODE` | `False` | Enables Public Demo restrictions |
| `DEMO_DB_HOST` | `demo-db` | Demonstration database host |
| `DEMO_DB_PORT` | `5432` | Demonstration database port |

The Public Demo Compose configuration automatically enables
Public Demo mode and configures the demonstration database host
and port.

The following credentials are required:

| Variable | Purpose |
|---|---|
| `DEMO_DB_ADMIN_PASSWORD` | Demonstration PostgreSQL administrator |
| `DEMO_PAGILA_PASSWORD` | Pagila read-only account |
| `DEMO_EEG_PASSWORD` | EEG read-only account |
| `DEMO_OLIST_PASSWORD` | Olist read-only account |
| `DEMO_BADMINTON_PASSWORD` | Badminton read-only account |

Each account should use a distinct password.

These credentials remain exclusively server-side.

#### Public Demo Usage Limits

The following environment variables configure application and LLM
resource protection in Public Demo mode:

| Variable | Default | Purpose |
|---|---:|---|
| `DEMO_MAX_PROJECTS_PER_USER` | `5` | Maximum number of projects per user |
| `DEMO_MAX_DAILY_QUESTIONS` | `30` | Maximum daily question attempts per user |
| `DEMO_MAX_DAILY_CATALOG_BUILDS` | `10` | Maximum daily catalog generation and regeneration attempts per user |
| `DEMO_MAX_QUESTION_LENGTH` | `2000` | Maximum question length in characters |

The default configuration is:

```dotenv
DEMO_MAX_PROJECTS_PER_USER=5
DEMO_MAX_DAILY_QUESTIONS=30
DEMO_MAX_DAILY_CATALOG_BUILDS=10
DEMO_MAX_QUESTION_LENGTH=2000
```

These limits are enforced only when Public Demo mode is enabled.
Standard application mode is not subject to these restrictions.

See [Resource Protection](#116-resource-protection) for enforcement
rules and operational considerations.

### 4.7. Observability Configuration

| Variable | Default |
|---|---|
| `OTEL_ENABLED` | `False` |
| `OTEL_SERVICE_NAME` | `askmydata` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Empty |
| `OTEL_EXPORTER_OTLP_HEADERS` | Empty |
| `OTEL_TRACES_SAMPLER_ARG` | `1.0` |

See [Observability](#9-observability) for configuration instructions.

### 4.8. Integration Test Configuration

The following variables configure dedicated external PostgreSQL
sources used by integration tests:

- `TEST_SOURCE_DB_HOST`
- `TEST_SOURCE_DB_PORT`
- `TEST_SOURCE_DB_NAME`
- `TEST_SOURCE_DB_USER`
- `TEST_SOURCE_DB_PASSWORD`
- `TEST_WRITABLE_DB_USER`
- `TEST_WRITABLE_DB_PASSWORD`
- `TEST_NOSELECT_DB_USER`
- `TEST_NOSELECT_DB_PASSWORD`

These settings are intended for testing only.

Integration tests must never use production databases or personal
data sources.

### 4.9. Secret Generation

Generate independent secrets for each deployment environment.

When Python and the project dependencies are available locally,
generate a Django secret key using:

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Generate a Fernet encryption key using:

```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Generate a random database password using:

```bash
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

Repeat the password generation command for each database account.

Alternatively, after building the application image, the same
commands can be executed inside a temporary application container.

Store the generated values in the deployment environment file.

Do not reuse development credentials in production.

Secrets must not be included in documentation, screenshots,
application logs or shared command outputs.

---

## 5. Standard Local Deployment

### 5.1. Repository Setup

Clone the repository:

```bash
git clone https://github.com/MarinePernici/AskMyData.git
cd AskMyData
```

Create `.env` from `.env.example` and configure the required values
as described in Section 4.

Use the following local settings:

```dotenv
APP_ENV=development
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=
PUBLIC_DEMO_MODE=False
```

OpenTelemetry can remain disabled.

### 5.2. Start the Application

Validate the Compose configuration:

```bash
docker compose --env-file .env \
  -p askmydata \
  -f compose.yaml \
  config --quiet
```

Build and start the services:

```bash
docker compose --env-file .env \
  -p askmydata \
  -f compose.yaml \
  up -d --build
```

Initialize the application database and create an administrator
as described in Section 8.

### 5.3. Access the Application

The application is available at:

```text
http://localhost:8000/
```

The Django administration interface is available at:

```text
http://localhost:8000/admin/
```

Standard local mode allows users to configure external PostgreSQL
data sources.

### 5.4. Stop the Environment

```bash
docker compose --env-file .env \
  -p askmydata \
  -f compose.yaml \
  down
```

Persistent database volumes are preserved.

---

## 6. Local Public Demo Deployment

### 6.1. Dataset Archives

The Public Demo requires the following directory structure:

```text
backups/
└── demo-db/
    ├── pagila.sql.gz
    ├── eeg_demo.sql.gz
    ├── olist.sql.gz
    └── badminton.sql.gz
```

The archives are compressed PostgreSQL SQL dumps.

They are not distributed through the public Git repository.

Dataset preparation, provenance and licensing considerations
are documented in [Demo Datasets](demo-datasets/README.md).

All four archives must be available before the demonstration
database service is initialized.

### 6.2. Dataset Configuration

| Dataset | Database | Read-only role |
|---|---|---|
| Pagila | `pagila` | `pagila_readonly` |
| EEG | `askmydata_eeg_public_demo` | `eeg_demo_readonly` |
| Olist | `olist` | `olist_readonly` |
| Badminton | `badminton` | `badminton_readonly` |

The dataset registry is defined in:

```text
src/config/demo_datasets.py
```

The application resolves dataset connection parameters server-side
using this registry and the configured environment variables.

Users cannot supply arbitrary connection parameters in Public Demo mode.

### 6.3. Database Initialization

The demonstration database service mounts:

- `scripts/demo-db/init.sh` as a PostgreSQL initialization script.
- `backups/demo-db/` as a read-only archive directory.

During the first initialization, the script:

1. Checks that all required archives exist and are not empty.
2. Validates their gzip integrity.
3. Creates the demonstration databases.
4. Creates dedicated database roles.
5. Restores each dataset.
6. Revokes unnecessary public privileges.
7. Grants database connection and table read permissions to the
   corresponding read-only role.

The initialization script runs only when the PostgreSQL data
directory is empty.

Restarting an existing container does not restore the datasets.

Changing passwords in `.env` does not automatically update
existing PostgreSQL roles.

### 6.4. Start the Public Demo

Configure the demonstration database credentials in `.env`.

Validate the Compose configuration:

```bash
docker compose --env-file .env \
  -p askmydata-public-demo \
  -f compose.yaml \
  -f compose.demo.yaml \
  config --quiet
```

Build and start the services:

```bash
docker compose --env-file .env \
  -p askmydata-public-demo \
  -f compose.yaml \
  -f compose.demo.yaml \
  up -d --build
```

The initial dataset restoration may take longer than subsequent
container startups.

Inspect the demonstration database initialization logs:

```bash
docker compose --env-file .env \
  -p askmydata-public-demo \
  -f compose.yaml \
  -f compose.demo.yaml \
  logs --tail 100 demo-db
```

Successful initialization ends with:

```text
Demo databases initialized successfully.
```

Initialize the application database and create an administrator
as described in Section 8.

### 6.5. Access the Public Demo

The application is available at:

```text
http://localhost:8001/
```

The administration interface is available at:

```text
http://localhost:8001/admin/
```

The Public Demo uses the normal application workflow with
predefined PostgreSQL data sources.

Access to application features requires an authorized user account.

### 6.6. Environment Isolation

The project name `askmydata-public-demo` separates the demonstration
environment from the standard local environment.

Both environments can run simultaneously:

- Standard local application: port 8000.
- Local Public Demo: port 8001.

Their application databases and persistent volumes are independent.

### 6.7. Stop the Public Demo

```bash
docker compose --env-file .env \
  -p askmydata-public-demo \
  -f compose.yaml \
  -f compose.demo.yaml \
  down
```

The application database and restored datasets are preserved.

---

## 7. Production Deployment

### 7.1. Deployment Status

The production container configuration has been prepared and its
individual components have been validated locally.

Remote deployment, public DNS resolution, real HTTPS certificate
provisioning and complete production validation remain pending.

The procedures in this section describe the intended deployment
process and must be validated on the selected server.

The Public Demo must not be opened to invited users until the
remaining security requirements have been addressed and the
implemented resource protection mechanisms have been validated
in the production environment.

### 7.2. Server Preparation

Prepare a Linux server with Docker and Docker Compose installed.

The server must provide:

- Persistent storage.
- Secure administrative access.
- Network access to required external services.
- Sufficient resources for the application and PostgreSQL services.

The hosting provider and server sizing remain to be determined.

Clone the repository on the server and check out the intended
deployment revision.

Use a reviewed and tested Git revision rather than deploying
unverified development changes.

### 7.3. Production Environment

Create a dedicated production `.env` file.

Generate independent production secrets and configure the required
database and LLM credentials.

A typical production configuration includes:

```dotenv
APP_ENV=production
APP_DOMAIN=demo.example.com

DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=demo.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://demo.example.com

PUBLIC_DEMO_MODE=True
```

Replace `demo.example.com` with the actual deployment domain.

The domain must be consistent across:

- `APP_DOMAIN`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- DNS configuration

Restrict access to the environment file:

```bash
chmod 600 .env
```

Prepare and securely transfer the required demonstration dataset
archives before starting the demonstration database service.

### 7.4. DNS and Network Configuration

Configure the deployment domain to resolve to the server.

Allow incoming TCP connections on ports 80 and 443.

Do not expose PostgreSQL ports or the internal Gunicorn port
to the public network.

Ensure that administrative access to the server is appropriately
restricted.

### 7.5. Production Application Server

The production configuration runs Gunicorn with:

- WSGI application: `config.wsgi:application`.
- Internal bind address: `0.0.0.0:8000`.
- Workers: 2.
- Worker timeout: 120 seconds.

These values represent the initial deployment configuration.

Worker count and timeout settings may be adjusted after observing
application behavior and server resource consumption.

The development source-code mount is removed in production.

WhiteNoise serves the static files collected during the image build.

### 7.6. Reverse Proxy and HTTPS

Caddy is configured through:

```text
deploy/caddy/Caddyfile
```

It:

- Accepts requests for the configured public domain.
- Manages HTTPS certificate provisioning and renewal.
- Redirects public HTTP requests to HTTPS.
- Forwards requests to the internal Gunicorn service.
- Supports response compression.

Caddy is the only application service publishing HTTP and HTTPS
ports to the host.

Django trusts the `X-Forwarded-Proto` header provided by the
reverse proxy.

### 7.7. Build and Initialize Production Services

Validate the combined Compose configuration:

```bash
docker compose --env-file .env \
  -p askmydata-production \
  -f compose.yaml \
  -f compose.demo.yaml \
  -f compose.prod.yaml \
  config --quiet
```

Build the application image:

```bash
docker compose --env-file .env \
  -p askmydata-production \
  -f compose.yaml \
  -f compose.demo.yaml \
  -f compose.prod.yaml \
  build web
```

Start the database services:

```bash
docker compose --env-file .env \
  -p askmydata-production \
  -f compose.yaml \
  -f compose.demo.yaml \
  -f compose.prod.yaml \
  up -d db demo-db
```

Wait for the database services to become healthy and confirm
that demonstration dataset restoration has completed.

Apply application database migrations:

```bash
docker compose --env-file .env \
  -p askmydata-production \
  -f compose.yaml \
  -f compose.demo.yaml \
  -f compose.prod.yaml \
  run --rm web python manage.py migrate
```

Create the initial administrator account:

```bash
docker compose --env-file .env \
  -p askmydata-production \
  -f compose.yaml \
  -f compose.demo.yaml \
  -f compose.prod.yaml \
  run --rm web python manage.py createsuperuser
```

Run the Django deployment checks:

```bash
docker compose --env-file .env \
  -p askmydata-production \
  -f compose.yaml \
  -f compose.demo.yaml \
  -f compose.prod.yaml \
  run --rm web python manage.py check --deploy
```

Review all reported issues before exposing the application.

### 7.8. Start the Production Application

Once database initialization and pre-deployment checks are complete:

```bash
docker compose --env-file .env \
  -p askmydata-production \
  -f compose.yaml \
  -f compose.demo.yaml \
  -f compose.prod.yaml \
  up -d
```

Inspect the service status:

```bash
docker compose --env-file .env \
  -p askmydata-production \
  -f compose.yaml \
  -f compose.demo.yaml \
  -f compose.prod.yaml \
  ps
```

Inspect Caddy logs to verify HTTPS certificate provisioning.

The application should then be accessible through:

```text
https://demo.example.com/
```

Replace the example domain with the actual deployment domain.

Complete the validation procedures in Section 10 before granting
access to invited users.

### 7.9. Known Production Configuration Limitations

HTTP Strict Transport Security (HSTS) is currently disabled.

HSTS activation must be reviewed after successful validation of
the public HTTPS deployment.

The production email backend intentionally discards outgoing emails.

Automated email delivery is not part of the current Public Demo
scope. Administrators generate and share invitation links manually.

These settings may produce findings during Django deployment checks.

They must be reviewed explicitly rather than ignored globally.

---

## 8. Application Initialization

### 8.1. Database Migrations

Django migrations initialize and update the application database schema.

For standard local deployment:

```bash
docker compose --env-file .env \
  -p askmydata \
  -f compose.yaml \
  exec web python manage.py migrate
```

For local Public Demo deployment:

```bash
docker compose --env-file .env \
  -p askmydata-public-demo \
  -f compose.yaml \
  -f compose.demo.yaml \
  exec web python manage.py migrate
```

Production migrations should be applied before making the updated
application available to users.

Database backups should be created before applying migrations
to an existing production database.

### 8.2. Administrator Account

Create an administrator using Django's standard management command.

For standard local deployment:

```bash
docker compose --env-file .env \
  -p askmydata \
  -f compose.yaml \
  exec web python manage.py createsuperuser
```

For local Public Demo deployment:

```bash
docker compose --env-file .env \
  -p askmydata-public-demo \
  -f compose.yaml \
  -f compose.demo.yaml \
  exec web python manage.py createsuperuser
```

The command interactively requests the administrator credentials.

Use a strong, unique password.

An administrator account only needs to be created once for each
independent application database.

### 8.3. Public Demo Access Management

The Public Demo uses controlled, invitation-based access.

Administrators can manage access requests and invitations through
the administration interface.

Invitation links are generated by the application and manually
shared with approved users.

Automated email delivery is not required.

User access should only be granted after the deployment has
passed the required security and functional validation checks.

---

## 9. Observability

### 9.1. Overview

AskMyData combines:

- Structured JSON application logs.
- Persistent QuestionRun metrics.
- Persistent ExecutionTrace records.
- Health endpoints.
- Optional OpenTelemetry traces and operational metrics.

OpenTelemetry complements the application-specific observability
mechanisms without replacing them.

OpenTelemetry instrumentation is intentionally restricted to
application-controlled spans covering QuestionRun execution,
Query Engine steps and LLM calls.

Automatic Django HTTP and PostgreSQL instrumentation is
disabled to reduce the risk of sensitive-data exposure.

The architectural decision is documented in
[ADR-0005](adrs/0005-opentelemetry-observability.md).

### 9.2. Enable OpenTelemetry

Configure the following environment variables:

```dotenv
OTEL_ENABLED=True
OTEL_SERVICE_NAME=askmydata
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-otlp-endpoint
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic%20your-credentials
OTEL_TRACES_SAMPLER_ARG=1.0
```

Use the OTLP endpoint and authentication credentials supplied
by the selected observability backend.

The endpoint must represent the base OTLP HTTP endpoint.

AskMyData automatically appends:

- `/v1/traces`
- `/v1/metrics`

Do not include these signal-specific suffixes in the configured
base endpoint.

Authentication headers are configured as comma-separated
key-value pairs.

URL-encoded header values are decoded by the application.

### 9.3. Grafana Cloud

Grafana Cloud Free is the initial observability backend.

The application exports traces and metrics directly through
OTLP over HTTP, using HTTPS for the external endpoint.

An OpenTelemetry Collector is not required.

Grafana Cloud credentials must be stored exclusively in the
deployment environment configuration.

The service name can be adjusted to distinguish development
and production telemetry.

### 9.4. Exported Metrics

The initial application metrics are:

| Metric | Type | Attributes |
|---|---|---|
| `askmydata.question_runs` | Counter | Status |
| `askmydata.question_run.duration` | Histogram | Status |
| `askmydata.llm.tokens` | Counter | Token type, model |
| `askmydata.pipeline_step.duration` | Histogram | Pipeline step |

Duration measurements are expressed in milliseconds.

Traces are exported using a batch span processor.

Metrics are exported periodically using the OpenTelemetry SDK's
periodic metric reader.

The default metric export interval is 60 seconds unless overridden
through supported SDK configuration.

### 9.5. Trace Sampling

The trace sampling ratio is configured through:

```dotenv
OTEL_TRACES_SAMPLER_ARG=1.0
```

A value of `1.0` samples all instrumented traces.

The ratio may be reduced if traffic or telemetry volume increases.

### 9.6. Validate Telemetry

After enabling telemetry:

1. Rebuild and recreate the application container with the updated configuration.
2. Sign in and open a configured project.
3. Execute a valid natural-language question.
4. Wait for telemetry export.
5. Verify that QuestionRun, Query Engine and LLM spans appear in the observability backend.
6. Verify that application metrics are available.
7. Check that correlation identifiers are present where expected.
8. Verify that exported application span attributes are restricted to the approved allowlist.
9. Verify that automatic HTTP and PostgreSQL query spans are not exported.
10. Inspect exported telemetry for unexpected sensitive information.

Application logs should also be inspected for telemetry
configuration or export errors.

Telemetry must remain optional and must not prevent normal
application execution when the external backend is unavailable.

The revised privacy-oriented instrumentation has been validated
locally using Docker and Grafana Cloud.

Validation confirmed:

- Successful export of application-controlled spans.
- Correct QuestionRun and Query Engine span hierarchy.
- Absence of automatic HTTP and PostgreSQL spans in the inspected trace.
- Compliance of inspected span attributes with the application allowlist.
- Availability of all four application metrics.
- Correlation between application logs and OpenTelemetry spans.

Production telemetry export with Gunicorn workers remains
to be validated on the target deployment.

---

## 10. Health Checks and Validation

### 10.1. Health Endpoints

AskMyData provides two health endpoints.

| Endpoint | Purpose |
|---|---|
| `/health/live/` | Application process availability |
| `/health/ready/` | Application database connectivity |

A successful response is:

```json
{"status": "ok"}
```

The readiness endpoint executes a lightweight `SELECT 1` query
against the application database.

If the database is unavailable, it returns HTTP 503:

```json
{"status": "unavailable"}
```

The readiness endpoint does not verify the availability of
external data sources, demonstration datasets, the LLM provider
or the observability backend.

### 10.2. Docker Health Checks

The PostgreSQL services use `pg_isready` to verify database
server availability.

The web service checks the application readiness endpoint.

In production, the internal web healthcheck includes:

- A `Host` header matching `APP_DOMAIN`.
- An `X-Forwarded-Proto: https` header.

This allows the internal healthcheck to operate without disabling
Django's HTTPS redirection or adding exceptions to the public
security configuration.

The production healthcheck has been validated locally with
Gunicorn and PostgreSQL.

It does not validate Caddy or the public TLS certificate.

### 10.3. Service Status

Inspect the running containers using:

```bash
docker compose ps
```

When using a named deployment, include the corresponding
project name and Compose files.

The web and PostgreSQL services should report a healthy status.

A healthy PostgreSQL service does not necessarily guarantee
that every demonstration dataset was restored successfully.

Dataset initialization logs and functional queries must also
be checked.

### 10.4. Public HTTPS Validation

After remote deployment, verify the public endpoints:

```bash
curl -I http://demo.example.com/
```

The HTTP request should redirect to HTTPS.

```bash
curl -I https://demo.example.com/
```

The HTTPS request should succeed with a valid certificate.

Verify application readiness:

```bash
curl --fail https://demo.example.com/health/ready/
```

Replace the example domain with the actual deployment domain.

Do not disable TLS certificate verification when validating
the public production deployment.

### 10.5. Functional Validation

Before opening the Public Demo, verify:

- Public landing page availability.
- Static asset loading.
- English and French interface translations.
- Administrator authentication.
- Access request submission.
- Access request approval and rejection.
- Invitation generation.
- Registration using a valid invitation.
- Rejection of invalid or expired invitations.
- User authentication and logout.
- Project creation.
- Selection of each available demonstration dataset.
- Automatic connection configuration.
- Catalog scope selection.
- Knowledge Catalog generation.
- Schema exploration.
- Natural-language question execution.
- SQL validation and read-only execution.
- Conversation history.
- User and project access isolation.
- Controlled error handling.
- Configured resource limit enforcement.

### 10.6. Automated Tests

Run automated tests against a dedicated local test environment.

For the complete standard application test suite:

```bash
docker compose --env-file .env \
  -p askmydata \
  -f compose.yaml \
  exec web python manage.py test
```

The complete standard application test suite can also be executed
from the local Public Demo environment by disabling Public Demo
mode for the test process:

```bash
docker compose --env-file .env \
  -p askmydata-public-demo \
  -f compose.yaml \
  -f compose.demo.yaml \
  exec -e PUBLIC_DEMO_MODE=False web \
  python manage.py test
```

Tests requiring an external PostgreSQL source must use a
dedicated integration test database.

For Public Demo-specific tests:

```bash
docker compose --env-file .env \
  -p askmydata-public-demo \
  -f compose.yaml \
  -f compose.demo.yaml \
  exec web python manage.py test \
  config.tests.test_demo_datasets \
  apps.data_sources.tests.test_demo_views \
  apps.authentication.tests.test_usage_limits
```

Usage limit integration tests are included in the complete test
suite and explicitly enable Public Demo mode through Django
test settings.

The automated tests cover:

- Public Demo dataset configuration and access restrictions.
- Usage limit enforcement and daily counter persistence.
- User-level quota isolation.
- Daily quota renewal.
- Standard mode compatibility.
- Project creation restrictions.
- Question length validation.
- Question execution restrictions.
- Catalog generation and regeneration restrictions.
- Accounting for failed execution attempts.

LLM services are mocked in usage limit integration tests to avoid
external API calls and unnecessary token consumption.

Do not execute the automated test suite against a production
deployment.

### 10.7. Pre-Release Validation

Before granting public demonstration access, confirm that:

- The intended Git revision has been reviewed.
- Automated tests pass.
- Code quality checks pass.
- Dependency security findings have been reviewed.
- No secrets are included in the repository.
- Independent production secrets have been generated.
- The runtime Fernet encryption key is valid and securely backed up.
- Existing encrypted credentials remain readable after application
  updates, when applicable.
- All required services are operational.
- Database migrations are applied.
- HTTPS is correctly configured.
- Dataset access permissions are restricted.
- Application access is invitation-based.
- Resource protection mechanisms are implemented and validated.
- Dataset reuse and exposure conditions have been reviewed.
- Backup and recovery procedures are available.
- Observability is operational when enabled.

---

## 11. Security Considerations

### 11.1. Secret Management

Deployment secrets must remain outside version control.

Use independent credentials for development and production.

Restrict access to environment files, database backups and
encryption keys.

Do not expose secrets through logs, telemetry, screenshots
or diagnostic command outputs.

### 11.2. Database Isolation

The application database and demonstration databases are hosted
in separate PostgreSQL services.

Each demonstration dataset has a dedicated database account
with restricted permissions.

The application Query Engine must not query the application
database as a user-configured data source.

PostgreSQL services must not publish ports to the public network.

### 11.3. Controlled SQL Execution

Database-level read-only permissions complement the application
SQL validation mechanisms.

Generated SQL must be validated before execution.

Public Demo queries must remain restricted to the selected
dataset and authorized catalog scope.

The application must reject unsupported or unsafe SQL operations.

### 11.4. Public Demo Restrictions

Public Demo mode restricts data source configuration to predefined
demonstration datasets.

Connection credentials and dataset resolution remain server-side.

Arbitrary external database connections are not supported in
the Public Demo.

Access to application features requires an authorized account.

### 11.5. HTTPS and Django Security

Production configuration enables:

- Disabled Django debug mode.
- Secure session cookies.
- Secure CSRF cookies.
- HTTPS redirection.
- Explicit allowed hosts.
- Explicit trusted CSRF origins.
- Reverse proxy SSL header handling.

HSTS activation remains pending validation of the remote HTTPS
deployment.

The internal Gunicorn service must remain inaccessible directly
from the public network.

### 11.6. Resource Protection

The Public Demo implements configurable protections against
excessive application and LLM resource consumption.

#### Application Usage Limits

| Resource | Default limit | Scope |
|---|---:|---|
| Projects | 5 | Per user |
| Questions | 30 | Per user, per day |
| Catalog generations and regenerations | 10 | Per user, per day |
| Question length | 2000 characters | Per question |

All limits are configurable through environment variables.

See [Public Demo Configuration](#46-public-demo-configuration).

#### Project Limit

All existing projects owned by a user count towards the project
limit, including incomplete, active and archived projects.

Deleting an incomplete project releases a project slot.

Archiving a project does not release a project slot.

Project creation is protected by a database transaction and
a user-level row lock to prevent concurrent requests from
exceeding the configured project limit.

#### Daily Usage Accounting

Daily question and catalog usage counters are persisted in the
application PostgreSQL database through the `DailyUsage` model.

Each record is associated with a user and a calendar date.

Daily quotas renew at midnight UTC. Historical usage records
are retained.

Catalog generation and regeneration share the same daily quota.

Usage is counted across all projects and conversations owned
by the user.

Deleting an incomplete project does not reset daily usage.

#### Enforcement

Usage limits are checked server-side before invoking the
corresponding execution services.

Daily usage reservations use atomic database updates to prevent
concurrent requests from exceeding the configured quotas.

Execution attempts are counted even when the subsequent operation
fails, as failed operations may already have consumed application
or LLM resources.

Questions exceeding the configured maximum length are rejected
before reserving daily question usage.

When a limit is reached, the operation is rejected and the user
receives a localized error message.

These restrictions apply exclusively to Public Demo mode.

#### Database Query Constraints

The existing SQL execution protections remain active:

- SQL validation before execution.
- Read-only database access.
- Catalog scope enforcement.
- Query execution timeout of 30 seconds.
- Maximum returned result size of 1000 rows.

#### Administration and Monitoring

Daily usage records can be inspected through the Django
administration interface by authorized superusers.

The administration interface provides read-only access to
question and catalog usage counters.

OpenTelemetry metrics provide additional visibility into LLM
token consumption and execution performance when enabled.

#### OpenAI Cost Protection

The production Public Demo should use a dedicated OpenAI project
and API key, separate from development credentials.

Budget alerts and provider-side usage monitoring should be
configured before opening the demonstration to invited users.

Application usage limits reduce the risk of excessive API
consumption but do not guarantee a global monetary spending cap.

OpenAI project budget alerts must not be treated as hard
spending limits.

#### Validation Status

Usage limit enforcement has been validated locally through
automated unit and integration tests.

Final configuration and operational validation must be performed
in the production environment before opening the Public Demo
to invited users.

### 11.7. Dataset Governance

Demonstration datasets must be reviewed for:

- Data provenance.
- Licensing and reuse conditions.
- Personal or sensitive information.
- Suitability for public demonstration.

Invitation-based access does not replace the need to verify
dataset reuse rights.

Dataset-specific considerations are documented in
[Demo Datasets](demo-datasets/README.md).

### 11.8. Telemetry Privacy

Telemetry must not export user questions, generated answers,
SQL queries, prompts, query results, credentials or other
sensitive application content.

Automatic Django HTTP and PostgreSQL instrumentation is
intentionally disabled.

Application span attributes are restricted through an explicit
allowlist enforced during span creation and attribute updates.

The permitted application span attributes are:

- `project_id`;
- `question_run_id`;
- `pipeline_step`;
- `llm.operation`;
- `llm.model`;
- `error.type`.

Attribute values and span names must remain controlled by
application code and must not contain user-provided content.

Operational metrics are restricted to technical dimensions
and numerical measurements.

Exceptions are represented through span status and exception
type without exporting raw exception messages or stack traces.

Structured application logs also apply confidentiality
protections:

- Invitation tokens are redacted from logged registration URLs.
- Exception details are replaced with exception types.
- Django logs use the centralized JSON formatter.
- SQL and third-party library logging verbosity is restricted.
- Gunicorn and Caddy access logging is not enabled.

These protections reduce the risk of sensitive-data exposure
but do not constitute a generic data-loss prevention mechanism.

Telemetry privacy and production logging must be validated
before opening the Public Demo to invited users.

---

## 12. Maintenance

### 12.1. Application Updates

Application updates should follow a controlled deployment process:

1. Select a reviewed and tested Git revision.
2. Back up the application database and required configuration.
3. Update the application source.
4. Review changes to `.env.example`.
5. Update the deployment environment when required.
6. Rebuild the application image.
7. Apply database migrations.
8. Recreate the application container.
9. Verify service health and application functionality.

Production updates may require a maintenance window.

The current Docker Compose architecture does not provide
zero-downtime deployment guarantees.

### 12.2. Rebuild Application Images

Rebuilding the application image is required when dependencies,
Docker build instructions or production application files change.

For standard local deployment:

```bash
docker compose --env-file .env \
  -p askmydata \
  -f compose.yaml \
  up -d --build
```

For production, use the complete production Compose configuration.

Restarting an existing container does not install newly added
Python dependencies.

In local development, source-code changes may be visible through
the mounted repository while installed dependencies remain
unchanged until the image is rebuilt.

### 12.3. Environment Changes

Changes to `.env` may require container recreation.

A container restart alone does not necessarily reload its
environment configuration.

Recreate the affected services using the corresponding
Docker Compose configuration.

Changes to PostgreSQL initialization credentials require
additional care because existing database roles are not
automatically updated.

### 12.4. Application Database Backups

The application database contains persistent platform state,
including user accounts, projects, catalogs, conversations,
invitations and execution history.

Regular backups are required for production deployments.

A PostgreSQL custom-format backup can be created using `pg_dump`.

Example for the production Public Demo:

```bash
mkdir -p backups/application-db
chmod 700 backups/application-db
umask 077

docker compose --env-file .env \
  -p askmydata-production \
  -f compose.yaml \
  -f compose.demo.yaml \
  -f compose.prod.yaml \
  exec -T db sh -c \
  'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  > "backups/application-db/askmydata-$(date -u +%Y%m%dT%H%M%SZ).dump"
```

Verify that the command completes successfully and that the
resulting backup is valid.

Backups must be stored securely and protected from unauthorized
access.

Database backups do not include the deployment environment file
or encryption keys.

These must be preserved separately through a secure backup process.

The backup frequency, retention policy and off-site storage
strategy remain to be defined for the remote deployment.

### 12.5. Database Recovery

Application database recovery requires:

- A valid PostgreSQL backup.
- A compatible PostgreSQL environment.
- The corresponding application revision or compatible schema.
- The original data source encryption key.
- Required deployment configuration and credentials.

PostgreSQL custom-format backups can be restored using `pg_restore`.

Restoration must first be tested against an isolated database.

The production recovery procedure must be validated before
the Public Demo is opened to users.

Do not restore an unverified backup directly over an active
production database.

### 12.6. Demonstration Dataset Maintenance

Demonstration datasets are intended to remain read-only during
normal application operation.

The original dataset archives should be preserved securely
so that the demonstration database service can be reconstructed.

Updating a dataset archive does not automatically update
an existing PostgreSQL database.

Dataset updates require a controlled restoration or migration
procedure.

Existing projects and Knowledge Catalogs may require regeneration
if the dataset schema changes.

### 12.7. Credential Rotation

Database passwords, API keys and observability credentials
should be rotated when required.

Updating PostgreSQL passwords requires changing the corresponding
database roles and application configuration consistently.

The Fernet encryption key must not be replaced without a
procedure for migrating existing encrypted credentials.

Django secret key rotation must account for its effects on
existing sessions and signed application data.

### 12.8. Logs

Inspect application logs using:

```bash
docker compose logs --tail 100 web
```

Follow logs in real time using:

```bash
docker compose logs -f web
```

Use the appropriate project name and Compose files for the
target environment.

Production log retention and rotation must be configured
according to the available server resources and operational needs.

### 12.9. Stop and Remove Services

Use `docker compose down` with the appropriate deployment
configuration to stop and remove containers.

Named volumes are preserved by default.

The following option explicitly removes persistent volumes:

```text
docker compose down -v
```

This operation is destructive and must not be used against
production or persistent development environments unless
data deletion is intentional and verified backups are available.

---

## 13. Troubleshooting

### 13.1. Invalid Docker Compose Configuration

Validate the configuration using:

```bash
docker compose config --quiet
```

Include the required project name, environment file and Compose
override files.

Check that all mandatory environment variables are defined.

Avoid sharing unrestricted `docker compose config` output because
it may contain resolved secrets.

### 13.2. Application Container Is Unhealthy

Inspect the container healthcheck history:

```bash
docker inspect <container-name> \
  --format '{{range .State.Health.Log}}{{println .ExitCode .Output}}{{end}}'
```

Inspect application logs:

```bash
docker logs --tail 100 <container-name>
```

Possible causes include:

- Application startup failure.
- Missing Python dependencies.
- Invalid environment configuration.
- Database connectivity failure.
- Incorrect allowed host configuration.
- Incorrect production HTTPS healthcheck configuration.

### 13.3. Missing Python Dependencies

A development container may use updated source code while
retaining dependencies installed in an older Docker image.

An error such as:

```text
ModuleNotFoundError: No module named 'whitenoise'
```

indicates that the required dependency is not available in
the running application environment.

Rebuild and recreate the application container using the
appropriate Compose configuration.

### 13.4. Database Authentication Failure

Verify that:

- PostgreSQL credentials are consistent with the connection URL.
- The correct database host is configured.
- The required database role exists.
- The role password matches the configured application password.
- Reserved URL characters are correctly encoded.

Remember that PostgreSQL initialization environment variables
do not automatically modify existing database roles.

### 13.5. Demonstration Dataset Initialization Failure

Inspect the `demo-db` service logs.

Verify that:

- All four required archives exist.
- The archives are not empty.
- The gzip files are valid.
- The archive directory is mounted correctly.
- Required passwords are configured.
- Sufficient disk space is available.

A failed initialization may leave a partially initialized
PostgreSQL data directory.

Restarting the service may not execute the initialization
script again.

Inspect the existing database state before attempting recovery.

If rebuilding the demonstration database volume is necessary,
first confirm that the correct volume has been identified and
that no required data will be lost.

Do not remove the application database volume.

### 13.6. HTTPS or Reverse Proxy Failure

Inspect Caddy logs and verify:

- The configured domain.
- DNS resolution.
- Availability of ports 80 and 443.
- Firewall configuration.
- Certificate provisioning.
- Internal connectivity to the web service.
- Django allowed hosts.
- Django trusted CSRF origins.

The production application must remain behind the reverse proxy.

Do not disable Django HTTPS protections as a workaround.

### 13.7. Static Files Not Available

Verify that:

- The production image was rebuilt after static asset changes.
- `collectstatic` completed successfully during the build.
- WhiteNoise is installed.
- The static file storage configuration is valid.
- The production configuration does not mount the development
  source directory over the application image.

### 13.8. OpenTelemetry Data Not Available

Verify:

- `OTEL_ENABLED` is set to `True`.
- The OTLP base endpoint is correct.
- Authentication headers are valid.
- The service name matches the expected backend filters.
- The trace sampling ratio is greater than zero.
- Outbound HTTPS connectivity is available.
- Application operations have generated telemetry.
- Sufficient time has elapsed for batch and periodic exports.

Inspect application logs for telemetry initialization and
export failures.

Telemetry failures must not be resolved by exposing sensitive
credentials in diagnostic output.

### 13.9. LLM Request Failure

Verify that:

- The configured API key is valid.
- The selected model is available to the configured account.
- The account has sufficient API access and usage capacity.
- Outbound connectivity to the LLM provider is available.
- Application resource limits have not been exceeded.

Inspect application logs and QuestionRun execution records
for diagnostic information.

Do not expose API keys, prompts or user data when sharing
diagnostic information.

### 13.10. Data Source Encryption Failure

An application startup error such as:

```text
ImproperlyConfigured: DATASOURCE_ENCRYPTION_KEY must be a valid Fernet key.
```

indicates that the configured encryption key is empty or invalid.

Verify that:

- The encryption key is defined in the deployment environment.
- The configured value is a valid Fernet key.
- The correct environment configuration is loaded.

A valid Fernet key does not guarantee that existing encrypted
credentials can be decrypted.

If the application starts but reports data source configuration
errors, verify that the original encryption key has been preserved
and that the stored encrypted credentials have not been corrupted.

If the encryption key has been changed unintentionally:

1. Restore the original encryption key from a secure backup.
2. Recreate the application container using the appropriate
   Compose configuration.
3. Verify application startup and service health.
4. Test the affected data source connections.
5. Verify catalog access and question execution.

Do not generate a replacement encryption key as a troubleshooting
step when existing encrypted credentials must remain accessible.

If the original key is permanently lost, the affected encrypted
credentials cannot be recovered through decryption. The affected
data source credentials must be configured again through an
appropriate recovery procedure.

Never include encryption keys, plaintext passwords or encrypted
credential values in diagnostic output.

---

## 14. Related Documentation

- [Project README](../README.md)
- [French README](../README.fr.md)
- [Product Vision](product-vision.md)
- [Requirements](requirements.md)
- [Functional Use Cases](functional-use-cases.md)
- [MVP and Production-ready Scope](mvp-scope.md)
- [Domain Model](domain-model.md)
- [Application Components](application-components.md)
- [Architecture Decision Records](adrs/README.md)
- [OpenTelemetry Observability ADR](adrs/0005-opentelemetry-observability.md)
- [Demo Datasets](demo-datasets/README.md)
- [MVP Quality Benchmark](benchmark/mvp-quality-benchmark.md)
