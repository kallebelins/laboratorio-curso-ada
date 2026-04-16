-- ============================================================
-- MovieFlix Analytics – Data Warehouse DDL
-- Schema: dw  (separado do schema público da aplicação)
-- Idempotente: pode ser reexecutado sem erros.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS dw;

-- ── Dimensão Filme ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dw.dim_movie (
    movie_id    VARCHAR(20)  PRIMARY KEY,   -- imdb_id do Data Lake
    title       VARCHAR(255) NOT NULL,
    genre       VARCHAR(255),
    year        INTEGER,
    country     VARCHAR(255),
    imdb_rating NUMERIC(3, 1)
);

-- ── Dimensão Usuário ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dw.dim_user (
    user_id   INTEGER      PRIMARY KEY,
    name      VARCHAR(255) NOT NULL,
    age_group VARCHAR(20),
    country   VARCHAR(255)
);

-- ── Tabela Fato Avaliações ───────────────────────────────────
CREATE TABLE IF NOT EXISTS dw.fact_rating (
    rating_id SERIAL      PRIMARY KEY,
    movie_id  VARCHAR(20) NOT NULL REFERENCES dw.dim_movie(movie_id) ON DELETE CASCADE,
    user_id   INTEGER     NOT NULL REFERENCES dw.dim_user(user_id)   ON DELETE CASCADE,
    score     NUMERIC(4, 2),
    rated_at  DATE
);

-- Índices para performance analítica
CREATE INDEX IF NOT EXISTS idx_fact_rating_movie  ON dw.fact_rating(movie_id);
CREATE INDEX IF NOT EXISTS idx_fact_rating_user   ON dw.fact_rating(user_id);
CREATE INDEX IF NOT EXISTS idx_fact_rating_date   ON dw.fact_rating(rated_at);
