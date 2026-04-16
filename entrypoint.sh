#!/bin/sh
# entrypoint.sh – aguarda o banco, inicializa o schema/dados e inicia a app.
set -e

echo "==> Aguardando o banco de dados ficar disponível..."
until python - <<'EOF'
import os, sys, psycopg2
try:
    psycopg2.connect(os.environ.get("DATABASE_URL", ""))
    sys.exit(0)
except Exception:
    sys.exit(1)
EOF
do
  echo "    Banco não disponível, tentando novamente em 2s..."
  sleep 2
done

echo "==> Banco disponível. Executando ETL inicial..."
python app/init_db.py

echo "==> Iniciando Gunicorn..."
exec gunicorn \
  --workers 2 \
  --bind 0.0.0.0:5000 \
  --timeout 60 \
  "app.app:app"
