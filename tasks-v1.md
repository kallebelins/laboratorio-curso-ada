# MovieFlix Analytics – Lista de Tarefas

> Stack escolhida: **Python (Flask)** · **PostgreSQL** · **Docker / Docker Compose** · **Nginx** · **GitHub Actions** · **OMDB API**

---

## FASE 1 – Estrutura do Projeto

```
[x] 001 - Definir e documentar a stack tecnológica
    Registrar no README as tecnologias escolhidas, justificativas e versões.
    Garante alinhamento do time antes de iniciar o código.
    Referências: README.md (seção Objetivos)
```

```
[x] 002 - Criar estrutura de diretórios do repositório
    Criar os diretórios: app/, nginx/, data/lake/, data/warehouse/, data/mart/,
    data/scripts/, .github/workflows/.
    Estrutura base para todas as fases seguintes.
    Referências: 001
```

```
[x] 003 - Configurar arquivo .env.example e .gitignore
    Criar .env.example com variáveis necessárias (DB_URL, OMDB_API_KEY,
    DOCKERHUB_USERNAME etc.). Adicionar .env e __pycache__ ao .gitignore.
    Evita expor secrets no repositório.
    Referências: 001, 002
    Links: https://docs.docker.com/compose/environment-variables/
```

---

## FASE 2 – Data Lake

```
[x] 004 - Buscar dados via OMDB API e gerar CSVs (Data Lake)
    Criar script data/scripts/fetch_lake.py que:
      - Consulta OMDB API para N filmes (ex.: 50 títulos variados)
      - Gera data/lake/movies.csv (imdbID, title, genre, year, country, imdbRating)
      - Gera data/lake/users.csv (id, name, age_group, country) – dados sintéticos
      - Gera data/lake/ratings.csv (user_id, movie_id, score, rated_at) – sintético
    Os CSVs são a fonte de dados de todas as fases seguintes.
    Referências: 003 (.env com OMDB_API_KEY)
    Links: https://www.omdbapi.com/
           https://docs.python.org/3/library/csv.html
```

---

## FASE 3 – Aplicação Web

```
[x] 005 - Modelar banco de dados da aplicação (PostgreSQL)
    Criar models/tabelas:
      movies  (id, imdb_id, title, genre, year, country, imdb_rating)
      users   (id, name, age_group, country)
      ratings (id, movie_id, user_id, score, rated_at)
    Definir DDL em app/schema.sql.
    Referências: 004
    Links: https://www.postgresql.org/docs/current/sql-createtable.html
```

```
[x] 006 - Criar script de carga (ETL simples: CSVs → PostgreSQL)
    Criar app/init_db.py que:
      - Cria o schema e as tabelas usando app/schema.sql caso não existam.
      - Lê data/lake/movies.csv, users.csv e ratings.csv com pandas.
      - Normaliza tipos (strip, parse de datas, cast numérico).
      - Insere os dados via pandas.to_sql (if_exists='replace').
    O script deve ser idempotente (pode ser reexecutado sem duplicar dados).
    Referências: 004, 005
    Links: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html
           https://www.psycopg.org/psycopg3/docs/
```

```
[x] 007 - Criar aplicação Flask com rotas analíticas (somente leitura)
    Implementar as rotas:
      GET /               → dashboard: top filmes e resumo de avaliações
      GET /movies         → listagem de filmes com nota média
      GET /movies/<id>    → detalhe do filme com avaliações
      GET /analytics      → visões analíticas (top gênero, por país, por faixa etária)
    Usar Flask + psycopg2 (ou SQLAlchemy core) para consultar o banco.
    Sem formulários de cadastro ou edição.
    Referências: 005, 006
    Links: https://flask.palletsprojects.com/
           https://flask-sqlalchemy.palletsprojects.com/
```

```
[x] 008 - Criar templates HTML simples (Jinja2)
    Páginas: index.html (dashboard), movies.html (listagem),
    movie_detail.html (detalhe) e analytics.html (visões analíticas).
    Sem frameworks CSS pesados – Bootstrap CDN é suficiente.
    Referências: 006, 007
    Links: https://getbootstrap.com/docs/5.3/
```

```
[x] 009 - Criar Dockerfile da aplicação
    Imagem base: python:3.12-slim.
    Instalar dependências via requirements.txt.
    Copiar data/lake/ para dentro da imagem (ou montar como volume no compose).
    Expor porta 5000. Usar CMD gunicorn para produção.
    Referências: 006, 007, 008
    Links: https://docs.docker.com/reference/dockerfile/
           https://gunicorn.org/
```

```
[x] 010 - Configurar Nginx como proxy reverso
    Criar nginx/nginx.conf com upstream apontando para o serviço app:5000.
    Servir na porta 80.
    Referências: 009
    Links: https://nginx.org/en/docs/beginners_guide.html
```

```
[x] 011 - Criar docker-compose.yml (app + db + nginx)
    Serviços: app (Flask), db (postgres:16-alpine), nginx.
    Usar volumes para persistência do Postgres e montagem de data/lake/.
    Incluir serviço/comando de inicialização que execute init_db.py antes
    de subir a aplicação (entrypoint ou depends_on com healthcheck).
    Referências: 009, 010
    Links: https://docs.docker.com/compose/
```

```
[x] 012 - Testar aplicação localmente com Docker Compose
    Rodar: docker compose up --build
    Verificar que http://localhost responde corretamente via Nginx.
    Confirmar que a carga dos CSVs foi executada e as páginas exibem dados reais
    do Data Lake (filmes, avaliações, visões analíticas).
    Referências: 011
```

---

## FASE 4 – Pipeline CI/CD (GitHub Actions)

```
[ ] 013 - Configurar secrets no repositório GitHub
    Adicionar em Settings → Secrets and variables → Actions:
      DOCKERHUB_USERNAME, DOCKERHUB_TOKEN
    Referências: 003
    Links: https://docs.github.com/en/actions/security-guides/encrypted-secrets
           https://hub.docker.com/settings/security
```

```
[ ] 014 - Criar workflow: build + test + push (.github/workflows/ci.yml)
    Etapas do job:
      1. checkout
      2. docker build -t <image>:latest
      3. docker compose up -d ; sleep 5
         curl --fail http://localhost || exit 1  (teste de smoke)
      4. docker compose down
      5. docker login + docker push (apenas em push para main)
    Trigger: push e pull_request na branch main.
    Referências: 011, 013
    Links: https://docs.github.com/en/actions/use-cases-and-examples/publishing-packages/publishing-docker-images
           https://github.com/docker/login-action
           https://github.com/docker/build-push-action
```

```
[ ] 015 - Validar pipeline no GitHub Actions
    Fazer push e verificar que os 3 passos passam (build, test, push).
    Confirmar imagem disponível no Docker Hub.
    Referências: 014
```

---

## FASE 5 – Data Warehouse, Data Mart e Queries

```
[ ] 016 - Criar schema do Data Warehouse no PostgreSQL
    Criar script data/scripts/create_dw.sql com tabelas dimensão e fato:
      dim_movie (movie_id, title, genre, year, country, imdb_rating)
      dim_user  (user_id, name, age_group, country)
      fact_rating (rating_id, movie_id, user_id, score, rated_at)
    Separar em schema "dw" para não conflitar com a app.
    Referências: 004
    Links: https://www.postgresql.org/docs/current/ddl-schemas.html
```

```
[ ] 017 - Criar script ETL: CSV do Data Lake → Data Warehouse
    Criar data/scripts/etl_load.py que:
      - Lê os 3 CSVs do Data Lake (pandas ou csv nativo)
      - Trata/normaliza dados (strip, tipos, datas)
      - Insere nas tabelas do DW via psycopg2 ou pandas.to_sql
    Referências: 004, 016
    Links: https://www.psycopg.org/psycopg3/docs/
           https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html
```

```
[ ] 018 - Criar views do Data Mart
    Criar data/scripts/create_mart.sql com views/materialized views:
      mart_top10_by_genre     → Top 10 filmes por gênero (média de score)
      mart_avg_by_age_group   → Nota média por faixa etária
      mart_ratings_by_country → Número de avaliações por país
    Referências: 016, 017
    Links: https://www.postgresql.org/docs/current/sql-createview.html
           https://www.postgresql.org/docs/current/sql-creatematerializedview.html
```

```
[ ] 019 - Escrever queries analíticas
    Criar data/scripts/analytics.sql com as consultas pedidas:
      Q1: Quais os 5 filmes mais populares? (maior nº de avaliações)
      Q2: Qual gênero tem melhor avaliação média?
      Q3: Qual país assiste mais filmes?
    Documentar resultados esperados como comentários no próprio arquivo.
    Referências: 018
```

```
[ ] 020 - Adicionar comandos ETL ao docker-compose.yml / Makefile
    Incluir targets para executar o pipeline de dados:
      python data/scripts/fetch_lake.py  (já disponível da fase 2)
      psql ... -f data/scripts/create_dw.sql
      python data/scripts/etl_load.py
      psql ... -f data/scripts/create_mart.sql
    Simplifica a execução do ETL em ambiente local e CI.
    Referências: 011, 017, 018
```

---

## FASE 6 – Documentação e Entrega

```
[ ] 021 - Atualizar README com arquitetura completa
    Incluir:
      - Diagrama de arquitetura (texto/ASCII ou Mermaid)
      - Como rodar localmente (pré-requisitos, docker compose up)
      - Como rodar o ETL
      - Link da imagem no Docker Hub
      - Exemplos dos resultados das queries analíticas
    Referências: todas as fases anteriores
    Links: https://mermaid.js.org/syntax/flowchart.html
```

```
[ ] 022 - Revisão final e testes end-to-end
    Checklist:
      [ ] Pipeline verde no GitHub Actions
      [ ] Imagem publicada no Docker Hub
      [ ] App acessível via Nginx (localhost:80)
      [ ] ETL roda sem erros
      [ ] Queries do Data Mart retornam resultados
    Referências: 012, 015, 020
```

```
[ ] 023 - Enviar projeto por e-mail
    Título: <Seu nome completo> + Projeto final
    Destinatário: raoni@srelabs.cloud
    Incluir: link do repositório GitHub e link da imagem no Docker Hub.
    Prazo: 22 de abril de 2026 às 23:59.
    Referências: README.md (seção Entregáveis)
```

---

## Resumo das Fases

| Fase | Foco | Tarefas |
|------|------|---------|
| 1 – Estrutura | Organização e configuração inicial | 001 – 003 |
| 2 – Data Lake | Extração OMDB API e geração dos CSVs | 004 |
| 3 – App Web | Modelo · Carga · Flask · Docker · Nginx | 005 – 012 |
| 4 – CI/CD | GitHub Actions + Docker Hub | 013 – 015 |
| 5 – DW, Data Mart e Queries | ETL · Warehouse · Mart · Análises | 016 – 020 |
| 6 – Entrega | Documentação e submissão | 021 – 023 |

**Total: 23 tarefas**
