"""
data/scripts/etl_load.py – Fase 5: ETL Data Lake → Data Warehouse
Lê os CSVs do Data Lake e carrega nas tabelas dimensão e fato do schema "dw".

Uso:
  python data/scripts/etl_load.py

Variáveis de ambiente (ou .env na raiz do projeto):
  DATABASE_URL   – ex.: postgresql://postgres:P4ssw0rd@localhost:5432/movieflix
  DATA_LAKE_DIR  – caminho para o diretório data/lake  (padrão: data/lake)
"""

import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

# ── Configuração ──────────────────────────────────────────────────────────────

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:P4ssw0rd@db:5432/movieflix"
)
DATA_LAKE_DIR = Path(os.environ.get("DATA_LAKE_DIR", "data/lake"))

DW_SQL   = Path(__file__).parent.parent / "warehouse" / "create_dw.sql"
MART_SQL = Path(__file__).parent.parent / "mart" / "create_mart.sql"


# ── Conexão ───────────────────────────────────────────────────────────────────

def get_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(DATABASE_URL)


# ── Schema ────────────────────────────────────────────────────────────────────

def create_dw_schema(conn: psycopg2.extensions.connection) -> None:
    """Executa create_dw.sql para garantir que as tabelas existam."""
    sql = DW_SQL.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print("[DW] Schema criado/verificado.")


# ── Data Mart ─────────────────────────────────────────────────────────────────

def create_mart_views(conn: psycopg2.extensions.connection) -> None:
    """Executa create_mart.sql para criar/recriar as views do Data Mart."""
    sql = MART_SQL.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print("[Mart] Views criadas/atualizadas.")


# ── dim_movie ─────────────────────────────────────────────────────────────────

def load_dim_movie(conn: psycopg2.extensions.connection) -> None:
    path = DATA_LAKE_DIR / "movies.csv"
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"imdbID": "movie_id", "imdbRating": "imdb_rating"})
    df["title"] = df["title"].str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["imdb_rating"] = pd.to_numeric(df["imdb_rating"], errors="coerce")

    sql = """
        INSERT INTO dw.dim_movie (movie_id, title, genre, year, country, imdb_rating)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (movie_id) DO UPDATE SET
            title       = EXCLUDED.title,
            genre       = EXCLUDED.genre,
            year        = EXCLUDED.year,
            country     = EXCLUDED.country,
            imdb_rating = EXCLUDED.imdb_rating
    """
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute(sql, (
                row["movie_id"],
                row["title"],
                row.get("genre"),
                None if pd.isna(row["year"]) else int(row["year"]),
                row.get("country"),
                None if pd.isna(row["imdb_rating"]) else float(row["imdb_rating"]),
            ))
    conn.commit()
    print(f"[DW] dim_movie: {len(df)} registros carregados.")


# ── dim_user ──────────────────────────────────────────────────────────────────

def load_dim_user(conn: psycopg2.extensions.connection) -> None:
    path = DATA_LAKE_DIR / "users.csv"
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"id": "user_id"})
    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce").astype("Int64")
    df["name"] = df["name"].str.strip()

    sql = """
        INSERT INTO dw.dim_user (user_id, name, age_group, country)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            name      = EXCLUDED.name,
            age_group = EXCLUDED.age_group,
            country   = EXCLUDED.country
    """
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute(sql, (
                int(row["user_id"]),
                row["name"],
                row.get("age_group"),
                row.get("country"),
            ))
    conn.commit()
    print(f"[DW] dim_user: {len(df)} registros carregados.")


# ── fact_rating ───────────────────────────────────────────────────────────────

def load_fact_rating(conn: psycopg2.extensions.connection) -> None:
    path = DATA_LAKE_DIR / "ratings.csv"
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"movie_id": "movie_id", "user_id": "user_id"})
    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce").astype("Int64")
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["rated_at"] = pd.to_datetime(df["rated_at"], errors="coerce").dt.date

    # Trunca a tabela para garantir idempotência (sem duplicatas)
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE dw.fact_rating RESTART IDENTITY CASCADE")
    conn.commit()

    sql = """
        INSERT INTO dw.fact_rating (movie_id, user_id, score, rated_at)
        VALUES (%s, %s, %s, %s)
    """
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute(sql, (
                row["movie_id"],
                int(row["user_id"]),
                None if pd.isna(row["score"]) else float(row["score"]),
                row["rated_at"] if row["rated_at"] is not pd.NaT else None,
            ))
    conn.commit()
    print(f"[DW] fact_rating: {len(df)} registros carregados.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"Conectando em: {DATABASE_URL.split('@')[-1]}")
    try:
        conn = get_connection()
    except psycopg2.OperationalError as exc:
        print(f"Erro de conexão: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        create_dw_schema(conn)
        load_dim_movie(conn)
        load_dim_user(conn)
        load_fact_rating(conn)
        print("[DW] ETL concluído com sucesso.")
        create_mart_views(conn)
        print("[Pipeline] Data Mart atualizado com sucesso.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
