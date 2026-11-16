# Badminton Demo Dataset

## Overview

Relational PostgreSQL dataset containing international badminton match results from 2007 to July 2026.

The dataset is used to demonstrate natural-language querying, SQL generation, relational joins, and schema exploration in AskMyData.


## Data provenance

- Source repository: https://github.com/SahilMotyar/bwf-match-data
- Original data: badminton match results and tournament metadata
- Records: 105,147 matches
- Disciplines: MS, WS, MD, WD, XD

## Licensing and public demo usage

The source repository does not specify an explicit license granting reuse or redistribution rights. The dataset must not be described as openly licensed.

The project has decided to include this dataset in the invitation-only AskMyData Public Demo, acknowledging and accepting the associated legal uncertainty.

The following precautions apply:

- Original source files and PostgreSQL database dumps are excluded from the public GitHub repository.
- Demo access is restricted to invited users.
- Database access uses a dedicated read-only PostgreSQL role.
- Dataset provenance and licensing uncertainty remain documented.
- The dataset can be disabled or removed if necessary.

These precautions limit exposure but do not establish legal authorization to reuse or redistribute the data.

## Relational model

The PostgreSQL schema contains 13 tables:

- Tournament metadata: `countries`, `tournament_categories`, `tournaments`, `tiers`
- Competition structure: `disciplines`, `rounds`
- Players and partnerships: `players`, `pairs`, `pair_players`
- Match results: `matches`, `match_participants`, `games`, `game_scores`

Player identities are derived from source names. Identical names may refer to different individuals, and variations in spelling may refer to the same player.

Match winners are preserved from the source data rather than inferred from game scores.

## Data preparation

Source files are stored locally under `backups/demo-db/badminton/`.

Generate the relational CSV files:

```bash
/usr/bin/python3 scripts/demo-db/badminton/import.py
```

Create a dedicated PostgreSQL database and apply:

```text
scripts/demo-db/badminton/schema.sql
```

Import the generated CSV files:

```bash
BADMINTON_CONTAINER=<container> \
BADMINTON_DATABASE=<database> \
bash scripts/demo-db/badminton/import.sh
```

The target database must be empty and contain the schema before import.

## Demo initialization

The compressed PostgreSQL archive is stored locally at:

```text
backups/demo-db/badminton.sql.gz
```

The demo initialization script restores this archive into the `badminton` database and creates the `badminton_readonly` role.

The archive must be supplied separately during deployment because it is excluded from Git.

## Validation

Local validation completed successfully:

- 13 relational tables imported
- 105,147 matches
- 210,294 match participants
- 242,009 games
- 484,018 game scores
- PostgreSQL restoration verified
- Read-only permissions verified
- Cross-database access denied
- TCP password authentication verified

These checks validate the technical import and access controls, not the completeness or accuracy of the original match records.
