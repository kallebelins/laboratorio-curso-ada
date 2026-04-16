-- ============================================================
-- MovieFlix Analytics – Queries Analíticas (Fase 5 – Tarefa 019)
-- Execute contra o banco com o schema "dw" carregado.
-- ============================================================


-- ── Q1: Quais os 5 filmes mais populares? (maior nº de avaliações) ──────────
--
-- Resultado esperado: os 5 filmes que acumularam mais avaliações de usuários,
-- independentemente da nota. Indica popularidade/alcance.

SELECT
    m.title,
    m.genre,
    COUNT(f.rating_id)              AS total_ratings,
    ROUND(AVG(f.score)::NUMERIC, 2) AS avg_score
FROM dw.fact_rating f
JOIN dw.dim_movie   m ON m.movie_id = f.movie_id
GROUP BY m.movie_id, m.title, m.genre
ORDER BY total_ratings DESC
LIMIT 5;

/*
  Resultado esperado (exemplo com dados sintéticos de 500 avaliações e 45 filmes):
  Os filmes com maior número de avaliações refletem a distribuição aleatória
  do script fetch_lake.py. Títulos populares da amostra (Jurassic World,
  Star Wars, Star Trek) tendem a aparecer no topo devido ao volume de busca.
*/


-- ── Q2: Qual gênero tem melhor avaliação média? ─────────────────────────────
--
-- Resultado esperado: o gênero principal (primeiro da lista) com a maior
-- média de score entre todas as avaliações. Filmes de Drama/Ação costumam
-- liderar pela amostra OMDB utilizada.

SELECT
    split_part(m.genre, ',', 1)     AS primary_genre,
    COUNT(f.rating_id)              AS total_ratings,
    ROUND(AVG(f.score)::NUMERIC, 2) AS avg_score
FROM dw.fact_rating f
JOIN dw.dim_movie   m ON m.movie_id = f.movie_id
WHERE m.genre IS NOT NULL
GROUP BY primary_genre
ORDER BY avg_score DESC
LIMIT 10;

/*
  Resultado esperado: géneros com poucas avaliações podem ter médias extremas.
  Filtrando gêneros com >= 5 avaliações o ranking se estabiliza. O gênero
  "Comedy" tende a ter boa média na amostra OMDB (filmes clássicos incluídos).
*/


-- ── Q3: Qual país assiste mais filmes? ──────────────────────────────────────
--
-- País do usuário que gerou o maior volume de avaliações.
-- Resultado esperado: os dados sintéticos de usuários distribuem países
-- com pesos definidos em fetch_lake.py; "United States" e "Brazil" costumam
-- liderar na amostra gerada.

SELECT
    u.country,
    COUNT(f.rating_id)              AS total_ratings,
    COUNT(DISTINCT f.movie_id)      AS distinct_movies_watched,
    ROUND(AVG(f.score)::NUMERIC, 2) AS avg_score
FROM dw.fact_rating f
JOIN dw.dim_user    u ON u.user_id = f.user_id
WHERE u.country IS NOT NULL
GROUP BY u.country
ORDER BY total_ratings DESC
LIMIT 10;

/*
  Resultado esperado: o país com mais avaliações é o que tem mais usuários
  sintéticos na amostra. Como fetch_lake.py usa Brasil, EUA e outros países
  com distribuição aproximadamente igual, pequenas variações aleatórias
  determinam o vencedor em cada execução.
*/
