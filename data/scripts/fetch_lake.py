"""
fetch_lake.py – Fase 2: Data Lake
Busca filmes via OMDB API e gera CSVs sintéticos em data/lake/.

Arquivos gerados:
  data/lake/movies.csv   – dados reais da OMDB API
  data/lake/users.csv    – dados sintéticos de usuários
  data/lake/ratings.csv  – avaliações sintéticas

Uso:
  python data/scripts/fetch_lake.py

Variáveis de ambiente:
  OMDB_API_KEY      (obrigatório) – chave da OMDB API
  LIMIT_PER_GENRE   (opcional)    – filmes por gênero (padrão: 15)
"""

import os
import random
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent  # data/
LAKE_DIR = BASE_DIR / "lake"
LAKE_DIR.mkdir(parents=True, exist_ok=True)

# Lê OMDB_API_KEY da variável de ambiente ou do arquivo .env
API_KEY = os.environ.get("OMDB_API_KEY", "").strip()
if not API_KEY:
    env_file = BASE_DIR.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OMDB_API_KEY=") and not line.startswith("#"):
                API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

if not API_KEY or API_KEY == "your_omdb_api_key_here":
    raise SystemExit(
        "OMDB_API_KEY não encontrada.\n"
        "Defina a variável de ambiente ou adicione-a ao arquivo .env."
    )

BASE_URL = "http://www.omdbapi.com/"
LIMIT_PER_GENRE = int(os.environ.get("LIMIT_PER_GENRE", "15"))

# Filtros
GENEROS_ALVO = ["Action", "Sci-Fi", "Comedy"]
TERMOS_BUSCA = ["Life", "World", "Star", "Man"]


# ---------------------------------------------------------------------------
# Etapa 1 – buscar filmes por gênero via OMDB API
# ---------------------------------------------------------------------------

def fetch_movies_by_genre(keywords, target_genres, limit_per_genre=15):
    all_movies = []
    seen_ids = set()
    genre_counts = {g: 0 for g in target_genres}

    for kw in keywords:
        print(f"Vasculhando filmes com o termo: '{kw}'...")
        for page in range(1, 6):  # até 5 páginas por termo
            params = {"s": kw, "type": "movie", "apikey": API_KEY, "page": page}
            try:
                res = requests.get(BASE_URL, params=params, timeout=10).json()
                if res.get("Response") == "False":
                    break

                for item in res.get("Search", []):
                    m_id = item["imdbID"]
                    if m_id in seen_ids:
                        continue

                    # Busca detalhes para obter Genre, Country, imdbRating
                    detail_res = requests.get(
                        BASE_URL,
                        params={"i": m_id, "apikey": API_KEY},
                        timeout=10,
                    ).json()

                    movie_genres = detail_res.get("Genre", "")

                    # Aceita o filme no primeiro gênero-alvo que ele atender
                    for target in target_genres:
                        if (
                            target in movie_genres
                            and genre_counts[target] < limit_per_genre
                        ):
                            all_movies.append(
                                {
                                    "imdbID": m_id,
                                    "title": detail_res.get("Title"),
                                    "genre": movie_genres,
                                    "year": detail_res.get("Year"),
                                    "country": detail_res.get("Country"),
                                    "imdbRating": detail_res.get("imdbRating"),
                                }
                            )
                            seen_ids.add(m_id)
                            genre_counts[target] += 1
                            print(
                                f"  [{sum(genre_counts.values()):>3}] "
                                f"{detail_res.get('Title')} [{target}]"
                            )
                            break

            except Exception as exc:
                print(f"  [WARN] Erro: {exc}")

            # Para se a meta de todos os gêneros foi atingida
            if all(count >= limit_per_genre for count in genre_counts.values()):
                break

        if all(count >= limit_per_genre for count in genre_counts.values()):
            break

    print(f"\n  {len(all_movies)} filmes filtrados por gênero.\n")
    return pd.DataFrame(all_movies)


# ---------------------------------------------------------------------------
# Etapa 2 – gerar usuários e avaliações sintéticos
# ---------------------------------------------------------------------------

def generate_mock_data(movie_df):
    if movie_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    rng = random.Random(42)

    users = pd.DataFrame(
        {
            "id": range(1, 21),
            "name": [f"Usuario_{i}" for i in range(1, 21)],
            "age_group": [
                rng.choice(["18-24", "25-34", "35-44", "45-54", "55+"])
                for _ in range(20)
            ],
            "country": [
                rng.choice(
                    [
                        "Brazil", "United States", "Mexico", "Argentina",
                        "Colombia", "Portugal", "Germany", "France",
                        "United Kingdom", "Spain",
                    ]
                )
                for _ in range(20)
            ],
        }
    )

    ratings_list = []
    movie_ids = movie_df["imdbID"].tolist()
    rating_id = 1
    for u_id in users["id"]:
        sample = rng.sample(movie_ids, k=min(len(movie_ids), 5))
        for m_id in sample:
            ratings_list.append(
                {
                    "id": rating_id,
                    "user_id": u_id,
                    "movie_id": m_id,
                    "score": round(rng.uniform(1.0, 10.0), 1),
                    "rated_at": "2024-02-15",
                }
            )
            rating_id += 1

    return users, pd.DataFrame(ratings_list)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 55)
    print(" MovieFlix Analytics – Geração do Data Lake")
    print("=" * 55)

    df_movies = fetch_movies_by_genre(TERMOS_BUSCA, GENEROS_ALVO, limit_per_genre=LIMIT_PER_GENRE)

    if df_movies.empty:
        raise SystemExit("Nenhum filme retornado. Verifique sua OMDB_API_KEY.")

    df_users, df_ratings = generate_mock_data(df_movies)

    print("Gravando arquivos CSV...")

    df_movies.to_csv(LAKE_DIR / "movies.csv", index=False)
    print(f"  ✔ data/lake/movies.csv ({len(df_movies)} registros)")

    df_users.to_csv(LAKE_DIR / "users.csv", index=False)
    print(f"  ✔ data/lake/users.csv ({len(df_users)} registros)")

    df_ratings.to_csv(LAKE_DIR / "ratings.csv", index=False)
    print(f"  ✔ data/lake/ratings.csv ({len(df_ratings)} registros)")

    print("\nData Lake gerado com sucesso em data/lake/")
    print("=" * 55)


if __name__ == "__main__":
    main()
