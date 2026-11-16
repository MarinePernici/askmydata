# EEG Demo Dataset

## Overview

The EEG demo dataset contains synthetic data representing an electrophysiological research context.

It is used to demonstrate AskMyData's ability to explore and query scientific datasets through natural language.

## Data provenance

The dataset was prepared specifically for the AskMyData demonstration.

It contains synthetic data and is not intended to represent actual patients or clinical observations.

## Database

- **Database:** `askmydata_eeg_public_demo`
- **Read-only role:** `eeg_demo_readonly`
- **Backup archive:** `backups/demo-db/eeg_demo.sql.gz`

The database is restored from a compressed PostgreSQL SQL dump.

## Demonstration use cases

The dataset is intended to support:

- Exploration of scientific data structures.
- Natural-language questions about measurements and associated records.
- SQL generation involving filters, aggregations, and joins where supported by the schema.
- Interpretation of query results in natural language.

## Initialization

The database is initialized through `scripts/demo-db/init.sh`.

The script restores `eeg_demo.sql.gz` and grants the dedicated role read-only access to tables in the `public` schema.

## Limitations

The dataset is synthetic and must not be used to draw clinical or scientific conclusions.

Its structure and generated values are intended for software demonstration rather than scientific validation.
