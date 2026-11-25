# Demo Datasets

AskMyData uses four PostgreSQL datasets to demonstrate natural-language querying, SQL generation, schema exploration, and relational data analysis.

The datasets cover different domains, data structures, and analytical use cases.

## Available datasets

| Dataset | Domain | Description | Documentation |
|---|---|---|---|
| EEG | Scientific / healthcare | Synthetic EEG-related data for exploring scientific measurements and associated records | [EEG](eeg.md) |
| Pagila | Film rental | PostgreSQL sample database representing a DVD rental business | [Pagila](pagila.md) |
| Olist | E-commerce | Brazilian e-commerce dataset covering orders, customers, products, payments, and deliveries | [Olist](olist.md) |
| Badminton | Sports | International badminton match results, tournaments, players, and scores | [Badminton](badminton.md) |

## Architecture

The demo datasets are stored in four separate PostgreSQL databases.

| Database | Read-only role | Backup archive |
|---|---|---|
| `askmydata_eeg_public_demo` | `eeg_demo_readonly` | `eeg_demo.sql.gz` |
| `pagila` | `pagila_readonly` | `pagila.sql.gz` |
| `olist` | `olist_readonly` | `olist.sql.gz` |
| `badminton` | `badminton_readonly` | `badminton.sql.gz` |

Each database is available as an independent, predefined data source in AskMyData when Public Demo mode is enabled.

The demonstration databases are hosted in a dedicated PostgreSQL container, separate from the application database service.

## Public Demo dataset scope

The four datasets listed above have been selected for the initial AskMyData Public Demo.

The Badminton dataset is included despite the absence of an explicit reuse license. This is a documented project decision, not a claim of legal authorization.

Access to the demo will be restricted to invited users. Original source files and database dumps will not be distributed through the public Git repository.

See [Badminton](badminton.md) for provenance, limitations, and licensing considerations.

## Database initialization

The initialization script is located at:

`scripts/demo-db/init.sh`

It is designed to run through the official PostgreSQL Docker image initialization mechanism, when the PostgreSQL data directory is empty.

The script:

1. Checks that the four compressed SQL archives exist and pass gzip integrity checks.
2. Creates the PostgreSQL databases and dedicated login roles.
3. Restores the SQL archives.
4. Configures database access and read-only permissions.

The archives are expected under `/demo-data` inside the PostgreSQL container.

The script requires the PostgreSQL administrator username and four environment variables containing the read-only role passwords.

The dedicated demo database service is defined in `compose.demo.yaml`, which extends the base Docker Compose configuration.

## Access restrictions

The initialization script applies the following database-level restrictions:

- Separate PostgreSQL login roles for each dataset.
- Database connection permissions granted to the corresponding role.
- `SELECT` permissions on tables in the `public` schema.
- Removal of public database connection and temporary-object permissions.
- Removal of public schema creation permissions.
- Removal of public execution permissions on functions in the `public` schema.

These restrictions are part of a broader security strategy. Additional application-level and infrastructure controls are required before exposing the demonstration publicly.

## Data provenance and licensing

Each dataset has its own provenance, licensing conditions, and limitations, documented in its dedicated page.

The source datasets and PostgreSQL backup archives are not included in the public Git repository.

The absence of an archive from Git does not by itself establish permission to redistribute or publicly expose the underlying data.

## Current status

- All four PostgreSQL demo datasets have been prepared and validated.
- The dataset selection for the initial Public Demo is finalized.
- Configurable Public Demo usage limits are implemented and validated through automated tests.
- Database initialization and read-only access have been validated.
- The dedicated demo database service is integrated into the Docker Compose demo configuration.
- Application-level dataset selection and Public Demo mode are implemented and tested.
- A production Docker Compose configuration is available, including Gunicorn, WhiteNoise, and Caddy.
- The production configuration has been validated locally.

The Public Demo has not yet been deployed to a remote production environment.

Production deployment, HTTPS validation, final security checks,
and production validation of the implemented usage limits remain
to be completed.
