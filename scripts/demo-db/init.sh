#!/usr/bin/env bash
set -Eeuo pipefail

# PostgreSQL demo databases initialization.
# Executed only when the PostgreSQL data directory is empty.

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${PAGILA_READONLY_PASSWORD:?PAGILA_READONLY_PASSWORD is required}"
: "${EEG_DEMO_READONLY_PASSWORD:?EEG_DEMO_READONLY_PASSWORD is required}"
: "${OLIST_READONLY_PASSWORD:?OLIST_READONLY_PASSWORD is required}"

DEMO_DATA_DIR="/demo-data"

for dataset in pagila eeg_demo olist; do
    archive="${DEMO_DATA_DIR}/${dataset}.sql.gz"

    if [[ ! -s "$archive" ]]; then
        echo "Missing or empty dataset archive: $archive" >&2
        exit 1
    fi

    gzip -t "$archive"
done

echo "Creating demo databases and read-only roles..."

{
    printf '\\set pagila_password %s\n' \
        "$(printf '%s' "$PAGILA_READONLY_PASSWORD" | base64 -w 0)"

    printf '\\set eeg_password %s\n' \
        "$(printf '%s' "$EEG_DEMO_READONLY_PASSWORD" | base64 -w 0)"

    printf '\\set olist_password %s\n' \
        "$(printf '%s' "$OLIST_READONLY_PASSWORD" | base64 -w 0)"

    cat <<'SQL'
SELECT format(
    'CREATE ROLE pagila_readonly LOGIN PASSWORD %L',
    convert_from(decode(:'pagila_password', 'base64'), 'UTF8')
) \gexec

SELECT format(
    'CREATE ROLE eeg_demo_readonly LOGIN PASSWORD %L',
    convert_from(decode(:'eeg_password', 'base64'), 'UTF8')
) \gexec

SELECT format(
    'CREATE ROLE olist_readonly LOGIN PASSWORD %L',
    convert_from(decode(:'olist_password', 'base64'), 'UTF8')
) \gexec

CREATE DATABASE pagila;
CREATE DATABASE askmydata_eeg_public_demo;
CREATE DATABASE olist;
SQL
} | psql -X -v ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname postgres

restore_dataset() {
    local database="$1"
    local archive="$2"
    local role="$3"

    echo "Restoring ${database}..."

    gzip -cd "${DEMO_DATA_DIR}/${archive}" |
        psql -X -v ON_ERROR_STOP=1 \
            --username "$POSTGRES_USER" \
            --dbname "$database"

    echo "Configuring read-only permissions for ${database}..."

    psql -X -v ON_ERROR_STOP=1 \
        --username "$POSTGRES_USER" \
        --dbname "$database" \
        -v readonly_role="$role" \
        -v database_name="$database" <<'SQL'
SELECT format(
    'REVOKE CONNECT, TEMPORARY ON DATABASE %I FROM PUBLIC',
    :'database_name'
) \gexec

REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Prevent public execution of dataset functions.
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;

SELECT format(
    'GRANT CONNECT ON DATABASE %I TO %I',
    :'database_name',
    :'readonly_role'
) \gexec

SELECT format(
    'GRANT USAGE ON SCHEMA public TO %I',
    :'readonly_role'
) \gexec

SELECT format(
    'GRANT SELECT ON ALL TABLES IN SCHEMA public TO %I',
    :'readonly_role'
) \gexec
SQL

    echo "Database ${database} initialized."
}

restore_dataset "pagila" "pagila.sql.gz" "pagila_readonly"
restore_dataset "askmydata_eeg_public_demo" "eeg_demo.sql.gz" "eeg_demo_readonly"
restore_dataset "olist" "olist.sql.gz" "olist_readonly"

echo "Demo databases initialized successfully."