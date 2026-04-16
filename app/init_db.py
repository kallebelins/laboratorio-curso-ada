"""
app/init_db.py – ETL idempotente: CSVs do Data Lake → PostgreSQL
Executa: python app/init_db.py  (WORKDIR = raiz do projeto)
"""

import os
import sys

import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:changeme@db:5432/movieflix"
)
DATA_LAKE = os.environ.get("DATA_LAKE_DIR", "data/lake")


# ─── conexão ──────────────────────────────────────────────────────────────────

def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ─── schema ───────────────────────────────────────────────────────────────────

def create_schema(conn: psycopg2.extensions.connection) -> None:
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, encoding="utf-8") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print("Schema criado/verificado.")


# ─── loaders ──────────────────────────────────────────────────────────────────

def load_movies(conn: psycopg2.extensions.connection) -> None:
    path = os.path.join(DATA_LAKE, "movies.csv")
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"imdbID": "imdb_id", "imdbRating": "imdb_rating"})
    df["title"] = df["title"].str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["imdb_rating"] = pd.to_numeric(df["imdb_rating"], errors="coerce")

    sql = """
        INSERT INTO movies (imdb_id, title, genre, year, country, imdb_rating)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (imdb_id) DO UPDATE SET
            title       = EXCLUDED.title,
            genre       = EXCLUDED.genre,
            year        = EXCLUDED.year,
            country     = EXCLUDED.country,
            imdb_rating = EXCLUDED.imdb_rating
    """
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute(sql, (
                row["imdb_id"],
                row["title"],
                row.get("genre") or None,
                None if pd.isna(row["year"]) else int(row["year"]),
                row.get("country") or None,
                None if pd.isna(row["imdb_rating"]) else float(row["imdb_rating"]),
            ))
    conn.commit()
    print(f"  → {len(df)} filmes carregados.")


def load_users(conn: psycopg2.extensions.connection) -> None:
    path = os.path.join(DATA_LAKE, "users.csv")
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df["name"] = df["name"].str.strip()

    sql = """
        INSERT INTO users (id, name, age_group, country)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            name      = EXCLUDED.name,
            age_group = EXCLUDED.age_group,
            country   = EXCLUDED.country
    """
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute(sql, (
                int(row["id"]),
                row["name"],
                row.get("age_group") or None,
                row.get("country") or None,
            ))
    conn.commit()
    print(f"  → {len(df)} usuários carregados.")


def load_ratings(conn: psycopg2.extensions.connection) -> None:
    path = os.path.join(DATA_LAKE, "ratings.csv")
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["rated_at"] = pd.to_datetime(df["rated_at"], errors="coerce").dt.date

    # Carrega apenas avaliações cujo movie_id existe na tabela movies
    with conn.cursor() as cur:
        cur.execute("SELECT imdb_id FROM movies")
        valid_ids = {row[0] for row in cur.fetchall()}

    df = df[df["movie_id"].isin(valid_ids)]

    # Truncate para garantir idempotência (sem duplicatas)
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE ratings RESTART IDENTITY")
        for _, row in df.iterrows():
            cur.execute(
                "INSERT INTO ratings (movie_id, user_id, score, rated_at) VALUES (%s, %s, %s, %s)",
                (
                    row["movie_id"],
                    int(row["user_id"]),
                    None if pd.isna(row["score"]) else float(row["score"]),
                    None if pd.isna(row["rated_at"]) else row["rated_at"],
                ),
            )
    conn.commit()
    print(f"  → {len(df)} avaliações carregadas.")


# ─── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Conectando ao banco de dados...")
    try:
        conn = get_connection()
    except psycopg2.OperationalError as exc:
        print(f"Erro de conexão: {exc}", file=sys.stderr)
        sys.exit(1)

    with conn:
        print("Criando schema...")
        create_schema(conn)
        print("Carregando movies...")
        load_movies(conn)
        print("Carregando users...")
        load_users(conn)
        print("Carregando ratings...")
        load_ratings(conn)

    conn.close()
    print("ETL concluído com sucesso.")


if __name__ == "__main__":
    main()
