# ============================================================
# MovieFlix Analytics – Makefile
# Simplifica a execução do pipeline de dados e da aplicação.
# ============================================================

.PHONY: help up down build logs \
        fetch-lake etl-load create-mart analytics \
        etl-full reset-dw

# ── Variáveis ─────────────────────────────────────────────────
DB_URL  ?= postgresql://postgres:P4ssw0rd@localhost:5432/movieflix
PSQL    := docker exec -i movieflix-dw psql -U postgres -d movieflix

# ── Ajuda ─────────────────────────────────────────────────────
help:
	@echo ""
	@echo "MovieFlix Analytics – comandos disponíveis:"
	@echo ""
	@echo "  Aplicação"
	@echo "    make up           Sobe todos os serviços (docker compose up -d --build)"
	@echo "    make down         Para e remove containers"
	@echo "    make build        Reconstrói a imagem da aplicação"
	@echo "    make logs         Exibe logs em tempo real"
	@echo ""
	@echo "  Pipeline de Dados"
	@echo "    make fetch-lake   Busca filmes na OMDB API e gera os CSVs do Data Lake"
	@echo "    make etl-load     ETL: CSVs -> Data Warehouse (schema dw)"
	@echo "    make create-mart  Cria as views do Data Mart (schema dw)"
	@echo "    make analytics    Executa as queries analíticas (Q1, Q2, Q3)"
	@echo "    make etl-full     Pipeline completo: etl-load + create-mart + analytics"
	@echo "    make reset-dw     Remove e recria o schema dw"
	@echo ""

# ── Aplicação ─────────────────────────────────────────────────
up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build app

logs:
	docker compose logs -f

# ── Data Lake ─────────────────────────────────────────────────
fetch-lake:
	docker compose run --rm app python data/scripts/fetch_lake.py

# ── Data Warehouse ────────────────────────────────────────────
etl-load:
	docker compose run --rm etl

create-mart:
	$(PSQL) -f /dev/stdin < data/scripts/create_mart.sql

analytics:
	@echo "=== Q1: Top 5 filmes mais populares ==="
	$(PSQL) -c "\
	  SELECT m.title, COUNT(f.rating_id) AS total_ratings, \
	         ROUND(AVG(f.score)::NUMERIC,2) AS avg_score \
	  FROM dw.fact_rating f \
	  JOIN dw.dim_movie m ON m.movie_id = f.movie_id \
	  GROUP BY m.movie_id, m.title \
	  ORDER BY total_ratings DESC LIMIT 5;"
	@echo ""
	@echo "=== Q2: Gênero com melhor avaliação média ==="
	$(PSQL) -c "\
	  SELECT split_part(m.genre,',',1) AS primary_genre, \
	         COUNT(f.rating_id) AS total_ratings, \
	         ROUND(AVG(f.score)::NUMERIC,2) AS avg_score \
	  FROM dw.fact_rating f \
	  JOIN dw.dim_movie m ON m.movie_id = f.movie_id \
	  WHERE m.genre IS NOT NULL \
	  GROUP BY primary_genre \
	  ORDER BY avg_score DESC LIMIT 5;"
	@echo ""
	@echo "=== Q3: País com mais avaliações ==="
	$(PSQL) -c "\
	  SELECT u.country, COUNT(f.rating_id) AS total_ratings, \
	         ROUND(AVG(f.score)::NUMERIC,2) AS avg_score \
	  FROM dw.fact_rating f \
	  JOIN dw.dim_user u ON u.user_id = f.user_id \
	  WHERE u.country IS NOT NULL \
	  GROUP BY u.country \
	  ORDER BY total_ratings DESC LIMIT 5;"

reset-dw:
	$(PSQL) -c "DROP SCHEMA IF EXISTS dw CASCADE;"
	$(PSQL) -f /dev/stdin < data/scripts/create_dw.sql

# ── Pipeline completo ─────────────────────────────────────────
etl-full: etl-load create-mart analytics
