"""
app/app.py – MovieFlix Analytics (Flask, read-only)
"""

import os

import psycopg2
import psycopg2.extras
from flask import Flask, abort, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:changeme@db:5432/movieflix"
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _db():
    """Abre uma conexão com cursor que retorna dicionários."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# ─── rotas ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    with _db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT m.imdb_id,
                       m.title,
                       m.genre,
                       m.year,
                       m.imdb_rating,
                       COUNT(r.id)                    AS num_ratings,
                       ROUND(AVG(r.score)::numeric, 2) AS avg_score
                FROM   movies m
                LEFT JOIN ratings r ON m.imdb_id = r.movie_id
                GROUP  BY m.imdb_id, m.title, m.genre, m.year, m.imdb_rating
                ORDER  BY num_ratings DESC
                LIMIT  5
            """)
            top_movies = cur.fetchall()

            cur.execute("SELECT COUNT(*) AS total FROM movies")
            total_movies = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) AS total FROM users")
            total_users = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) AS total FROM ratings")
            total_ratings = cur.fetchone()["total"]

            cur.execute("SELECT ROUND(AVG(score)::numeric, 2) AS avg FROM ratings")
            avg_rating = cur.fetchone()["avg"]

    return render_template(
        "index.html",
        top_movies=top_movies,
        total_movies=total_movies,
        total_users=total_users,
        total_ratings=total_ratings,
        avg_rating=avg_rating,
    )


@app.route("/movies")
def movies():
    with _db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT m.imdb_id,
                       m.title,
                       m.genre,
                       m.year,
                       m.country,
                       m.imdb_rating,
                       COUNT(r.id)                    AS num_ratings,
                       ROUND(AVG(r.score)::numeric, 2) AS avg_score
                FROM   movies m
                LEFT JOIN ratings r ON m.imdb_id = r.movie_id
                GROUP  BY m.imdb_id, m.title, m.genre, m.year, m.country, m.imdb_rating
                ORDER  BY m.title
            """)
            all_movies = cur.fetchall()

    return render_template("movies.html", movies=all_movies)


@app.route("/movies/<imdb_id>")
def movie_detail(imdb_id: str):
    with _db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM movies WHERE imdb_id = %s", (imdb_id,))
            movie = cur.fetchone()

        if movie is None:
            abort(404)

        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.name,
                       u.age_group,
                       u.country,
                       r.score,
                       r.rated_at
                FROM   ratings r
                JOIN   users   u ON r.user_id = u.id
                WHERE  r.movie_id = %s
                ORDER  BY r.rated_at DESC
            """, (imdb_id,))
            movie_ratings = cur.fetchall()

            cur.execute("""
                SELECT COUNT(*)                        AS total,
                       ROUND(AVG(score)::numeric, 2)  AS avg,
                       MAX(score)                     AS max_score,
                       MIN(score)                     AS min_score
                FROM   ratings
                WHERE  movie_id = %s
            """, (imdb_id,))
            stats = cur.fetchone()

    return render_template(
        "movie_detail.html",
        movie=movie,
        ratings=movie_ratings,
        stats=stats,
    )


@app.route("/analytics")
def analytics():
    with _db() as conn:
        with conn.cursor() as cur:
            # Q1: Top 5 filmes mais populares (maior nº de avaliações)
            cur.execute("""
                SELECT m.title,
                       m.genre,
                       COUNT(f.rating_id)              AS total_ratings,
                       ROUND(AVG(f.score)::numeric, 2) AS avg_score
                FROM   dw.fact_rating f
                JOIN   dw.dim_movie   m ON m.movie_id = f.movie_id
                GROUP  BY m.movie_id, m.title, m.genre
                ORDER  BY total_ratings DESC
                LIMIT  5
            """)
            top_popular = cur.fetchall()

            # Q2: Top gêneros por nota média – Data Mart view
            cur.execute("""
                SELECT split_part(m.genre, ',', 1)         AS genre,
                       ROUND(AVG(f.score)::numeric, 2)     AS avg_score,
                       COUNT(f.rating_id)                  AS num_ratings
                FROM   dw.fact_rating f
                JOIN   dw.dim_movie   m ON m.movie_id = f.movie_id
                WHERE  m.genre IS NOT NULL
                GROUP  BY genre
                ORDER  BY avg_score DESC
                LIMIT  10
            """)
            top_genres = cur.fetchall()

            # Top 10 filmes por gênero – Data Mart view (mart_top10_by_genre)
            cur.execute("""
                SELECT primary_genre,
                       title,
                       avg_score,
                       total_ratings
                FROM   dw.mart_top10_by_genre
            """)
            top10_by_genre = cur.fetchall()

            # Q3: Nota média por faixa etária – Data Mart view
            cur.execute("""
                SELECT age_group,
                       avg_score,
                       total_ratings AS num_ratings
                FROM   dw.mart_avg_by_age_group
            """)
            by_age_group = cur.fetchall()

            # Q3: Avaliações por país – Data Mart view (mart_ratings_by_country)
            cur.execute("""
                SELECT country,
                       total_ratings AS num_ratings,
                       avg_score
                FROM   dw.mart_ratings_by_country
                LIMIT  10
            """)
            by_country = cur.fetchall()

    return render_template(
        "analytics.html",
        top_popular=top_popular,
        top_genres=top_genres,
        top10_by_genre=top10_by_genre,
        by_age_group=by_age_group,
        by_country=by_country,
    )


# ─── entry-point local ────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
