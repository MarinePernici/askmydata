
-- BWF Badminton Match Dataset
-- PostgreSQL schema for AskMyData recruiter demo
--
-- Source: https://github.com/SahilMotyar/bwf-match-data
-- BWF data reuse rights have not been explicitly granted.
-- Do not commit source data or database dumps.

CREATE TABLE countries (
    country_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE tournament_categories (
    category_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE tiers (
    tier_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE tournaments (
    tournament_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    country_id BIGINT REFERENCES countries(country_id),
    category_id BIGINT REFERENCES tournament_categories(category_id),
    prize_money NUMERIC(14, 2),
    source_url TEXT,
    source_code TEXT
);

CREATE TABLE disciplines (
    discipline_code TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE rounds (
    round_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE players (
    player_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE pairs (
    pair_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY
);

CREATE TABLE pair_players (
    pair_id BIGINT NOT NULL REFERENCES pairs(pair_id),
    player_id BIGINT NOT NULL REFERENCES players(player_id),
    PRIMARY KEY (pair_id, player_id)
);

CREATE TABLE matches (
    match_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tournament_id BIGINT NOT NULL REFERENCES tournaments(tournament_id),
    discipline_code TEXT NOT NULL REFERENCES disciplines(discipline_code),
    tier_id BIGINT NOT NULL REFERENCES tiers(tier_id),
    round_id BIGINT REFERENCES rounds(round_id),
    match_date DATE NOT NULL,
    winner_side SMALLINT NOT NULL CHECK (winner_side IN (1, 2)),
    score_raw TEXT NOT NULL
);

CREATE TABLE match_participants (
    match_id BIGINT NOT NULL REFERENCES matches(match_id),
    side SMALLINT NOT NULL CHECK (side IN (1, 2)),
    player_id BIGINT REFERENCES players(player_id),
    pair_id BIGINT REFERENCES pairs(pair_id),
    at_home BOOLEAN NOT NULL DEFAULT FALSE,
    source_name TEXT NOT NULL,
    PRIMARY KEY (match_id, side),
    CHECK (
        (player_id IS NOT NULL AND pair_id IS NULL)
        OR
        (player_id IS NULL AND pair_id IS NOT NULL)
    )
);

CREATE TABLE games (
    game_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(match_id),
    game_number SMALLINT NOT NULL CHECK (game_number BETWEEN 1 AND 5),
    UNIQUE (match_id, game_number)
);

CREATE TABLE game_scores (
    game_id BIGINT NOT NULL REFERENCES games(game_id),
    side SMALLINT NOT NULL CHECK (side IN (1, 2)),
    points SMALLINT NOT NULL CHECK (points >= 0),
    PRIMARY KEY (game_id, side)
);

CREATE INDEX idx_matches_tournament ON matches(tournament_id);
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_discipline ON matches(discipline_code);
CREATE INDEX idx_match_participants_player ON match_participants(player_id);
CREATE INDEX idx_match_participants_pair ON match_participants(pair_id);
CREATE INDEX idx_pair_players_player ON pair_players(player_id);
