# Pagila Demo Dataset

## Overview

Pagila is a PostgreSQL sample database representing a DVD rental business.

It is used in AskMyData to evaluate natural-language querying, SQL generation, relational joins, aggregations, and business-oriented analysis.

## Data provenance and licensing

- **Dataset:** Pagila
- **Version:** `pagila-v3.1.0`
- **Source:** https://github.com/devrimgunduz/pagila
- **Database engine:** PostgreSQL 17
- **License:** PostgreSQL License
- **Copyright:** © 2015–2026 Devrim Gündüz

Pagila is a PostgreSQL adaptation of the Sakila sample database.

The dataset was obtained from the upstream repository.

The PostgreSQL License permits use, copying, modification, and distribution, including commercial use, provided that the required copyright notice, permission notice, and warranty disclaimers are preserved in distributed copies.

The full license text is included in [PAGILA-LICENSE.txt](./licenses/PAGILA-LICENSE.txt) and is also available in the upstream repository.

## Database structure

- **Schema:** `public`
- **Logical tables:** 15
- **Physical relations initially discovered:** 22

Seven PostgreSQL child partitions of the `payment` table were initially exposed as separate tables.

After correcting PostgreSQL schema discovery, AskMyData exposes the 15 logical tables while excluding the seven child partitions.

See [MVP Quality Benchmark](../benchmark/mvp-quality-benchmark.md) for the validation details.

## Database

- **Database:** `pagila`
- **Read-only role:** `pagila_readonly`
- **Backup archive:** `backups/demo-db/pagila.sql.gz`

## Relational model

Pagila represents several interconnected business entities, including:

- Films and categories.
- Actors and film casts.
- Customers and stores.
- Inventory and rentals.
- Payments and staff.

These relationships support SQL queries involving multiple tables.

## Demonstration use cases

Examples of natural-language questions include:

- Which films are rented most frequently?
- What is the total rental revenue by category?
- Which customers have generated the most revenue?
- How does rental activity vary over time?

These are example analytical questions, not recorded benchmark results.

## Initialization

The database is restored from `pagila.sql.gz` through `scripts/demo-db/init.sh`.

The script creates the database, restores its contents, and grants `pagila_readonly` read-only access to tables in the `public` schema.

## Limitations

Pagila is a sample business database, not a representation of a live rental company.

Its data should be interpreted as demonstration data rather than current commercial information.
