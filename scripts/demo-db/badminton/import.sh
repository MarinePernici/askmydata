
#!/usr/bin/env bash
set -Eeuo pipefail

# BWF badminton dataset import for AskMyData demo.
# Run from the AskMyData project root.
# The target database must already exist and contain schema.sql.

CONTAINER="${BADMINTON_CONTAINER:-askmydata-demo-db-test}"
DATABASE="${BADMINTON_DATABASE:-badminton_schema_test}"
CSV_DIR="backups/demo-db/badminton/generated"

import_csv() {
    local table="$1"
    local columns="$2"
    local file="${CSV_DIR}/${table}.csv"

    if [[ ! -s "$file" ]]; then
        echo "Missing or empty CSV: $file" >&2
        exit 1
    fi

    echo "Importing ${table}..."

    docker exec -i "$CONTAINER" \
        psql -X -v ON_ERROR_STOP=1 \
        -U postgres -d "$DATABASE" \
        -c "COPY ${table} (${columns}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '');" \
        < "$file"
}

# Reference tables
import_csv countries "country_id, name"
import_csv tournament_categories "category_id, name"
import_csv tiers "tier_id, name"
import_csv tournaments \
    "tournament_id, name, start_date, end_date, country_id, category_id, prize_money, source_url, source_code"
import_csv disciplines "discipline_code, name"
import_csv rounds "round_id, name"

# Players and doubles pairs
import_csv players "player_id, name"
import_csv pairs "pair_id"
import_csv pair_players "pair_id, player_id"

# Matches and results
import_csv matches \
    "match_id, tournament_id, discipline_code, tier_id, round_id, match_date, winner_side, score_raw"
import_csv match_participants \
    "match_id, side, player_id, pair_id, at_home, source_name"
import_csv games "game_id, match_id, game_number"
import_csv game_scores "game_id, side, points"

echo "Badminton import completed."
