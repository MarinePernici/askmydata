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

## Relational model

The PostgreSQL schema contains six tables:

- `users`: demographic and clinical characteristics.
- `evaluations`: evaluation records and dates.
- `diagnostics`: diagnostic categories.
- `schoollevels`: educational levels.
- `alpha_peak`: alpha peak measurements by electrode and value type.
- `power_spectral_density`: spectral power measurements by electrode and frequency.

The relational structure supports analyses combining participant
characteristics, evaluation records, and electrophysiological measurements.

## Demonstration use cases

Examples of natural-language questions include:

- How many participants are included in the dataset?
- What is the distribution of participants by gender and laterality?
- How many evaluations have been performed per participant?
- What is the distribution of participants by diagnostic category?
- What is the average alpha peak value by electrode and value type?
- How does average power spectral density vary across frequencies
  and electrodes?
- How does average alpha peak value vary across diagnostic categories
  for each value type?

These questions demonstrate potential analytical use cases,
including aggregations, relational joins, and scientific data exploration.

They are illustrative examples, not validated benchmark results.

## Initialization

The database is initialized through `scripts/demo-db/init.sh`.

The script restores `eeg_demo.sql.gz` and grants the dedicated role read-only access to tables in the `public` schema.

## Limitations

The dataset is synthetic and must not be used to draw clinical or scientific conclusions.

Its structure and generated values are intended for software demonstration rather than scientific validation.
