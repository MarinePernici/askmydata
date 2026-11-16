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

Each database is intended to be configured as an independent data source in AskMyData.

The demonstration database environment is separate from the application's development database.

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

The dedicated demo database service has not yet been integrated into `compose.yaml`.

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

The four PostgreSQL demo datasets have been prepared and their initialization process has been tested.

The public demonstration environment is not yet deployed. Its final scope, access restrictions, and operational configuration will be established during the production-readiness phase.
