-- ============================================================
-- MovieFlix Analytics – Data Mart
-- Views e Materialized Views sobre o schema dw
-- Idempotente: DROP ... IF EXISTS antes de CREATE
-- ============================================================

-- ── mart_top10_by_genre ─────────────────────────────────────
-- Top 10 filmes por gênero principal (primeiro gênero listado),
-- ordenado pela média de score das avaliações de usuários.
DROP VIEW IF EXISTS dw.mart_top10_by_genre;
CREATE VIEW dw.mart_top10_by_genre AS
WITH genre_scores AS (
    SELECT
        split_part(m.genre, ',', 1)                     AS primary_genre,
        m.movie_id,
        m.title,
        ROUND(AVG(f.score)::NUMERIC, 2)                 AS avg_score,
        COUNT(f.rating_id)                              AS total_ratings,
        ROW_NUMBER() OVER (
            PARTITION BY split_part(m.genre, ',', 1)
            ORDER BY AVG(f.score) DESC, COUNT(f.rating_id) DESC
        )                                               AS rk
    FROM dw.fact_rating f
    JOIN dw.dim_movie   m ON m.movie_id = f.movie_id
    WHERE m.genre IS NOT NULL
    GROUP BY split_part(m.genre, ',', 1), m.movie_id, m.title
)
SELECT primary_genre, movie_id, title, avg_score, total_ratings
FROM   genre_scores
WHERE  rk <= 10
ORDER  BY primary_genre, rk;


-- ── mart_avg_by_age_group ───────────────────────────────────
-- Nota média das avaliações agrupada por faixa etária do usuário.
DROP VIEW IF EXISTS dw.mart_avg_by_age_group;
CREATE VIEW dw.mart_avg_by_age_group AS
SELECT
    u.age_group,
    ROUND(AVG(f.score)::NUMERIC, 2) AS avg_score,
    COUNT(f.rating_id)              AS total_ratings
FROM dw.fact_rating f
JOIN dw.dim_user    u ON u.user_id = f.user_id
WHERE u.age_group IS NOT NULL
GROUP BY u.age_group
ORDER BY avg_score DESC;


-- ── mart_ratings_by_country ─────────────────────────────────
-- Número de avaliações e nota média por país do usuário.
DROP VIEW IF EXISTS dw.mart_ratings_by_country;
CREATE VIEW dw.mart_ratings_by_country AS
SELECT
    u.country,
    COUNT(f.rating_id)              AS total_ratings,
    ROUND(AVG(f.score)::NUMERIC, 2) AS avg_score
FROM dw.fact_rating f
JOIN dw.dim_user    u ON u.user_id = f.user_id
WHERE u.country IS NOT NULL
GROUP BY u.country
ORDER BY total_ratings DESC;
