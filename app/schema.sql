-- MovieFlix Analytics – Schema DDL
-- Idempotent: use IF NOT EXISTS so it can be re-run safely.

CREATE TABLE IF NOT EXISTS movies (
    id          SERIAL PRIMARY KEY,
    imdb_id     VARCHAR(20)  UNIQUE NOT NULL,
    title       VARCHAR(255) NOT NULL,
    genre       VARCHAR(255),
    year        INTEGER,
    country     VARCHAR(255),
    imdb_rating NUMERIC(3, 1)
);

CREATE TABLE IF NOT EXISTS users (
    id        INTEGER PRIMARY KEY,
    name      VARCHAR(255) NOT NULL,
    age_group VARCHAR(20),
    country   VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS ratings (
    id       SERIAL PRIMARY KEY,
    movie_id VARCHAR(20)    NOT NULL REFERENCES movies(imdb_id) ON DELETE CASCADE,
    user_id  INTEGER        NOT NULL REFERENCES users(id)       ON DELETE CASCADE,
    score    NUMERIC(4, 2),
    rated_at DATE
);
