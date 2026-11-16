"""Transform BWF source files into relational CSV files for PostgreSQL."""

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
SOURCE_DIR = BASE_DIR / "backups" / "demo-db" / "badminton"
OUTPUT_DIR = SOURCE_DIR / "generated"


def write_csv(filename, columns, rows):
    """Write a relational CSV file with a header."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with (OUTPUT_DIR / filename).open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)


def load_tournaments():
    """Load tournament metadata and prepare lookup by name."""
    with (SOURCE_DIR / "index.json").open(encoding="utf-8") as file:
        data = json.load(file)

    by_name = defaultdict(list)

    for tournament in data:
        by_name[tournament["name"].strip()].append(tournament)

    return data, by_name


def export_tournament_references(tournaments):
    """Export countries, categories and tournaments."""
    country_names = sorted(
        {
            item["country"].strip()
            for item in tournaments
            if item.get("country") and item["country"].strip()
        }
    )

    category_names = sorted(
        {
            item["category"].strip()
            for item in tournaments
            if item.get("category") and item["category"].strip()
        }
    )

    countries = {name: index for index, name in enumerate(country_names, start=1)}
    categories = {name: index for index, name in enumerate(category_names, start=1)}

    write_csv(
        "countries.csv",
        ["country_id", "name"],
        [(identifier, name) for name, identifier in countries.items()],
    )

    write_csv(
        "tournament_categories.csv",
        ["category_id", "name"],
        [(identifier, name) for name, identifier in categories.items()],
    )

    rows = []

    for item in tournaments:
        prize = item.get("prize_money")
        if prize:
            prize = prize.replace(",", "").strip()

        rows.append(
            (
                item["id"],
                item["name"],
                item["start_date"][:10] if item.get("start_date") else "",
                item["end_date"][:10] if item.get("end_date") else "",
                countries.get((item.get("country") or "").strip(), ""),
                categories.get((item.get("category") or "").strip(), ""),
                prize or "",
                item.get("url") or "",
                item.get("code") or "",
            )
        )

    write_csv(
        "tournaments.csv",
        [
            "tournament_id",
            "name",
            "start_date",
            "end_date",
            "country_id",
            "category_id",
            "prize_money",
            "source_url",
            "source_code",
        ],
        rows,
    )

    return countries, categories


def export_players_and_pairs():
    """Export players, doubles pairs and their relationships."""
    players = set()
    pairs = set()

    with (SOURCE_DIR / "matches.csv").open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            is_doubles = row["discipline"] in {"MD", "WD", "XD"}

            for side in ("team1", "team2"):
                team = row[side].strip()

                if is_doubles:
                    names = tuple(name.strip() for name in team.split(" / "))
                    if len(names) != 2 or not all(names):
                        raise ValueError(f"Invalid pair: {team!r}")

                    players.update(names)
                    pairs.add(tuple(sorted(names)))
                else:
                    if not team:
                        raise ValueError("Empty player name")
                    players.add(team)

    player_ids = {
        name: identifier for identifier, name in enumerate(sorted(players), start=1)
    }

    pair_ids = {
        pair: identifier for identifier, pair in enumerate(sorted(pairs), start=1)
    }

    write_csv(
        "players.csv",
        ["player_id", "name"],
        [(identifier, name) for name, identifier in player_ids.items()],
    )

    write_csv(
        "pairs.csv",
        ["pair_id"],
        [(identifier,) for identifier in pair_ids.values()],
    )

    write_csv(
        "pair_players.csv",
        ["pair_id", "player_id"],
        [
            (pair_id, player_ids[player])
            for pair, pair_id in pair_ids.items()
            for player in pair
        ],
    )

    return player_ids, pair_ids


def export_match_references():
    """Export disciplines, tiers and rounds used by matches."""
    disciplines = {
        "MS": "Men's Singles",
        "WS": "Women's Singles",
        "MD": "Men's Doubles",
        "WD": "Women's Doubles",
        "XD": "Mixed Doubles",
    }

    tiers = set()
    rounds = set()

    with (SOURCE_DIR / "matches.csv").open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["discipline"] not in disciplines:
                raise ValueError(f"Unknown discipline: {row['discipline']}")

            tier = row["tier"].strip()
            if not tier:
                raise ValueError("Empty tournament tier")
            tiers.add(tier)

            round_name = row["round"].strip()
            if round_name:
                rounds.add(round_name)

    tier_ids = {
        name: identifier for identifier, name in enumerate(sorted(tiers), start=1)
    }

    round_ids = {
        name: identifier for identifier, name in enumerate(sorted(rounds), start=1)
    }

    write_csv(
        "disciplines.csv",
        ["discipline_code", "name"],
        sorted(disciplines.items()),
    )

    write_csv(
        "tiers.csv",
        ["tier_id", "name"],
        [(identifier, name) for name, identifier in tier_ids.items()],
    )

    write_csv(
        "rounds.csv",
        ["round_id", "name"],
        [(identifier, name) for name, identifier in round_ids.items()],
    )

    return tier_ids, round_ids


def export_matches(tournament_lookup, player_ids, pair_ids, tier_ids, round_ids):
    """Export matches, participants, games and scores."""
    match_rows = []
    participant_rows = []
    game_rows = []
    score_rows = []

    game_id = 0

    with (SOURCE_DIR / "matches.csv").open(encoding="utf-8", newline="") as file:
        for match_id, row in enumerate(csv.DictReader(file), start=1):
            match_date = date.fromisoformat(row["date"][:10])

            candidates = [
                tournament
                for tournament in tournament_lookup[row["tournament"].strip()]
                if date.fromisoformat(tournament["start_date"][:10])
                <= match_date
                <= date.fromisoformat(tournament["end_date"][:10])
            ]

            if len(candidates) != 1:
                raise ValueError(
                    f"Cannot uniquely identify tournament for match {match_id}"
                )

            tournament_id = candidates[0]["id"]
            discipline = row["discipline"]
            is_doubles = discipline in {"MD", "WD", "XD"}

            match_rows.append(
                (
                    match_id,
                    tournament_id,
                    discipline,
                    tier_ids[row["tier"].strip()],
                    round_ids.get(row["round"].strip(), ""),
                    match_date.isoformat(),
                    int(row["winner"]),
                    row["score"].strip(),
                )
            )

            for side in (1, 2):
                team = row[f"team{side}"].strip()

                if is_doubles:
                    names = tuple(sorted(name.strip() for name in team.split(" / ")))
                    player_id = ""
                    pair_id = pair_ids[names]
                else:
                    player_id = player_ids[team]
                    pair_id = ""

                participant_rows.append(
                    (
                        match_id,
                        side,
                        player_id,
                        pair_id,
                        row[f"team{side}_at_home"].strip().lower()
                        in {"true", "1", "yes"},
                        team,
                    )
                )

            for game_number, score in enumerate(row["score"].split(), start=1):
                game_id += 1
                points1, points2 = map(int, score.split("-"))

                game_rows.append((game_id, match_id, game_number))
                score_rows.append((game_id, 1, points1))
                score_rows.append((game_id, 2, points2))

    write_csv(
        "matches.csv",
        [
            "match_id",
            "tournament_id",
            "discipline_code",
            "tier_id",
            "round_id",
            "match_date",
            "winner_side",
            "score_raw",
        ],
        match_rows,
    )

    write_csv(
        "match_participants.csv",
        [
            "match_id",
            "side",
            "player_id",
            "pair_id",
            "at_home",
            "source_name",
        ],
        participant_rows,
    )

    write_csv(
        "games.csv",
        ["game_id", "match_id", "game_number"],
        game_rows,
    )

    write_csv(
        "game_scores.csv",
        ["game_id", "side", "points"],
        score_rows,
    )

    return len(match_rows), len(game_rows)


if __name__ == "__main__":
    tournaments, tournament_lookup = load_tournaments()
    export_tournament_references(tournaments)

    player_ids, pair_ids = export_players_and_pairs()
    tier_ids, round_ids = export_match_references()
    match_count, game_count = export_matches(
        tournament_lookup,
        player_ids,
        pair_ids,
        tier_ids,
        round_ids,
    )

    print(f"Matches exported: {match_count}")
    print(f"Games exported: {game_count}")
    print(f"Tournaments exported: {len(tournaments)}")
    print(f"Players exported: {len(player_ids)}")
    print(f"Pairs exported: {len(pair_ids)}")
    print(f"Tiers exported: {len(tier_ids)}")
    print(f"Rounds exported: {len(round_ids)}")
    print(f"Output directory: {OUTPUT_DIR}")
